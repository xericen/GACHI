import base64
import hashlib
import hmac
import json
import season


SECRET = wiz.model("auth_config").jwt_secret()


def _uri():
    try:
        return wiz.request.uri()
    except Exception:
        return ""


def _header(name):
    try:
        return wiz.request.header(name, "")
    except Exception:
        pass
    try:
        return wiz.request.headers.get(name, "")
    except Exception:
        pass
    return ""


def _decode_segment(value):
    value = value + ("=" * (-len(value) % 4))
    return base64.urlsafe_b64decode(value.encode("utf-8"))


def _jwt_payload():
    auth = _header("Authorization") or wiz.request.query("token", "")
    if auth.startswith("Bearer "):
        auth = auth[7:]
    parts = auth.split(".")
    if len(parts) != 3:
        return {}
    signing_input = f"{parts[0]}.{parts[1]}".encode("utf-8")
    expected = hmac.new(SECRET, signing_input, hashlib.sha256).digest()
    try:
        actual = _decode_segment(parts[2])
        if not hmac.compare_digest(expected, actual):
            return {}
        return json.loads(_decode_segment(parts[1]).decode("utf-8"))
    except Exception:
        return {}


def _is_admin_api(path):
    prefixes = [
        "/wiz/api/page.admin/",
        "/admin/stats/",
        "/admin/places/",
        "/admin/courses/",
        "/admin/curation/featured",
        "/admin/settings/",
    ]
    exact = ["/admin/places", "/admin/courses"]
    if path in exact:
        return True
    return any(path.startswith(prefix) for prefix in prefixes)


def _deny(status, message):
    path = _uri()
    if _is_admin_api(path):
        wiz.response.status(status, message=message)
        return
    if status == 401:
        wiz.response.redirect(f"/login?returnTo={path or '/admin/dashboard'}")
    else:
        wiz.response.redirect("/")

class Controller(wiz.controller("base")):
    def __init__(self):
        super().__init__()

        payload = _jwt_payload()
        if not wiz.session.has("id") and payload.get("sub"):
            wiz.session.set(
                id=payload.get("sub", ""),
                email=payload.get("email", ""),
                name=payload.get("name", ""),
                role=payload.get("role", "user")
            )
        logged_in = wiz.session.has("id") or bool(payload.get("sub"))
        is_admin = wiz.session.get("role") == "admin" or payload.get("role") == "admin"

        if not logged_in:
            _deny(401, "관리자 로그인이 필요합니다.")
            return

        if not is_admin:
            _deny(403, "관리자 권한이 필요합니다.")
