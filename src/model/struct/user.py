# =============================================================================
# User Sub-Struct (사용자 비즈니스 로직)
# =============================================================================

import base64
import datetime
import hashlib
import hmac
import os
import re
import time

import bcrypt
import dns.resolver
import peewee as pw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class User:
    LEGACY_EMAIL_CIPHER_VERSION = "v1"
    EMAIL_DOMAIN_CACHE_SECONDS = 600
    EMAIL_DOMAIN_CACHE_LIMIT = 512
    _email_domain_cache = {}

    def __init__(self, core):
        self.core = core
        self.db = core.orm.use("user")
        self._jwt_secret = wiz.model("auth_config").jwt_secret()
        email_config = wiz.config("auth").email_encryption
        self.email_cipher_version = str(email_config.active_key_id or "").strip()
        encoded_key = str(getattr(email_config.keys, self.email_cipher_version, "") or "").strip()
        try:
            self._email_key = base64.b64decode(encoded_key, validate=True)
        except Exception as exc:
            raise RuntimeError("invalid active email encryption key") from exc
        if len(self._email_key) != 32 or not self.email_cipher_version:
            raise RuntimeError("email encryption key must be a named 256-bit key")
        legacy_key = hmac.new(
            self._jwt_secret,
            b"gachi:user-email-encryption-key:v1",
            hashlib.sha256,
        ).digest()
        self._email_keys = {
            self.email_cipher_version: self._email_key,
            self.LEGACY_EMAIL_CIPHER_VERSION: legacy_key,
        }
        self._legacy_index_key = self._jwt_secret

    def _email_aad(self, version):
        return f"gachi:user-email:{version}".encode("utf-8")

    def _normalize_email(self, email):
        return str(email or "").strip().lower()

    def _normalize_nickname(self, name):
        return str(name or "").strip().lower()

    def validate_email_address(self, email):
        normalized = self._normalize_email(email)
        if not normalized or len(normalized) > 254 or normalized.count("@") != 1:
            return False, "올바른 이메일 형식으로 입력해주세요."

        local, domain = normalized.rsplit("@", 1)
        if (
            not local
            or len(local) > 64
            or local.startswith(".")
            or local.endswith(".")
            or ".." in local
            or not re.fullmatch(r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+", local)
        ):
            return False, "올바른 이메일 형식으로 입력해주세요."

        try:
            ascii_domain = domain.encode("idna").decode("ascii").lower()
        except Exception:
            return False, "올바른 이메일 형식으로 입력해주세요."

        labels = ascii_domain.split(".")
        if (
            len(labels) < 2
            or len(ascii_domain) > 253
            or len(labels[-1]) < 2
            or any(
                not label
                or len(label) > 63
                or label.startswith("-")
                or label.endswith("-")
                or not re.fullmatch(r"[a-z0-9-]+", label)
                for label in labels
            )
            or labels[-1] in {"invalid", "test", "example", "localhost", "local"}
        ):
            return False, "메일을 받을 수 있는 실제 이메일 도메인을 입력해주세요."

        now = time.monotonic()
        cached = self._email_domain_cache.get(ascii_domain)
        if cached and now - cached["checked_at"] < self.EMAIL_DOMAIN_CACHE_SECONDS:
            if cached["available"]:
                return True, ""
            return False, "메일을 받을 수 없는 이메일 도메인입니다."

        available = False
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 1.0
            resolver.lifetime = 2.0
            answers = resolver.resolve(ascii_domain, "MX")
            available = any(
                str(answer.exchange).rstrip(".")
                for answer in answers
            )
        except Exception:
            available = False

        if ascii_domain not in self._email_domain_cache and len(self._email_domain_cache) >= self.EMAIL_DOMAIN_CACHE_LIMIT:
            self._email_domain_cache.pop(next(iter(self._email_domain_cache)))
        self._email_domain_cache[ascii_domain] = {
            "available": available,
            "checked_at": now,
        }
        if not available:
            return False, "메일을 받을 수 없는 이메일 도메인입니다."
        return True, ""

    def nickname_exists(self, name, exclude_id=None):
        normalized = self._normalize_nickname(name)
        if not normalized:
            return False
        model = self.db.orm
        query = model.select().where(
            pw.fn.LOWER(pw.fn.TRIM(model.name)) == normalized
        )
        if exclude_id:
            query = query.where(model.id != exclude_id)
        return query.exists()

    def _email_hash(self, email):
        normalized = self._normalize_email(email)
        return hmac.new(
            self._email_key,
            f"gachi:user-email-index:v2:{normalized}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _legacy_email_hash(self, email):
        normalized = self._normalize_email(email)
        return hmac.new(
            self._legacy_index_key,
            f"gachi:user-email-index:v1:{normalized}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def protect_email(self, email):
        normalized = self._normalize_email(email)
        if not normalized:
            raise ValueError("email is required")
        email_hash = self._email_hash(normalized)
        nonce = os.urandom(12)
        ciphertext = AESGCM(self._email_key).encrypt(
            nonce,
            normalized.encode("utf-8"),
            self._email_aad(self.email_cipher_version),
        )
        encoded = base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii").rstrip("=")
        return dict(
            email=f"private-{email_hash[:32]}@gachi.invalid",
            email_hash=email_hash,
            email_encrypted=f"{self.email_cipher_version}:{encoded}",
        )

    def _decrypt_email(self, encrypted):
        value = str(encrypted or "").strip()
        if not value:
            return ""
        try:
            version, encoded = value.split(":", 1)
            key = self._email_keys.get(version)
            if key is None:
                return ""
            encoded += "=" * (-len(encoded) % 4)
            raw = base64.urlsafe_b64decode(encoded.encode("ascii"))
            plaintext = AESGCM(key).decrypt(raw[:12], raw[12:], self._email_aad(version))
            return self._normalize_email(plaintext.decode("utf-8"))
        except Exception:
            return ""

    def reveal_email(self, encrypted, fallback=""):
        decrypted = self._decrypt_email(encrypted)
        if decrypted:
            return decrypted
        stored = self._normalize_email(fallback)
        if stored.endswith("@gachi.invalid"):
            return ""
        return stored

    def _hydrate_email(self, user):
        if user is None:
            return None
        result = dict(user)
        result["email"] = self.reveal_email(
            result.get("email_encrypted"),
            result.get("email"),
        )
        result.pop("email_hash", None)
        result.pop("email_encrypted", None)
        return result

    def _find_row_by_email(self, email):
        normalized = self._normalize_email(email)
        if not normalized:
            return None
        for email_hash in (self._email_hash(normalized), self._legacy_email_hash(normalized)):
            try:
                user = self.db.get(email_hash=email_hash)
                if user is not None:
                    return user
            except Exception:
                pass
        return self.db.get(email=normalized)

    def find_by_email(self, email):
        user = self._hydrate_email(self._find_row_by_email(email))
        if user:
            user.pop("password", None)
        return user

    def _hash_password(self, password):
        if isinstance(password, str):
            password = password.encode("utf-8")
        return bcrypt.hashpw(password, bcrypt.gensalt()).decode("utf-8")

    def _check_password(self, password, hashed):
        if isinstance(password, str):
            password = password.encode("utf-8")
        if isinstance(hashed, str):
            hashed = hashed.encode("utf-8")
        return bcrypt.checkpw(password, hashed)

    def authenticate(self, email, password):
        user = self._find_row_by_email(email)
        if user is None:
            return None
        if not self._check_password(password, user.get("password", "")):
            return None
        user = self._hydrate_email(user)
        user.pop("password", None)
        return user

    def get(self, id=None):
        user = self._hydrate_email(self.db.get(id=id))
        if user:
            user.pop("password", None)
        return user

    def list(self, text="", role=""):
        kwargs = {}
        like = None
        if role:
            kwargs["role"] = role
        if text:
            kwargs["name"] = text
            like = "name"

        rows = self.db.rows(
            orderby="created",
            order="ASC",
            like=like,
            **kwargs,
        )
        result = []
        for row in rows:
            user = self._hydrate_email(row)
            user.pop("password", None)
            result.append(user)
        return result

    def create(self, data):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = dict(data or {})
        protected = self.protect_email(payload.get("email"))
        payload.update(protected)
        payload["password"] = self._hash_password(payload["password"])
        payload["created"] = now
        payload["updated"] = now
        if not payload.get("role"):
            payload["role"] = "user"
        return self.db.insert(payload)

    def update_profile(self, id, **fields):
        allowed = {
            key: value for key, value in fields.items()
            if key in ["name", "mobile", "role"]
        }
        allowed["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.update(allowed, id=id)

    def change_password(self, id, current_password, new_password):
        user = self.db.get(id=id)
        if user is None:
            return False
        if not self._check_password(current_password, user.get("password", "")):
            return False
        hashed = self._hash_password(new_password)
        self.db.update(
            dict(
                password=hashed,
                updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
            id=id,
        )
        return True

    def count(self, **kwargs):
        return self.db.count(**kwargs) or 0


Model = User
