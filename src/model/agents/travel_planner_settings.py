import datetime
import json
import os


DEFAULT_MODEL = "gemini-2.5-flash"
MODEL_SETTING_KEY = "ai_model_config"
SUPPORTED_MODELS = [
    {"id": "gemini-2.5-flash-lite", "name": "Gemini 2.5 Flash Lite", "description": "빠른 응답과 낮은 호출 비용에 적합"},
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "description": "복합 일정 생성과 도구 호출에 적합"},
]


class TravelPlannerSettings:
    def __init__(self, wiz_context):
        self.wiz = wiz_context

    def enabled(self):
        return self._as_bool(self._runtime_config().get("enabled"), True)

    def api_key(self):
        key = os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        return key.strip() if key else self._config_value("api_key", "")

    def model(self):
        runtime = self._runtime_config()
        model = str(runtime.get("model") or "").strip()
        if model:
            return model
        model = os.environ.get("GEMINI_MODEL", "").strip()
        return model or self._config_value("model", DEFAULT_MODEL) or DEFAULT_MODEL

    def timeout(self):
        runtime = self._runtime_config()
        raw = runtime.get("timeout")
        if raw is None:
            raw = os.environ.get("GEMINI_TIMEOUT", "").strip() or self._config_value("timeout", "30")
        return self._bounded_int(raw, 30, 5, 60)

    def temperature(self):
        return self._bounded_float(self._runtime_config().get("temperature"), 0.45, 0, 1)

    def max_output_tokens(self):
        return self._bounded_int(self._runtime_config().get("max_output_tokens"), 900, 256, 2048)

    def admin_view(self):
        runtime = self._runtime_config()
        model = self.model()
        models = [dict(item) for item in SUPPORTED_MODELS]
        if model and model not in [item["id"] for item in models]:
            models.append({"id": model, "name": model, "description": "현재 환경 설정 모델"})
        enabled = self.enabled()
        has_key = bool(self.api_key())
        status = "disabled" if not enabled else ("ready" if has_key else "missing_key")
        return {
            "provider": "Google Gemini",
            "enabled": enabled,
            "model": model,
            "timeout": self.timeout(),
            "temperature": self.temperature(),
            "max_output_tokens": self.max_output_tokens(),
            "api_key_configured": has_key,
            "status": status,
            "models": models,
            "tools": ["장소 검색", "경로 조회"],
            "updated_at": runtime.get("_updated_at", ""),
        }

    def update(self, data):
        data = data if isinstance(data, dict) else {}
        model = str(data.get("model") or "").strip()
        allowed = [item["id"] for item in SUPPORTED_MODELS]
        current = self.model()
        if current and current not in allowed:
            allowed.append(current)
        if model not in allowed:
            raise ValueError("지원하는 AI 모델을 선택해주세요.")
        payload = {
            "enabled": self._as_bool(data.get("enabled"), True),
            "model": model,
            "timeout": self._bounded_int(data.get("timeout"), 30, 5, 60),
            "temperature": self._bounded_float(data.get("temperature"), 0.45, 0, 1),
            "max_output_tokens": self._bounded_int(data.get("max_output_tokens"), 900, 256, 2048),
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._save_runtime_config(payload)
        return self.admin_view()

    def _config_value(self, name, default=""):
        try:
            config = self.wiz.config("ai")
            gemini = getattr(config, "gemini", None)
            value = getattr(gemini, name, None) if gemini is not None else None
            return str(value).strip() if value is not None else default
        except Exception:
            return default

    def _settings_db(self):
        db = self.wiz.model("portal/season/orm").use("app_setting")
        try:
            db.orm.create_table(safe=True)
        except Exception:
            pass
        return db

    def _runtime_config(self):
        try:
            row = self._settings_db().get(key=MODEL_SETTING_KEY)
            if row is None:
                return {}
            data = json.loads(row.get("value") or "{}")
            if not isinstance(data, dict):
                return {}
            data["_updated_at"] = str(row.get("updated") or data.get("updated_at") or "")
            return data
        except Exception:
            return {}

    def _save_runtime_config(self, data):
        db = self._settings_db()
        row = db.get(key=MODEL_SETTING_KEY)
        payload = {
            "key": MODEL_SETTING_KEY,
            "value": json.dumps(data, ensure_ascii=False),
            "updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if row is None:
            db.insert(payload)
        else:
            db.update(payload, id=row["id"])

    def _as_bool(self, value, default=True):
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        return str(value).strip().lower() in ["1", "true", "yes", "on"]

    def _bounded_int(self, value, default, minimum, maximum):
        try:
            return max(minimum, min(int(value), maximum))
        except Exception:
            return default

    def _bounded_float(self, value, default, minimum, maximum):
        try:
            return round(max(minimum, min(float(value), maximum)), 2)
        except Exception:
            return default


Model = TravelPlannerSettings
