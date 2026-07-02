import base64
import datetime
import hashlib
import hmac
import json
import math
import time

session = wiz.model("portal/season/session").use()
struct = wiz.model("struct")
ai_chat = wiz.model("ai_chat")
ai_tools = wiz.model("ai_tools")
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


def _json_query_string(name, fallback):
    raw = wiz.request.query(name, fallback)
    try:
        parsed = json.loads(raw or fallback)
    except Exception:
        parsed = json.loads(fallback)
    return json.dumps(parsed, ensure_ascii=False)


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


def _saved_course_rows(user_id):
    rows = struct.db("saved_course").rows(user_id=user_id, orderby="updated", order="DESC")
    for row in rows:
        row["created"] = str(row.get("created", ""))
        row["updated"] = str(row.get("updated", ""))
    return rows


def _json_loads(value, fallback):
    try:
        if value is None or value == "":
            return fallback
        return json.loads(value)
    except Exception:
        return fallback


def _request_payload(name="data"):
    payload = _json_loads(wiz.request.query(name, "{}"), {})
    if not isinstance(payload, dict):
        payload = {}
    for key, value in dict(wiz.request.query()).items():
        if key not in [name]:
            payload[key] = value
    return payload


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value, default=None):
    try:
        if value in [None, ""]:
            return default
        return float(value)
    except Exception:
        return default


