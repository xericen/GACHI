# =============================================================================
# User Sub-Struct (사용자 비즈니스 로직)
# =============================================================================

import base64
import datetime
import hashlib
import hmac
import os

import bcrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class User:
    LEGACY_EMAIL_CIPHER_VERSION = "v1"

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
