import base64
import datetime
import hashlib
import hmac
import json
import uuid


class Mobile:
    def __init__(self, core):
        self.core = core

    def _now(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _decode_segment(self, value):
        value = value + ("=" * (-len(value) % 4))
        return base64.urlsafe_b64decode(value.encode("utf-8"))

    def jwt_user_id(self, token):
        token = str(token or "").strip()
        if token.startswith("Bearer "):
            token = token[7:]
        parts = token.split(".")
        if len(parts) != 3:
            return ""
        try:
            secret = wiz.model("auth_config").jwt_secret()
            signing_input = f"{parts[0]}.{parts[1]}".encode("utf-8")
            expected = hmac.new(secret, signing_input, hashlib.sha256).digest()
            actual = self._decode_segment(parts[2])
            if not hmac.compare_digest(expected, actual):
                return ""
            payload = json.loads(self._decode_segment(parts[1]).decode("utf-8"))
            return str(payload.get("sub") or "").strip()
        except Exception:
            return ""

    def register_device(self, user_id, payload):
        user_id = str(user_id or "").strip()
        payload = payload if isinstance(payload, dict) else {}
        token = str(payload.get("device_token") or payload.get("token") or "").strip()
        if not user_id:
            return 401, dict(message="로그인이 필요합니다.")
        if not token or len(token) > 512:
            return 400, dict(message="유효한 푸시 토큰이 필요합니다.")

        db = self.core.db("mobile_device")
        current = db.get(device_token=token)
        now = self._now()
        values = dict(
            user_id=user_id,
            device_token=token,
            platform=str(payload.get("platform") or "ios").strip()[:16],
            app_version=str(payload.get("app_version") or "").strip()[:32],
            locale=str(payload.get("locale") or "ko-KR").strip()[:32],
            enabled=True,
            updated=now,
        )
        if current:
            db.update(values, id=current["id"])
            device_id = current["id"]
        else:
            device_id = uuid.uuid4().hex
            db.insert(dict(id=device_id, created=now, **values))
        return 200, dict(device_id=device_id, registered=True)

    def unregister_device(self, user_id, token):
        user_id = str(user_id or "").strip()
        token = str(token or "").strip()
        if not user_id:
            return 401, dict(message="로그인이 필요합니다.")
        if not token:
            return 400, dict(message="푸시 토큰이 필요합니다.")
        db = self.core.db("mobile_device")
        row = db.get(device_token=token, user_id=user_id)
        if row:
            db.update(dict(enabled=False, updated=self._now()), id=row["id"])
        return 200, dict(registered=False)

    def active_tokens(self, user_ids):
        ids = [str(value or "").strip() for value in (user_ids or []) if str(value or "").strip()]
        if not ids:
            return []
        try:
            model = self.core.db("mobile_device").orm
            query = model.select().where(
                (model.user_id.in_(ids)) & (model.enabled == True)
            )
            return [row.device_token for row in query]
        except Exception:
            return []

    def enqueue_push(self, user_ids, event_type, title, body, deep_link="", payload=None):
        """활성 iOS 토큰별 APNs 작업을 만든다. 알림 실패가 본 업무를 막지 않도록 0을 반환한다."""
        ids = list(dict.fromkeys(
            str(value or "").strip()
            for value in (user_ids or [])
            if str(value or "").strip()
        ))
        if not ids:
            return 0
        try:
            device_model = self.core.db("mobile_device").orm
            devices = device_model.select().where(
                (device_model.user_id.in_(ids))
                & (device_model.platform == "ios")
                & (device_model.enabled == True)
            )
            job_db = self.core.db("mobile_push_job")
            now = datetime.datetime.now()
            event_payload = payload if isinstance(payload, dict) else {}
            count = 0
            for device in devices:
                job_db.insert(dict(
                    id=uuid.uuid4().hex,
                    user_id=str(device.user_id or "")[:32],
                    device_token=str(device.device_token or "")[:512],
                    event_type=str(event_type or "general")[:32],
                    title=str(title or "GACHI")[:100],
                    body=str(body or "")[:500],
                    deep_link=str(deep_link or "")[:500],
                    payload=json.dumps(event_payload, ensure_ascii=False),
                    status="queued",
                    attempts=0,
                    available_at=now,
                    last_error="",
                    created_at=now,
                    updated_at=now,
                    sent_at=None,
                ))
                count += 1
            return count
        except Exception:
            return 0


Model = Mobile
