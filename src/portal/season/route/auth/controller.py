import base64
import datetime
import hashlib
import html
import hmac
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

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


def _display_name(user):
    user = user or {}
    return (
        user.get("name")
        or user.get("nickname")
        or user.get("display_name")
        or user.get("displayName")
        or user.get("username")
        or ""
    )


def _public_user(user):
    return dict(
        id=user.get("id", ""),
        email=user.get("email", ""),
        name=_display_name(user),
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
    try:
        struct.admin.record_user_activity(data["id"], "login")
    except Exception:
        pass
    return data




def _safe_return_to(value):
    value = str(value or "").strip()
    if not value.startswith("/") or value.startswith("//"):
        return "/"
    return value


def _issue_social_state(provider, return_to, mode):
    payload = dict(
        provider=provider,
        return_to=_safe_return_to(return_to),
        mode="register" if mode == "register" else "login",
        nonce=secrets.token_urlsafe(16),
        exp=int(time.time()) + 600,
    )
    encoded = _b64url(payload)
    signature = hmac.new(SECRET, encoded.encode("utf-8"), hashlib.sha256).digest()
    signed = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
    return f"{encoded}.{signed}"


def _verify_social_state(state, provider):
    parts = str(state or "").split(".")
    if len(parts) != 2:
        return {}
    encoded, raw_signature = parts
    expected = hmac.new(SECRET, encoded.encode("utf-8"), hashlib.sha256).digest()
    try:
        actual = _decode_segment(raw_signature)
        payload = json.loads(_decode_segment(encoded).decode("utf-8"))
    except Exception:
        return {}
    if not hmac.compare_digest(expected, actual):
        return {}
    if str(payload.get("provider") or "") != provider:
        return {}
    if int(payload.get("exp") or 0) < int(time.time()):
        return {}
    payload["return_to"] = _safe_return_to(payload.get("return_to") or "/")
    payload["mode"] = "register" if payload.get("mode") == "register" else "login"
    return payload


def _social_config(provider):
    auth_config = wiz.config("auth")
    social = getattr(auth_config, "social", None)
    source = getattr(social, provider, None) if social is not None else None
    return dict(
        enabled=bool(getattr(source, "enabled", False)) if source is not None else False,
        client_id=str(getattr(source, "client_id", "") or "").strip() if source is not None else "",
        client_secret=str(getattr(source, "client_secret", "") or "").strip() if source is not None else "",
        redirect_uri=str(getattr(source, "redirect_uri", "") or "").strip() if source is not None else "",
    )


def _social_redirect_uri(provider, provider_config):
    if provider_config.get("redirect_uri"):
        return provider_config["redirect_uri"]
    scheme = (_header("X-Forwarded-Proto") or "https").split(",")[0].strip()
    host = (_header("X-Forwarded-Host") or _header("Host") or "travel.wizide.com").split(",")[0].strip()
    return f"{scheme}://{host}{BASEURI}/social/{provider}/callback"


def _http_json(url, data=None, headers=None):
    body = None
    request_headers = dict(headers or {})
    if data is not None:
        body = urllib.parse.urlencode(data).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
    request = urllib.request.Request(url, data=body, headers=request_headers)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _decode_jwt_payload(token):
    parts = str(token or "").split(".")
    if len(parts) != 3:
        return {}
    try:
        return json.loads(_decode_segment(parts[1]).decode("utf-8"))
    except Exception:
        return {}


def _social_authorize_url(provider, provider_config, state, redirect_uri):
    common = dict(client_id=provider_config["client_id"], redirect_uri=redirect_uri, state=state)
    if provider == "google":
        common.update(response_type="code", scope="openid email profile", prompt="select_account")
        return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(common)
    if provider == "kakao":
        common.update(response_type="code")
        return "https://kauth.kakao.com/oauth/authorize?" + urllib.parse.urlencode(common)
    if provider == "apple":
        common.update(response_type="code", response_mode="form_post", scope="name email")
        return "https://appleid.apple.com/auth/authorize?" + urllib.parse.urlencode(common)
    return ""


def _social_profile(provider, provider_config, code, redirect_uri):
    token_data = dict(
        grant_type="authorization_code",
        client_id=provider_config["client_id"],
        redirect_uri=redirect_uri,
        code=code,
    )
    if provider_config.get("client_secret"):
        token_data["client_secret"] = provider_config["client_secret"]

    if provider == "google":
        token = _http_json("https://oauth2.googleapis.com/token", token_data)
        access_token = token.get("access_token", "")
        return _http_json(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )

    if provider == "kakao":
        token = _http_json("https://kauth.kakao.com/oauth/token", token_data)
        access_token = token.get("access_token", "")
        raw = _http_json(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        account = raw.get("kakao_account") or {}
        profile = account.get("profile") or {}
        return dict(
            sub=str(raw.get("id") or ""),
            email=account.get("email") or "",
            email_verified=bool(account.get("is_email_verified", False)),
            name=profile.get("nickname") or "",
        )

    if provider == "apple":
        token = _http_json("https://appleid.apple.com/auth/token", token_data)
        claims = _decode_jwt_payload(token.get("id_token", ""))
        if claims.get("iss") != "https://appleid.apple.com":
            return {}
        if str(claims.get("aud") or "") != provider_config["client_id"]:
            return {}
        if int(claims.get("exp") or 0) <= int(time.time()):
            return {}
        raw_user = wiz.request.query("user", "")
        try:
            apple_user = json.loads(raw_user) if raw_user else {}
        except Exception:
            apple_user = {}
        name_data = apple_user.get("name") or {}
        display_name = " ".join(filter(None, [name_data.get("lastName"), name_data.get("firstName")])).strip()
        return dict(
            sub=claims.get("sub") or "",
            email=claims.get("email") or "",
            email_verified=str(claims.get("email_verified", "")).lower() == "true",
            name=display_name,
        )

    return {}


def _privacy_hash(namespace, value):
    raw = f"{namespace}:{str(value or '').strip()}".encode("utf-8")
    return hmac.new(SECRET, raw, hashlib.sha256).hexdigest()


def _social_user(provider, profile):
    email = str(profile.get("email") or "").strip().lower()
    subject = str(profile.get("sub") or "").strip()
    if not subject:
        raise ValueError("소셜 계정 식별 정보를 확인할 수 없습니다.")
    if not email:
        raise ValueError("소셜 계정에서 이메일 제공에 동의해주세요.")
    if profile.get("email_verified") is False:
        raise ValueError("이메일이 확인된 소셜 계정만 사용할 수 있습니다.")

    identity_db = struct.db("social_identity")
    subject_hash = _privacy_hash(f"social:{provider}:subject", subject)
    email_hash = _privacy_hash("social:email", email)
    identity = identity_db.get(provider=provider, subject_hash=subject_hash)
    if identity is not None:
        user = struct.user.get(identity.get("user_id"))
        if user is not None:
            return user

    user = struct.user.find_by_email(email)
    if user is None:
        anonymous_name = f"여행자-{subject_hash[:6].upper()}"
        user_id = struct.user.create(dict(
            name=anonymous_name,
            email=email[:128],
            password=secrets.token_urlsafe(32),
            mobile="",
            role="user",
        ))
        user = struct.user.get(user_id)

    if user is None:
        raise ValueError("사용자 계정을 생성할 수 없습니다.")

    now = datetime.datetime.now()
    try:
        identity_db.insert(dict(
            user_id=user.get("id"),
            provider=provider,
            subject_hash=subject_hash,
            email_hash=email_hash,
            created=now,
            updated=now,
        ))
    except Exception:
        identity = identity_db.get(provider=provider, subject_hash=subject_hash)
        if identity is None or identity.get("user_id") != user.get("id"):
            raise ValueError("소셜 계정 연결 정보를 저장할 수 없습니다.")
    return user


def _send_login_redirect(target, user_data, token):
    target = _safe_return_to(target)
    safe_target = html.escape(target, quote=True)
    script_target = json.dumps(target)
    script_user = json.dumps(user_data, ensure_ascii=False)
    script_token = json.dumps(token)
    wiz.response.send(f"""<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="0;url={safe_target}">
</head>
<body>
    <script>
    (function () {{
        try {{
            window.localStorage.setItem("tour-on-user", JSON.stringify({script_user}));
            window.localStorage.setItem("tour-on-jwt", {script_token});
        }} catch (e) {{}}
        window.location.replace({script_target});
    }})();
    </script>
</body>
</html>""", content_type="text/html; charset=utf-8")


def _send_social_error(message, return_to="/", mode="login"):
    params = urllib.parse.urlencode(dict(
        socialError=message,
        returnTo=_safe_return_to(return_to),
        mode="register" if mode == "register" else "login",
    ))
    wiz.response.redirect(f"/login?{params}")


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
        name=_display_name(raw),
        role=raw.get("role", "user")
    )


handled = False

social_status = wiz.request.match(f"{BASEURI}/social/providers")
social_callback = wiz.request.match(f"{BASEURI}/social/<provider>/callback")
social_start = wiz.request.match(f"{BASEURI}/social/<provider>")

if social_status is not None:
    providers = {}
    for provider in ["kakao", "apple", "google"]:
        provider_config = _social_config(provider)
        missing_secret = provider in ["google", "apple"] and not provider_config.get("client_secret")
        providers[provider] = dict(
            available=bool(
                provider_config.get("enabled")
                and provider_config.get("client_id")
                and not missing_secret
            ),
            callback_uri=_social_redirect_uri(provider, provider_config),
        )
    wiz.response.status(200, providers=providers)
    handled = True

elif social_callback is not None:
    provider = str(social_callback.provider or "").lower()
    state = str(wiz.request.query("state", "") or "")
    state_payload = _verify_social_state(state, provider)
    return_to = _safe_return_to(state_payload.get("return_to") or "/")
    mode = str(state_payload.get("mode") or "login")
    provider_config = _social_config(provider)
    error = str(wiz.request.query("error", "") or "")

    if provider not in ["apple", "google", "kakao"]:
        _send_social_error("지원하지 않는 로그인 방식입니다.", return_to, mode)
    elif error:
        _send_social_error("소셜 로그인이 취소되었습니다.", return_to, mode)
    elif not state_payload:
        _send_social_error("로그인 요청이 만료되었습니다. 다시 시도해주세요.", return_to, mode)
    else:
        try:
            code = str(wiz.request.query("code", "") or "")
            redirect_uri = _social_redirect_uri(provider, provider_config)
            profile = _social_profile(provider, provider_config, code, redirect_uri)
            if not code or not profile.get("sub"):
                raise ValueError("소셜 계정 정보를 확인할 수 없습니다.")
            user = _social_user(provider, profile)
            user_data = _set_user_session(user)
            token = _issue_token(user_data)
            wiz.session.set(social_auth_state="", social_provider="", social_return_to="", social_auth_mode="")
            _send_login_redirect(return_to, user_data, token)
        except ValueError as error:
            _send_social_error(str(error), return_to, mode)
        except Exception:
            _send_social_error("소셜 로그인 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", return_to, mode)
    handled = True

elif social_start is not None:
    provider = str(social_start.provider or "").lower()
    return_to = _safe_return_to(wiz.request.query("returnTo", "/"))
    mode = str(wiz.request.query("mode", "login") or "login")
    provider_config = _social_config(provider)
    missing_secret = provider in ["google", "apple"] and not provider_config.get("client_secret")

    if provider not in ["apple", "google", "kakao"]:
        _send_social_error("지원하지 않는 로그인 방식입니다.", return_to, mode)
    elif not provider_config.get("enabled") or not provider_config.get("client_id") or missing_secret:
        _send_social_error("현재 이 간편 로그인은 설정 중입니다. 이메일 로그인을 이용해주세요.", return_to, mode)
    else:
        state = _issue_social_state(provider, return_to, mode)
        redirect_uri = _social_redirect_uri(provider, provider_config)
        wiz.session.set(
            social_auth_state=state,
            social_provider=provider,
            social_return_to=return_to,
            social_auth_mode=mode,
        )
        wiz.response.redirect(_social_authorize_url(provider, provider_config, state, redirect_uri))
    handled = True

elif wiz.request.match(f"{BASEURI}/check") is not None:
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
    if status:
        try:
            struct.admin.record_user_activity(data.get("id", ""), "visit")
        except Exception:
            pass
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
    elif struct.user.find_by_email(email) is not None:
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
            token = _issue_token(user_data)
        except Exception:
            wiz.response.status(500, message="회원가입 처리 중 오류가 발생했습니다.")
        else:
            wiz.response.status(200, session=user_data, token=token)
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
