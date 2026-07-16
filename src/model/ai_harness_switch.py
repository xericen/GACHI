import datetime
import json


HARNESS_SETTING_KEY = "ai_harness_enabled"


class AiHarnessSwitch:
    """DB-backed runtime switch. It is read on every execution selection."""

    def __init__(self, wiz_context):
        self.wiz = wiz_context

    def enabled(self):
        try:
            db = self._settings_db()
            row = db.get(key=HARNESS_SETTING_KEY)
            if row is None:
                db.insert({
                    "key": HARNESS_SETTING_KEY,
                    "value": json.dumps(True),
                    "updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                return True
            raw = row.get("value")
            try:
                raw = json.loads(raw)
            except Exception:
                pass
            if isinstance(raw, dict):
                raw = raw.get("enabled")
            return self._as_bool(raw, True)
        except Exception:
            # 설정 조회 장애가 기존 실행기로의 예기치 않은 전환을 만들지 않게 한다.
            return True

    def set_enabled(self, enabled):
        db = self._settings_db()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "key": HARNESS_SETTING_KEY,
            "value": json.dumps(bool(enabled)),
            "updated": now,
        }
        row = db.get(key=HARNESS_SETTING_KEY)
        if row is None:
            db.insert(payload)
        else:
            db.update(payload, id=row["id"])
        return self.enabled()

    def _settings_db(self):
        db = self.wiz.model("portal/season/orm").use("app_setting")
        try:
            db.orm.create_table(safe=True)
        except Exception:
            pass
        return db

    def _as_bool(self, value, default=True):
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        return str(value).strip().lower() in ["1", "true", "yes", "on"]


Model = AiHarnessSwitch
