import base64
import hashlib
import html
import hmac
import json
import time

config = wiz.model("portal/season/config")
struct = wiz.model("struct")
BASEURI = config.auth_baseuri
LOGOUT_URI = config.auth_logout_uri
LOGIN_URL = config.auth_login_uri
SECRET = wiz.model("auth_config").jwt_secret()
LOCAL_AUTH_KEYS = [
    "tour-on-jwt",
    "tour-on-user",
    "tour-on-token",
    "tour-on-session",
    "tour-on-auth",
]


def _public_user(user):
    return dict(
        id=user.get("id", ""),
        email=user.get("email", ""),
        name=user.get("name", ""),
        role=user.get("role", "user")
    )


def _b64url(data):
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


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


def _issue_token(user):
    payload = dict(
        sub=user.get("id", ""),
        email=user.get("email", ""),
        name=user.get("name", ""),
        role=user.get("role", "user"),
        iat=int(time.time())
    )
    header = dict(typ="JWT", alg="HS256")
    signing_input = f"{_b64url(header)}.{_b64url(payload)}"
    signature = hmac.new(SECRET, signing_input.encode("utf-8"), hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
    return f"{signing_input}.{signature}"


def _set_user_session(user):
    data = _public_user(user)
    wiz.session.set(id=data["id"], email=data["email"], name=data["name"], role=data["role"])
    return data


def _clear_all_sessions():
    try:
        wiz.session.clear()
    except Exception:
        pass
    try:
        wiz.model("portal/season/session").use().clear()
    except Exception:
        pass


def _send_logout_redirect(target):
    target = target or "/"
    safe_target = html.escape(target, quote=True)
    script_target = json.dumps(target)
    auth_keys = json.dumps(LOCAL_AUTH_KEYS)
    wiz.response.send(f"""<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="0;url={safe_target}">
</head>
<body>
    <script>
    (function () {{
        var keys = {auth_keys};
        try {{
            keys.forEach(function (key) {{
                window.localStorage && window.localStorage.removeItem(key);
                window.sessionStorage && window.sessionStorage.removeItem(key);
            }});
        }} catch (e) {{}}
        window.location.replace({script_target});
    }})();
    </script>
</body>
</html>""", content_type="text/html; charset=utf-8")


def _session_user_data(raw=None):
    raw = raw or {}
    user_id = raw.get("id") or raw.get("user_id") or raw.get("userid") or raw.get("uid") or raw.get("sub") or ""
    if user_id:
        try:
            user = struct.user.get(user_id)
            if user is not None:
                return _public_user(user)
        except Exception:
            pass
    return dict(
        id=user_id,
        email=raw.get("email", ""),
        name=raw.get("name", raw.get("username", "")),
        role=raw.get("role", "user")
    )


handled = False

if wiz.request.match(f"{BASEURI}/check") is not None:
    raw_session = wiz.session.get() or {}
    user_id = wiz.session.user_id()
    if user_id and not raw_session.get("id"):
        raw_session["id"] = user_id
    data = _session_user_data(raw_session)
    status = bool(data.get("id") or data.get("email"))
    if not status:
        payload = _jwt_payload()
        if payload.get("sub"):
            data = _session_user_data(dict(
                id=payload.get("sub", ""),
                email=payload.get("email", ""),
                name=payload.get("name", ""),
                role=payload.get("role", "user")
            ))
            wiz.session.set(**data)
            status = True
    wiz.response.status(200, status=status, session=data)
    handled = True

elif wiz.request.match(f"{BASEURI}/signup") is not None:
    name = wiz.request.query("name", "").strip()
    email = wiz.request.query("email", "").strip()
    password = wiz.request.query("password", "")
    password_confirm = wiz.request.query("password_confirm", "")

    if not name or not email or not password:
        wiz.response.status(400, message="닉네임, 이메일, 비밀번호를 입력해주세요.")
    elif len(password) < 6:
        wiz.response.status(400, message="비밀번호는 6자 이상 입력해주세요.")
    elif password != password_confirm:
        wiz.response.status(400, message="비밀번호 확인이 일치하지 않습니다.")
    elif struct.user.db.get(email=email) is not None:
        wiz.response.status(409, message="이미 가입된 이메일입니다.")
    else:
        try:
            user_id = struct.user.create(dict(
                name=name,
                email=email,
                password=password,
                mobile="",
                role="user"
            ))
            user = struct.user.get(user_id)
            user_data = _set_user_session(user)
            wiz.response.status(200, session=user_data, token=_issue_token(user_data))
        except Exception:
            wiz.response.status(500, message="회원가입 처리 중 오류가 발생했습니다.")
    handled = True

elif wiz.request.match(f"{BASEURI}/logout") is not None:
    returnTo = wiz.request.query("returnTo", "/")
    target = LOGOUT_URI if LOGOUT_URI is not None and LOGOUT_URI != f"{BASEURI}/logout" else returnTo
    _clear_all_sessions()
    _send_logout_redirect(target)
    handled = True

elif wiz.request.match(f"{BASEURI}/login") is not None:
    email = wiz.request.query("email", "").strip()
    password = wiz.request.query("password", "")

    if email or password:
        if not email or not password:
            wiz.response.status(400, message="이메일과 비밀번호를 입력해주세요.")
        else:
            user = struct.user.authenticate(email, password)
            if user is None:
                wiz.response.status(401, message="이메일 또는 비밀번호가 올바르지 않습니다.")
            else:
                user_data = _set_user_session(user)
                wiz.response.status(200, session=user_data, token=_issue_token(user_data))
        handled = True
    elif LOGIN_URL is not None and LOGIN_URL != f"{BASEURI}/login":
        wiz.response.redirect(LOGIN_URL)
        handled = True

elif config.auth_saml_use:
    wiz.model("portal/season/auth/saml").proceed()
    handled = True

if not handled:
    wiz.response.redirect("/")