def _distance_meters(lat1, lng1, lat2, lng2):
    lat1 = _safe_float(lat1)
    lng1 = _safe_float(lng1)
    lat2 = _safe_float(lat2)
    lng2 = _safe_float(lng2)
    if None in [lat1, lng1, lat2, lng2]:
        return None
    radius = 6371000
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return radius * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def _community_created_label(created):
    if not created:
        return "방금"
    if isinstance(created, str):
        try:
            created = datetime.datetime.fromisoformat(created)
        except Exception:
            return "방금"
    delta = datetime.datetime.now() - created
    minutes = max(0, int(delta.total_seconds() // 60))
    if minutes < 1:
        return "방금"
    if minutes < 60:
        return f"{minutes}분 전"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}시간 전"
    return f"{hours // 24}일 전"


def _community_created_age(created):
    if not created:
        return 0
    if isinstance(created, str):
        try:
            created = datetime.datetime.fromisoformat(created)
        except Exception:
            return 0
    return max(0, int((datetime.datetime.now() - created).total_seconds() // 60))


def _community_device_owner_key():
    actor_key = str(wiz.request.query("actor_key", "")).strip()
    if not actor_key:
        return ""
    return f"device:{hashlib.md5(actor_key.encode('utf-8')).hexdigest()[:24]}"


def _community_owner_key():
    user = _current_user()
    if user.get("id"):
        return str(user.get("id", ""))[:32]
    return _community_device_owner_key()


def _community_post_payload(row, owner_key=""):
    created = row.get("created")
    return dict(
        id=row.get("id", ""),
        kind=row.get("kind", "post"),
        topic=row.get("topic", "recommend"),
        title=row.get("title", ""),
        summary=row.get("summary", ""),
        category=row.get("category", ""),
        destination=row.get("destination", ""),
        place=row.get("place", ""),
        photo=row.get("photo", ""),
        photoName=row.get("photo_name", ""),
        author=row.get("author", "") or "여행자",
        likes=_safe_int(row.get("likes"), 0),
        comments=_safe_int(row.get("comments"), 0),
        views=_safe_int(row.get("views"), 0),
        votes=_safe_int(row.get("votes"), 0),
        tags=_json_loads(row.get("tags", "[]"), []),
        poll=_json_loads(row.get("poll", ""), None),
        owned=bool(owner_key and row.get("user_id", "") == owner_key),
        createdAt=_community_created_age(created),
        createdLabel=_community_created_label(created)
    )


def _community_comment_db():
    db = struct.db("community_comment")
    try:
        db.orm.create_table(safe=True)
    except Exception:
        pass
    return db


def _community_reaction_db():
    db = struct.db("community_reaction")
    try:
        db.orm.create_table(safe=True)
    except Exception:
        pass
    return db


def _community_actor_key():
    user = _current_user()
    if user.get("id"):
        return f"user:{user.get('id')}"
    actor_key = str(wiz.request.query("actor_key", "")).strip()
    if actor_key:
        return f"device:{actor_key[:140]}"
    return ""


def _community_reaction_id(post_id, reaction_type, actor_key):
    return hashlib.md5(f"{post_id}:{reaction_type}:{actor_key}".encode("utf-8")).hexdigest()


def _community_comment_payload(row):
    created = row.get("created")
    return dict(
        id=row.get("id", ""),
        postId=row.get("post_id", ""),
        author=row.get("author", "") or "여행자",
        body=row.get("body", ""),
        createdAt=_community_created_age(created),
        createdLabel=_community_created_label(created)
    )


def _community_update_count(post_id, key, amount=1):
    db = struct.db("community_post")
    row = db.get(id=post_id)
    if row is None:
        return None
    value = max(0, _safe_int(row.get(key), 0) + amount)
    db.update({
        key: value,
        "updated": datetime.datetime.now()
    }, id=post_id)
    return db.get(id=post_id)


def community_posts():
    owner_key = _community_owner_key()
    rows = struct.db("community_post").rows()
    posts = [_community_post_payload(row, owner_key) for row in rows]
    posts.sort(key=lambda item: item.get("createdAt", 0))
    wiz.response.status(200, posts=posts)


def community_my_posts():
    owner_key = _community_owner_key()
    if not owner_key:
        wiz.response.status(400, message="보관함 사용자 정보가 없습니다.")
        return
    rows = struct.db("community_post").rows(user_id=owner_key)
    posts = [_community_post_payload(row, owner_key) for row in rows]
    posts.sort(key=lambda item: item.get("createdAt", 0))
    wiz.response.status(200, posts=posts)


def community_comments():
    post_id = wiz.request.query("post_id", "").strip()
    if not post_id:
        wiz.response.status(400, message="게시글 정보가 없습니다.")
        return
    rows = _community_comment_db().rows(post_id=post_id, orderby="created", order="ASC", dump=100)
    comments = [_community_comment_payload(row) for row in rows]
    comments.sort(key=lambda item: item.get("createdAt", 0), reverse=True)
    wiz.response.status(200, comments=comments)


def view_community_post():
    post_id = wiz.request.query("post_id", "").strip()
    owner_key = _community_owner_key()
    row = _community_update_count(post_id, "views", 1)
    if row is None:
        wiz.response.status(404, message="게시글을 찾을 수 없습니다.")
        return
    wiz.response.status(200, post=_community_post_payload(row, owner_key))


def like_community_post():
    post_id = wiz.request.query("post_id", "").strip()
    actor_key = _community_actor_key()
    owner_key = _community_owner_key()
    if not actor_key:
        wiz.response.status(400, message="좋아요 사용자 정보가 없습니다.")
        return

    post_db = struct.db("community_post")
    row = post_db.get(id=post_id)
    if row is None:
        wiz.response.status(404, message="게시글을 찾을 수 없습니다.")
        return

    reaction_db = _community_reaction_db()
    reaction_id = _community_reaction_id(post_id, "like", actor_key)
    if reaction_db.get(id=reaction_id) is not None:
        wiz.response.status(200, post=_community_post_payload(row, owner_key), liked=True, already=True)
        return

    now = datetime.datetime.now()
    reaction_db.insert(dict(
        id=reaction_id,
        post_id=post_id,
        user_key=actor_key,
        reaction_type="like",
        option="",
        created=now
    ))
    row = _community_update_count(post_id, "likes", 1)
    wiz.response.status(200, post=_community_post_payload(row, owner_key), liked=True, already=False)


def vote_community_poll():
    post_id = wiz.request.query("post_id", "").strip()
    option = wiz.request.query("option", "").strip()
    actor_key = _community_actor_key()
    owner_key = _community_owner_key()
    if not actor_key:
        wiz.response.status(400, message="투표 사용자 정보가 없습니다.")
        return

    post_db = struct.db("community_post")
    row = post_db.get(id=post_id)
    if row is None:
        wiz.response.status(404, message="게시글을 찾을 수 없습니다.")
        return

    poll = _json_loads(row.get("poll", ""), None)
    options = poll.get("options", []) if isinstance(poll, dict) else []
    if not option or option not in options:
        wiz.response.status(400, message="투표 선택지가 올바르지 않습니다.")
        return

    reaction_db = _community_reaction_db()
    reaction_id = _community_reaction_id(post_id, "poll", actor_key)
    existing = reaction_db.get(id=reaction_id)
    if existing is not None:
        wiz.response.status(
            200,
            post=_community_post_payload(row, owner_key),
            voted=True,
            already=True,
            selectedOption=existing.get("option", "")
        )
        return

    counts = poll.get("counts") if isinstance(poll.get("counts"), dict) else {}
    counts[option] = _safe_int(counts.get(option), 0) + 1
    poll["counts"] = counts
    now = datetime.datetime.now()
    reaction_db.insert(dict(
        id=reaction_id,
        post_id=post_id,
        user_key=actor_key,
        reaction_type="poll",
        option=option[:200],
        created=now
    ))
    post_db.update({
        "poll": json.dumps(poll, ensure_ascii=False),
        "votes": _safe_int(row.get("votes"), 0) + 1,
        "updated": now
    }, id=post_id)
    row = post_db.get(id=post_id)
    wiz.response.status(200, post=_community_post_payload(row, owner_key), voted=True, already=False, selectedOption=option)


def delete_community_post():
    post_id = wiz.request.query("post_id", "").strip()
    owner_key = _community_owner_key()
    if not owner_key:
        wiz.response.status(400, message="삭제 사용자 정보가 없습니다.")
        return

    post_db = struct.db("community_post")
    row = post_db.get(id=post_id)
    if row is None:
        wiz.response.status(404, message="게시글을 찾을 수 없습니다.")
        return
    if row.get("user_id", "") != owner_key:
        wiz.response.status(403, message="내가 쓴 글만 삭제할 수 있습니다.")
        return

    try:
        _community_comment_db().delete(post_id=post_id)
    except Exception:
        pass
    try:
        _community_reaction_db().delete(post_id=post_id)
    except Exception:
        pass
    post_db.delete(id=post_id)
    wiz.response.status(200, post_id=post_id)


def save_community_comment():
    post_id = wiz.request.query("post_id", "").strip()
    body = wiz.request.query("body", "").strip()
    if not post_id or not body:
        wiz.response.status(400, message="댓글 내용을 입력해주세요.")
        return

    post_db = struct.db("community_post")
    post = post_db.get(id=post_id)
    if post is None:
        wiz.response.status(404, message="게시글을 찾을 수 없습니다.")
        return

    now = datetime.datetime.now()
    user = _current_user()
    comment_id = hashlib.md5(f"{post_id}:{now.timestamp()}:{body}".encode("utf-8")).hexdigest()
    comment_db = _community_comment_db()
    comment_db.insert(dict(
        id=comment_id,
        post_id=post_id,
        user_id=user.get("id", ""),
        author=str(user.get("name") or wiz.request.query("author", "") or "여행자")[:80],
        body=body,
        created=now
    ))
    count = comment_db.count(post_id=post_id) or _safe_int(post.get("comments"), 0) + 1
    post_db.update({
        "comments": count,
        "updated": now
    }, id=post_id)
    row = post_db.get(id=post_id)
    wiz.response.status(200, post=_community_post_payload(row, _community_owner_key()), comment=_community_comment_payload(comment_db.get(id=comment_id)))


def save_community_post():
    raw = wiz.request.query("post", "{}")
    post = _json_loads(raw, {})
    if not isinstance(post, dict):
        wiz.response.status(400, message="커뮤니티 글 정보가 없습니다.")
        return

    now = datetime.datetime.now()
    user = _current_user()
    owner_key = str(user.get("id") or "")[:32] or _community_device_owner_key()
    post_id = str(post.get("id") or "").strip()
    if not post_id:
        post_id = hashlib.md5(f"{now.timestamp()}:{post.get('title', '')}".encode("utf-8")).hexdigest()

    db = struct.db("community_post")
    exists = db.get(id=post_id)
    if exists is not None and exists.get("user_id", "") and owner_key and exists.get("user_id", "") != owner_key:
        wiz.response.status(403, message="내가 쓴 글만 수정할 수 있습니다.")
        return
    data = dict(
        id=post_id,
        user_id=owner_key,
        kind=str(post.get("kind") or "post")[:20],
        topic=str(post.get("topic") or "recommend")[:40],
        title=str(post.get("title") or "")[:200],
        summary=str(post.get("summary") or ""),
        category=str(post.get("category") or "")[:60],
        destination=str(post.get("destination") or "")[:120],
        place=str(post.get("place") or "")[:160],
        photo=str(post.get("photo") or ""),
        photo_name=str(post.get("photoName") or post.get("photo_name") or "")[:200],
        author=str(post.get("author") or user.get("name") or "여행자")[:80],
        likes=_safe_int(post.get("likes"), 0),
        comments=_safe_int(post.get("comments"), 0),
        views=_safe_int(post.get("views"), 0),
        votes=_safe_int(post.get("votes"), 0),
        tags=json.dumps(post.get("tags") if isinstance(post.get("tags"), list) else [], ensure_ascii=False),
        poll=json.dumps(post.get("poll"), ensure_ascii=False) if post.get("poll") else "",
        updated=now
    )
    if exists is None:
        data["created"] = now
        db.insert(data)
    else:
        db.update(data, id=post_id)

    row = db.get(id=post_id)
    wiz.response.status(200, post=_community_post_payload(row, owner_key))

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
        wiz.response.status(400, message="이름, 이메일, 비밀번호를 입력해주세요.")
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
    community_action = wiz.request.query("community_action", "").strip()
    if community_action == "list":
        community_posts()
        return
    if community_action == "mine":
        community_my_posts()
        return
    if community_action == "comments":
        community_comments()
        return

    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    wiz.response.status(200, course_ids=_saved_course_ids(user_id), courses=_saved_course_rows(user_id))


def log_filter_event():
    filter_key = wiz.request.query("filter_key", "").strip()
    filter_value = wiz.request.query("filter_value", "").strip()
    if not filter_key or not filter_value:
        wiz.response.status(400, message="필터 정보가 없습니다.")
        return
    struct.admin.log_filter_event(filter_key, filter_value, _current_user_id())
    wiz.response.status(200)


def search_course_places():
    rows = struct.place.nearby_search(
        lat=wiz.request.query("lat", ""),
        lng=wiz.request.query("lng", ""),
        keyword=wiz.request.query("keyword", wiz.request.query("search", "")),
        region=wiz.request.query("region", wiz.request.query("location", "")),
        limit=wiz.request.query("limit", 8)
    )
    wiz.response.status(200, rows=rows)


def create_builder_course():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    data = _json_loads(wiz.request.query("data", "{}"), {})
    if not isinstance(data, dict):
        wiz.response.status(400, message="코스 정보가 없습니다.")
        return

    data["user_id"] = user_id
    row = struct.course.create(data)
    if row is None:
        wiz.response.status(400, message="코스 제목을 입력해주세요.")
        return

    wiz.response.status(200, row=row)


def update_builder_course():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    course_id = wiz.request.query("course_id", "").strip()
    if not course_id:
        wiz.response.status(400, message="코스 정보가 없습니다.")
        return

    current = struct.course.get(course_id, include_places=False)
    if current is None or current.get("user_id") != user_id:
        wiz.response.status(404, message="코스를 찾을 수 없습니다.")
        return

    data = _json_loads(wiz.request.query("data", "{}"), {})
    if not isinstance(data, dict):
        wiz.response.status(400, message="코스 정보가 없습니다.")
        return

    data["user_id"] = user_id
    row = struct.course.update(course_id, data)
    if row is None:
        wiz.response.status(404, message="코스를 찾을 수 없습니다.")
        return

    wiz.response.status(200, row=row)


def course_execution_courses():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    wiz.response.status(200, courses=struct.course.execution_catalog(user_id))


def course_execution():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    course_id = wiz.request.query("course_id", "").strip()
    if not course_id:
        wiz.response.status(400, message="코스 정보가 없습니다.")
        return

    execution = struct.course.execution(course_id, user_id)
    if execution is None:
        wiz.response.status(404, message="코스를 찾을 수 없습니다.")
        return

    wiz.response.status(200, execution=execution)


def course_checkin():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    course_id = wiz.request.query("course_id", "").strip()
    place_id = wiz.request.query("place_id", "").strip()
    method = wiz.request.query("method", "manual").strip()
    if not course_id or not place_id:
        wiz.response.status(400, message="체크인할 코스와 장소 정보가 필요합니다.")
        return

    row = struct.course.checkin(
        course_id=course_id,
        place_id=place_id,
        user_id=user_id,
        method=method,
        lat=wiz.request.query("lat", ""),
        lng=wiz.request.query("lng", ""),
    )
    if row is None:
        wiz.response.status(400, message="체크인을 저장하지 못했습니다.")
        return

    wiz.response.status(200, checkin=row, execution=struct.course.execution(course_id, user_id))


def zenly_presence_heatmap():
    heatmap = struct.zenly.heatmap(
        region=wiz.request.query("region", wiz.request.query("location", "")),
        limit=wiz.request.query("limit", 12)
    )
    wiz.response.status(200, heatmap=heatmap)


def zenly_presence_hourly():
    place_id = wiz.request.query("place_id", wiz.request.query("placeId", "")).strip()
    if not place_id:
        wiz.response.status(400, message="장소 정보가 필요합니다.")
        return
    wiz.response.status(200, hourly=struct.zenly.hourly(place_id, wiz.request.query("hours", 12)))


def zenly_presence_touch():
    row = None
    place_id = wiz.request.query("place_id", wiz.request.query("placeId", "")).strip()
    region = wiz.request.query("region", wiz.request.query("location", ""))
    if place_id:
        row = struct.zenly.record_presence(place_id, region=region)
    else:
        row = struct.zenly.record_presence_nearby(
            wiz.request.query("lat", ""),
            wiz.request.query("lng", ""),
            region=region,
            radius=wiz.request.query("radius", 180)
        )
    if row is None:
        wiz.response.status(204, touched=False)
        return
    wiz.response.status(200, touched=True)


def zenly_signals_nearby():
    payload = struct.zenly.nearby_signals(
        lat=wiz.request.query("lat", ""),
        lng=wiz.request.query("lng", ""),
        radius=wiz.request.query("radius", 1500),
        user_id=_current_user_id()
    )
    wiz.response.status(200, **payload)


def zenly_signal_create():
    status, payload = struct.zenly.create_signal(_current_user(), _request_payload())
    wiz.response.status(status, **payload)


def zenly_signal_respond():
    status, payload = struct.zenly.respond_signal(
        wiz.request.query("signal_id", wiz.request.query("signalId", "")),
        _current_user()
    )
    wiz.response.status(status, **payload)


def zenly_signal_response_update():
    status, payload = struct.zenly.update_response(
        wiz.request.query("signal_id", wiz.request.query("signalId", "")),
        wiz.request.query("response_id", wiz.request.query("responseId", "")),
        wiz.request.query("status", ""),
        _current_user()
    )
    wiz.response.status(status, **payload)


def zenly_signal_report():
    status, payload = struct.zenly.report_signal(
        wiz.request.query("signal_id", wiz.request.query("signalId", "")),
        _current_user(),
        wiz.request.query("reason", "")
    )
    wiz.response.status(status, **payload)


def directions_segment():
    segment = ai_tools.execute_segment_lookup(dict(
        origin_lat=wiz.request.query("origin_lat", ""),
        origin_lng=wiz.request.query("origin_lng", ""),
        destination_place_id=wiz.request.query("destination_place_id", "").strip(),
        mode=wiz.request.query("mode", "walking").strip(),
    ))
    if segment.get("status") == "not_available":
        wiz.response.status(400, message=segment.get("message", "구간 정보를 계산하지 못했습니다."))
        return
    if segment.get("status") == "not_found":
        wiz.response.status(404, message="도착 장소를 찾을 수 없습니다.")
        return

    wiz.response.status(200, segment=segment)


def save_course():
    community_action = wiz.request.query("community_action", "").strip()
    if community_action == "post":
        save_community_post()
        return
    if community_action == "view":
        view_community_post()
        return
    if community_action == "like":
        like_community_post()
        return
    if community_action == "vote":
        vote_community_poll()
        return
    if community_action == "comment":
        save_community_comment()
        return
    if community_action == "delete":
        delete_community_post()
        return

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
        wiz.response.status(200, course_ids=_saved_course_ids(user_id), courses=_saved_course_rows(user_id))
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
        places_json=_json_query_string("places_json", "[]"),
        route_json=_json_query_string("route_json", "{}"),
        updated=now
    )

    if exists is None:
        data["created"] = now
        db.insert(data)
    else:
        db.update(data, id=exists["id"])

    if like_exists is None:
        try:
            like_db.insert(dict(
                user_id=user_id,
                course_id=course_id,
                created=now
            ))
        except Exception:
            pass

    wiz.response.status(200, course_ids=_saved_course_ids(user_id), courses=_saved_course_rows(user_id))


def chat_send():
    status, payload = ai_chat.send(
        wiz.request.query("prompt", ""),
        wiz.request.query("history", "[]"),
        _current_user_id(),
        wiz.request.query("thread_id", "").strip()
    )
    wiz.response.status(status, **payload)


def chat_threads():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    wiz.response.status(200, threads=ai_chat.threads(user_id))


def chat_thread():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    thread = ai_chat.thread(user_id, wiz.request.query("thread_id", "").strip())
    if thread is None:
        wiz.response.status(404, message="대화 기록을 찾을 수 없습니다.")
        return

    wiz.response.status(200, thread=thread)
