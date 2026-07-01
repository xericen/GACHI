import json
import datetime
import base64
import hashlib
import hmac
import time

session = wiz.model("portal/season/session").use()
struct = wiz.model("struct")
SECRET = wiz.model("auth_config").jwt_secret()


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
    session.set(id=data["id"], email=data["email"], name=data["name"], role=data["role"])
    return data


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


def _current_user():
    data = _session_user_data(session.get() or {})
    if data.get("id") or data.get("email"):
        return data

    payload = _jwt_payload()
    if payload.get("sub"):
        data = _session_user_data(dict(
            id=payload.get("sub", ""),
            email=payload.get("email", ""),
            name=payload.get("name", ""),
            role=payload.get("role", "user")
        ))
        session.set(id=data["id"], email=data["email"], name=data["name"], role=data["role"])
        return data

    return {}


def _current_user_id():
    return _current_user().get("id", "")


def _saved_course_ids(user_id):
    rows = struct.db("saved_course").rows(user_id=user_id)
    return [row.get("course_id") for row in rows if row.get("course_id")]


def login():
    email = wiz.request.query("email", "").strip()
    password = wiz.request.query("password", "")

    if not email or not password:
        wiz.response.status(400, message="이메일과 비밀번호를 입력해주세요.")
        return

    user = struct.user.authenticate(email, password)
    if user is None:
        wiz.response.status(401, message="이메일 또는 비밀번호가 올바르지 않습니다.")
        return

    user_data = _set_user_session(user)
    wiz.response.status(200, session=user_data, token=_issue_token(user_data))


def register():
    name = wiz.request.query("name", "").strip()
    email = wiz.request.query("email", "").strip()
    password = wiz.request.query("password", "")
    password_confirm = wiz.request.query("password_confirm", "")

    if not name or not email or not password:
        wiz.response.status(400, message="닉네임, 이메일, 비밀번호를 입력해주세요.")
        return

    if len(password) < 6:
        wiz.response.status(400, message="비밀번호는 6자 이상 입력해주세요.")
        return

    if password != password_confirm:
        wiz.response.status(400, message="비밀번호 확인이 일치하지 않습니다.")
        return

    if struct.user.db.get(email=email) is not None:
        wiz.response.status(409, message="이미 가입된 이메일입니다.")
        return

    try:
        user_id = struct.user.create(dict(
            name=name,
            email=email,
            password=password,
            mobile="",
            role="user"
        ))
    except Exception:
        wiz.response.status(500, message="회원가입 처리 중 오류가 발생했습니다.")
        return

    user = struct.user.get(user_id)
    user_data = _set_user_session(user)
    wiz.response.status(200, session=user_data, token=_issue_token(user_data))


def saved_courses():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    wiz.response.status(200, course_ids=_saved_course_ids(user_id))


def save_course():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    course_id = wiz.request.query("course_id", "").strip()
    saved = str(wiz.request.query("saved", "true")).lower() not in ["false", "0", "no"]

    if not course_id:
        wiz.response.status(400, message="코스 정보가 없습니다.")
        return

    db = struct.db("saved_course")
    like_db = struct.db("course_like")
    exists = db.get(user_id=user_id, course_id=course_id)
    like_exists = like_db.get(user_id=user_id, course_id=course_id)

    if not saved:
        if exists is not None:
            db.delete(id=exists["id"])
        if like_exists is not None:
            like_db.delete(id=like_exists["id"])
        wiz.response.status(200, course_ids=_saved_course_ids(user_id))
        return

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = dict(
        user_id=user_id,
        course_id=course_id,
        title=wiz.request.query("title", "").strip(),
        location=wiz.request.query("location", "").strip(),
        summary=wiz.request.query("summary", "").strip(),
        duration=wiz.request.query("duration", "").strip(),
        rating=wiz.request.query("rating", "").strip(),
        icon=wiz.request.query("icon", "").strip(),
        tone=wiz.request.query("tone", "").strip(),
        updated=now
    )

    if exists is None:
        data["created"] = now
        db.insert(data)
    else:
        db.update(data, id=exists["id"])

    if like_exists is None:
        like_db.insert(dict(
            user_id=user_id,
            course_id=course_id,
            created=now
        ))

    wiz.response.status(200, course_ids=_saved_course_ids(user_id))


def overview():
    """대시보드 통계 및 최근 게시물"""
    # Post 통계 (패키지 Struct 접근)
    post_struct = struct.post
    total_posts = post_struct.post.db.count() or 0
    published_posts = post_struct.post.db.count(status="published") or 0
    draft_posts = post_struct.post.db.count(status="draft") or 0

    # User 통계 (로컬 Struct)
    total_members = struct.user.count()

    stats = [
        {"label": "전체 게시물", "value": str(total_posts), "change": 0, "icon": "📄", "bgColor": "bg-red-50"},
        {"label": "공개 게시물", "value": str(published_posts), "change": 0, "icon": "✅", "bgColor": "bg-green-50"},
        {"label": "임시저장", "value": str(draft_posts), "change": 0, "icon": "✏️", "bgColor": "bg-yellow-50"},
        {"label": "멤버", "value": str(total_members), "change": 0, "icon": "👥", "bgColor": "bg-purple-50"},
    ]

    # 최근 게시물 5건
    recent = post_struct.post.db.rows(orderby="created", order="DESC", page=1, dump=5)
    colors = [
        "bg-red-100 text-red-700",
        "bg-pink-100 text-pink-700",
        "bg-green-100 text-green-700",
        "bg-amber-100 text-amber-700",
        "bg-red-100 text-red-700",
    ]
    for i, r in enumerate(recent):
        r["author"] = r.get("author_name", "")
        r["date"] = str(r.get("created", ""))[:10]
        r["avatarColor"] = colors[i % len(colors)]

    wiz.response.status(200, stats=stats, recent=recent)
