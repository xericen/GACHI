def _header(name):
    try:
        return wiz.request.header(name, "")
    except Exception:
        pass
    try:
        return wiz.request.headers.get(name, "")
    except Exception:
        return ""


def _method():
    try:
        return wiz.request.method().upper()
    except Exception:
        return str(wiz.request.query("_method", "POST")).upper()


payload = dict(wiz.request.query())
mobile = wiz.model("struct").mobile
session = wiz.model("portal/season/session").use()
session_user = session.get() or {}
user_id = str(session_user.get("id") or "").strip()
if not user_id:
    auth = _header("Authorization") or payload.get("token_auth", "")
    user_id = mobile.jwt_user_id(auth)

if _method() == "DELETE":
    status, data = mobile.unregister_device(
        user_id,
        payload.get("device_token") or payload.get("token")
    )
elif _method() == "POST":
    status, data = mobile.register_device(user_id, payload)
else:
    status, data = 405, dict(message="지원하지 않는 요청 방식입니다.")

wiz.response.status(status, **data)
