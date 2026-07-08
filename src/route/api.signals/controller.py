import json


def _method():
    try:
        return wiz.request.method().upper()
    except Exception:
        pass
    return wiz.request.query("_method", "GET").upper()


def _payload():
    raw = wiz.request.query("data", "{}")
    try:
        data = json.loads(raw)
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    for key, value in dict(wiz.request.query()).items():
        if key != "data":
            data[key] = value
    return data


def _current_user():
    session = wiz.model("portal/season/session").use()
    raw = session.get() or {}
    user_id = raw.get("id", "")
    if user_id:
        user = wiz.model("struct").user.get(user_id)
        if user:
            return user
    return raw


if _method() != "POST":
    wiz.response.status(405, message="POST로 신호를 생성해주세요.")
else:
    status, payload = wiz.model("struct").zenly.create_signal(_current_user(), _payload())
    wiz.response.status(status, **payload)
