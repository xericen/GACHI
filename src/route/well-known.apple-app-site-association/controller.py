import json
import os
import re


def _setting(name, fallback=""):
    try:
        config = wiz.config("apple")
        value = getattr(config, name, "")
        if value:
            return str(value).strip()
    except Exception:
        pass
    return str(os.getenv(name.upper(), fallback) or "").strip()


team_id = _setting("apple_team_id") or _setting("team_id")
app_id_prefix = _setting("apple_app_id_prefix") or team_id
bundle_id = _setting("apple_bundle_id", "com.wizide.gachi") or _setting("bundle_id", "com.wizide.gachi")

if not re.match(r"^[A-Z0-9]{10}$", app_id_prefix) or not re.match(r"^[A-Za-z0-9.-]+$", bundle_id):
    wiz.response.status(503, message="Apple App ID Prefix 또는 Bundle ID 설정이 필요합니다.")
else:
    app_id = f"{app_id_prefix}.{bundle_id}"
    body = {
        "applinks": {
            "details": [
                {
                    "appIDs": [app_id],
                    "components": [
                        {"/": "/access", "comment": "GACHI 앱 화면"},
                        {"/": "/course/*", "comment": "여행 코스 상세"},
                        {"/": "/courses/*", "comment": "여행 코스 상세"},
                    ],
                }
            ]
        }
    }
    wiz.response.send(
        json.dumps(body, ensure_ascii=False, separators=(",", ":")),
        content_type="application/json; charset=utf-8",
    )
