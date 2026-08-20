import base64
import datetime
import hashlib
import hmac
import json
import math
import os
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

session = wiz.model("portal/season/session").use()
struct = wiz.model("struct")
ai_chat = wiz.model("ai_chat")
ai_tools = wiz.model("ai_tools")
SECRET = wiz.model("auth_config").jwt_secret()
_NAVER_MENU_CACHE = {}
_NAVER_MENU_CACHE_SECONDS = 600
_NAVER_PLACE_SEARCH_CACHE = {}
_NAVER_PLACE_SEARCH_CACHE_SECONDS = 300
_NAVER_DIRECTIONS_CACHE_SECONDS = 300
_NAVER_DIRECTIONS_CACHE_LIMIT = 2000
_ODSAY_TRANSIT_CACHE_SECONDS = 600
_ODSAY_TRANSIT_CACHE_LIMIT = 2000
_WALKING_ROUTE_CACHE_SECONDS = 600
_WALKING_ROUTE_CACHE_LIMIT = 2000
_OPENROUTESERVICE_SAFE_DAILY_LIMIT = 1900
_OSM_FOOT_ROUTER_MIN_INTERVAL_SECONDS = 1.1


def _project_env_value(*names):
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value

    try:
        env_source = wiz.project.fs().read(".env") or ""
    except Exception:
        return ""

    expected = set(names)
    for raw_line in env_source.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() not in expected:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if value:
            return value
    return ""


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


def _portone_identity_config():
    return dict(
        store_id=_project_env_value("PORTONE_STORE_ID", "PUBLIC_PORTONE_STORE_ID"),
        channel_key=_project_env_value("PORTONE_IDENTITY_CHANNEL_KEY", "PUBLIC_PORTONE_PASS_CHANNEL_KEY"),
        api_secret=_project_env_value("PORTONE_API_SECRET")
    )


def _portone_identity_configured(config=None):
    config = config or _portone_identity_config()
    return all(config.get(key) for key in ["store_id", "channel_key", "api_secret"])


def _identity_profile_from_session(user_id):
    if not user_id or session.get("identity_user_id", "") != user_id:
        return dict(verified=False, name="", age=0, gender="", verifiedAt="")
    if not session.get("identity_verified", False):
        return dict(verified=False, name="", age=0, gender="", verifiedAt="")
    return dict(
        verified=True,
        name=str(session.get("identity_name", "") or ""),
        age=_safe_int(session.get("identity_age", 0), 0),
        gender=str(session.get("identity_gender", "") or ""),
        verifiedAt=str(session.get("identity_verified_at", "") or "")
    )


def _identity_age(birth_date):
    try:
        born = datetime.datetime.strptime(str(birth_date or "")[:10], "%Y-%m-%d").date()
    except Exception:
        return 0
    today = datetime.date.today()
    return max(0, today.year - born.year - ((today.month, today.day) < (born.month, born.day)))


def _identity_gender(value):
    return {
        "MALE": "남성",
        "FEMALE": "여성",
        "OTHER": "기타"
    }.get(str(value or "").upper(), "")


def _portone_identity(identity_verification_id, config):
    endpoint = "https://api.portone.io/identity-verifications/{}".format(
        urllib.parse.quote(identity_verification_id, safe="")
    )
    request = urllib.request.Request(
        endpoint,
        headers={
            "Authorization": "PortOne {}".format(config["api_secret"]),
            "Accept": "application/json"
        },
        method="GET"
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _saved_course_route(row):
    try:
        route = json.loads(row.get("route_json") or "{}")
    except Exception:
        route = {}
    return route if isinstance(route, dict) else {}


def _saved_course_is_mine(row, user_id):
    course_id = row.get("course_id", "")
    course = struct.db("course").get(id=course_id) if course_id else None
    return str(_saved_course_route(row).get("source") or "") == "mine" or (
        course is not None and str(course.get("user_id") or "") == str(user_id)
    )


def _saved_course_ids(user_id):
    rows = struct.db("saved_course").rows(user_id=user_id)
    return [
        row.get("course_id") for row in rows
        if row.get("course_id") and not _saved_course_is_mine(row, user_id)
    ]


def _saved_course_rows(user_id):
    rows = struct.db("saved_course").rows(user_id=user_id, orderby="updated", order="DESC")
    rows = [row for row in rows if not _saved_course_is_mine(row, user_id)]
    for row in rows:
        row["created"] = str(row.get("created", ""))
        row["updated"] = str(row.get("updated", ""))
    return rows


def _legacy_owned_course_places(saved_row):
    places = _json_loads(saved_row.get("places_json"), [])
    if not isinstance(places, list):
        return []

    course_id = str(saved_row.get("course_id") or "")
    place_db = struct.db("place")
    now = datetime.datetime.now()
    normalized = []
    for index, raw in enumerate(places, start=1):
        place = raw if isinstance(raw, dict) else {}
        raw_place_id = str(place.get("place_id") or place.get("id") or "").strip()
        place_id = raw_place_id if raw_place_id and len(raw_place_id) <= 32 else ""
        if not place_id:
            identity = f"{course_id}:{index}:{place.get('name', '')}:{place.get('lat', '')}:{place.get('lng', '')}"
            place_id = hashlib.md5(identity.encode("utf-8")).hexdigest()

        if place_db.get(id=place_id) is None:
            place_db.insert(dict(
                id=place_id,
                name=str(place.get("name") or f"코스 장소 {index}").strip()[:200],
                category=str(place.get("tag") or place.get("category") or "여행지").strip()[:80],
                image=str(place.get("image") or "").strip()[:500],
                address=str(place.get("address") or place.get("area") or "").strip()[:300],
                area=str(place.get("area") or "").strip()[:100],
                latitude=str(place.get("lat") or place.get("latitude") or "").strip()[:40],
                longitude=str(place.get("lng") or place.get("longitude") or "").strip()[:40],
                is_hidden=False,
                created=now,
                updated=now,
            ))

        normalized.append(dict(
            place_id=place_id,
            name=str(place.get("name") or "").strip(),
            area=str(place.get("area") or "").strip(),
            address=str(place.get("address") or place.get("area") or "").strip(),
            category=str(place.get("tag") or place.get("category") or "여행지").strip(),
            image=str(place.get("image") or "").strip(),
            latitude=place.get("lat", place.get("latitude")),
            longitude=place.get("lng", place.get("longitude")),
            day=_safe_int(place.get("day"), 1),
            day_label=str(place.get("day_label") or "1일차").strip(),
            order_index=index,
            visit_time=str(place.get("time") or place.get("visit_time") or "").strip(),
            memo=str(place.get("tag") or place.get("memo") or "").strip(),
            item_type="place",
        ))
    return normalized


def _migrate_legacy_owned_courses(user_id):
    saved_db = struct.db("saved_course")
    course_db = struct.db("course")
    for saved_row in saved_db.rows(user_id=user_id, orderby="updated", order="ASC", dump=200):
        legacy_id = str(saved_row.get("course_id") or "").strip()
        current = course_db.get(id=legacy_id) if legacy_id else None
        owns_current = current is not None and str(current.get("user_id") or "") == str(user_id)
        if str(_saved_course_route(saved_row).get("source") or "") != "mine" and not owns_current:
            continue

        migrated = current if owns_current else None
        if migrated is None:
            duration = str(saved_row.get("duration") or "").strip()
            payload = dict(
                title=str(saved_row.get("title") or "AI 여행 코스").strip(),
                region=str(saved_row.get("location") or "").strip(),
                category="여행",
                description=str(saved_row.get("summary") or "AI와 함께 만든 여행 코스입니다.").strip(),
                cover_image="",
                image="",
                duration_type="overnight" if duration else "hours",
                duration_value=duration or "4",
                companion_type="",
                is_public=False,
                is_featured=False,
                user_id=user_id,
                places=_legacy_owned_course_places(saved_row),
                tags=["여행", "AI플래너", str(saved_row.get("location") or "").strip()],
            )
            preserve_id = legacy_id if len(legacy_id) <= 32 and current is None else ""
            migrated = struct.course.create(payload, course_id=preserve_id)

        if migrated is not None:
            saved_db.delete(id=saved_row.get("id"))
            own_like = struct.db("course_like").get(user_id=user_id, course_id=legacy_id)
            if own_like is not None:
                struct.db("course_like").delete(id=own_like.get("id"))


def _owned_course_rows(user_id):
    _migrate_legacy_owned_courses(user_id)
    rows = struct.db("course").rows(user_id=user_id, orderby="updated", order="DESC", dump=200)
    return [struct.course.normalize(row, include_places=True) for row in rows]


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
    rows = [row for row in rows if row.get("kind", "post") not in ["course_story", "profile_feed"]]
    posts = [_community_post_payload(row, owner_key) for row in rows]
    posts.sort(key=lambda item: item.get("createdAt", 0))
    wiz.response.status(200, posts=posts)


def community_my_posts():
    owner_key = _community_owner_key()
    if not owner_key:
        wiz.response.status(400, message="보관함 사용자 정보가 없습니다.")
        return
    rows = struct.db("community_post").rows(user_id=owner_key)
    rows = [row for row in rows if row.get("kind", "post") not in ["course_story", "profile_feed"]]
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


def report_community_post():
    post_id = wiz.request.query("post_id", "").strip()
    reason = wiz.request.query("reason", "부적절한 내용").strip()[:200] or "부적절한 내용"
    actor_key = _community_actor_key()
    owner_key = _community_owner_key()
    if not actor_key:
        wiz.response.status(400, message="신고 사용자 정보가 없습니다.")
        return

    post_db = struct.db("community_post")
    row = post_db.get(id=post_id)
    if row is None:
        wiz.response.status(404, message="게시글을 찾을 수 없습니다.")
        return
    if owner_key and row.get("user_id", "") == owner_key:
        wiz.response.status(400, message="내가 쓴 글은 신고할 수 없습니다.")
        return

    reaction_db = _community_reaction_db()
    report_id = _community_reaction_id(post_id, "report", actor_key)
    if reaction_db.get(id=report_id) is not None:
        wiz.response.status(200, reported=True, already=True, message="이미 신고한 게시글입니다.")
        return

    reaction_db.insert(dict(
        id=report_id,
        post_id=post_id,
        user_key=actor_key,
        reaction_type="report",
        option=reason,
        created=datetime.datetime.now()
    ))
    wiz.response.status(200, reported=True, already=False, message="신고가 접수되었습니다.")


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

def identity_verification_status():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    config = _portone_identity_config()
    wiz.response.status(
        200,
        configured=_portone_identity_configured(config),
        identity=_identity_profile_from_session(user_id)
    )


def identity_verification_start():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    config = _portone_identity_config()
    if not _portone_identity_configured(config):
        wiz.response.status(503, configured=False, message="PASS 본인 인증 연동 설정이 필요합니다.")
        return

    identity_verification_id = "gachi-{}".format(secrets.token_hex(16))
    session.set(
        identity_pending_id=identity_verification_id,
        identity_pending_user_id=user_id,
        identity_pending_at=int(time.time())
    )
    wiz.response.status(
        200,
        configured=True,
        storeId=config["store_id"],
        channelKey=config["channel_key"],
        identityVerificationId=identity_verification_id
    )


def identity_verification_complete():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    identity_verification_id = wiz.request.query("identity_verification_id", "").strip()
    pending_id = str(session.get("identity_pending_id", "") or "")
    pending_user_id = str(session.get("identity_pending_user_id", "") or "")
    pending_at = _safe_int(session.get("identity_pending_at", 0), 0)
    if (
        not identity_verification_id
        or identity_verification_id != pending_id
        or pending_user_id != user_id
        or pending_at <= 0
        or int(time.time()) - pending_at > 600
    ):
        wiz.response.status(400, message="인증 요청이 만료됐어요. PASS 인증을 다시 시작해주세요.")
        return

    config = _portone_identity_config()
    if not _portone_identity_configured(config):
        wiz.response.status(503, configured=False, message="PASS 본인 인증 연동 설정이 필요합니다.")
        return

    verification = None
    provider_error = False
    try:
        provider_payload = _portone_identity(identity_verification_id, config)
        verification = provider_payload.get("identityVerification", provider_payload)
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError, TypeError):
        provider_error = True
    except Exception:
        provider_error = True

    if provider_error or not isinstance(verification, dict):
        wiz.response.status(502, message="PASS 인증 결과를 확인하지 못했어요. 잠시 후 다시 시도해주세요.")
        return

    if str(verification.get("status") or "").upper() != "VERIFIED":
        wiz.response.status(409, message="PASS 본인 인증이 완료되지 않았어요.")
        return

    response_store_id = str(verification.get("storeId") or "")
    response_channel_key = str(verification.get("channelKey") or "")
    if response_store_id and response_store_id != config["store_id"]:
        wiz.response.status(409, message="인증 상점 정보가 일치하지 않습니다.")
        return
    if response_channel_key and response_channel_key != config["channel_key"]:
        wiz.response.status(409, message="인증 채널 정보가 일치하지 않습니다.")
        return

    customer = verification.get("verifiedCustomer") or {}
    name = str(customer.get("name") or "").strip()
    age = _identity_age(customer.get("birthDate"))
    gender = _identity_gender(customer.get("gender"))
    if not name or age <= 0 or not gender:
        wiz.response.status(422, message="PASS에서 기본 정보를 확인하지 못했어요. 인증 수단을 바꿔 다시 시도해주세요.")
        return

    verified_at = datetime.datetime.now().isoformat(timespec="seconds")
    session.set(
        identity_verified=True,
        identity_user_id=user_id,
        identity_name=name,
        identity_age=age,
        identity_gender=gender,
        identity_verified_at=verified_at
    )
    for key in ["identity_pending_id", "identity_pending_user_id", "identity_pending_at"]:
        if session.has(key):
            session.delete(key)

    wiz.response.status(
        200,
        identity=dict(
            verified=True,
            name=name,
            age=age,
            gender=gender,
            verifiedAt=verified_at
        )
    )


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


def _update_my_profile_response():
    current_user = _current_user()
    user_id = str(current_user.get("id") or "").strip()
    user = struct.user.get(user_id) if user_id else None
    if user is None and current_user.get("email"):
        user = struct.user.db.get(email=current_user.get("email"))
        user_id = str((user or {}).get("id") or "").strip()

    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    nickname = wiz.request.query("nickname", "").strip()
    if not nickname:
        wiz.response.status(400, message="닉네임을 입력해주세요.")
        return
    if len(nickname) > 50:
        wiz.response.status(400, message="닉네임은 50자 이내로 입력해주세요.")
        return

    if user is None:
        wiz.response.status(404, message="사용자 정보를 찾을 수 없습니다.")
        return

    try:
        struct.user.update_profile(user_id, name=nickname)
        updated = struct.user.get(user_id)
    except Exception:
        wiz.response.status(500, message="프로필 저장 중 오류가 발생했습니다.")
        return

    user_data = _set_user_session(updated)
    wiz.response.status(200, session=user_data, token=_issue_token(user_data))


def update_my_profile():
    _update_my_profile_response()


def saved_courses():
    profile_action = wiz.request.query("profile_action", "").strip()
    if profile_action == "update":
        _update_my_profile_response()
        return

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
    if community_action == "course_story":
        course_id = wiz.request.query("course_id", "").strip()
        if not course_id:
            wiz.response.status(400, message="코스 정보가 없습니다.")
            return
        owner_key = _community_owner_key()
        rows = struct.db("community_post").rows(
            kind="course_story",
            place=course_id,
            orderby="created",
            order="DESC",
            dump=100
        )
        posts = [_community_post_payload(row, owner_key) for row in rows]
        wiz.response.status(200, posts=posts)
        return

    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    wiz.response.status(
        200,
        course_ids=_saved_course_ids(user_id),
        courses=_saved_course_rows(user_id),
        owned_courses=_owned_course_rows(user_id)
    )


def log_filter_event():
    filter_key = wiz.request.query("filter_key", "").strip()
    filter_value = wiz.request.query("filter_value", "").strip()
    if not filter_key or not filter_value:
        wiz.response.status(400, message="필터 정보가 없습니다.")
        return
    struct.admin.log_filter_event(filter_key, filter_value, _current_user_id())
    wiz.response.status(200)


def search_course_places():
    lat = wiz.request.query("lat", "")
    lng = wiz.request.query("lng", "")
    keyword = wiz.request.query("keyword", wiz.request.query("search", "")).strip()[:120]
    limit = wiz.request.query("limit", 8)
    stored_rows = struct.place.nearby_search(
        lat=lat,
        lng=lng,
        keyword=keyword,
        region=wiz.request.query("region", wiz.request.query("location", "")),
        limit=limit
    )
    rows = _naver_place_search_results(keyword, lat, lng, limit) + stored_rows
    client_id = _project_env_value("NAVER_MAPS_CLIENT_ID", "NCP_MAPS_CLIENT_ID")
    wiz.response.status(200, rows=rows, naver_maps_client_id=client_id)


def _naver_static_course_map_data(raw_points):
    source = json.loads(raw_points)
    if not isinstance(source, list):
        source = []
    points = []
    for index, row in enumerate(source[:12]):
        if not isinstance(row, dict):
            continue
        lat = float(row.get("lat"))
        lng = float(row.get("lng"))
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            continue
        points.append(dict(
            lat=lat,
            lng=lng,
            label=str(row.get("label") or index + 1)[:2]
        ))
    if not points:
        raise ValueError("map_points_required")

    client_id = _project_env_value("NAVER_MAPS_CLIENT_ID", "NCP_MAPS_CLIENT_ID")
    client_secret = _project_env_value("NAVER_MAPS_CLIENT_SECRET", "NCP_MAPS_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("naver_maps_config_missing")

    center_lat = sum(point["lat"] for point in points) / len(points)
    center_lng = sum(point["lng"] for point in points) / len(points)
    lat_span = max(point["lat"] for point in points) - min(point["lat"] for point in points)
    lng_span = max(point["lng"] for point in points) - min(point["lng"] for point in points)
    span = max(lat_span, lng_span)
    if span <= 0.008:
        level = 15
    elif span <= 0.02:
        level = 13
    elif span <= 0.05:
        level = 11
    elif span <= 0.12:
        level = 9
    elif span <= 0.3:
        level = 7
    else:
        level = 5

    params = [
        ("w", "900"),
        ("h", "720"),
        ("center", f"{center_lng:.7f},{center_lat:.7f}"),
        ("level", str(level)),
        ("maptype", "basic"),
        ("format", "png"),
        ("scale", "2")
    ]
    for point in points:
        params.append((
            "markers",
            f"type:d|size:mid|pos:{point['lng']:.7f} {point['lat']:.7f}|label:{point['label']}"
        ))
    if len(points) > 1:
        path = "weight:5|color:0xF20D19FF"
        for point in points:
            path += f"|pos:{point['lng']:.7f} {point['lat']:.7f}"
        params.append(("path", path))

    url = "https://maps.apigw.ntruss.com/map-static/v2/raster?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={
        "x-ncp-apigw-api-key-id": client_id,
        "x-ncp-apigw-api-key": client_secret,
        "User-Agent": "travel-wizide-course-map/1.0"
    })
    with urllib.request.urlopen(request, timeout=8) as response:
        image = response.read()
    return "data:image/png;base64," + base64.b64encode(image).decode("ascii")


def naver_maps_config():
    client_id = _project_env_value("NAVER_MAPS_CLIENT_ID", "NCP_MAPS_CLIENT_ID")
    raw_points = wiz.request.query("static_points", "")
    if not raw_points:
        wiz.response.status(200, naver_maps_client_id=client_id)

    status = 200
    message = ""
    image_data_url = ""
    try:
        image_data_url = _naver_static_course_map_data(raw_points)
    except ValueError:
        status = 400
        message = "지도 좌표가 필요합니다."
    except Exception:
        status = 502
        message = "NAVER 지도 이미지를 불러오지 못했습니다."

    if status != 200:
        wiz.response.status(status, message=message)
    wiz.response.status(200, image_data_url=image_data_url)


def _naver_coordinate(value, minimum, maximum):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < minimum or number > maximum:
        return None
    return number


def _naver_directions_cache_fs():
    root = wiz.project.fs("data")
    if not root.exists("naver-directions-cache"):
        root.makedirs("naver-directions-cache")
    return wiz.project.fs("data", "naver-directions-cache")


def _naver_directions_cache_read(cache_key, now):
    try:
        cache_fs = _naver_directions_cache_fs()
        filename = hashlib.sha256(cache_key.encode("utf-8")).hexdigest() + ".json"
        cached = cache_fs.read.json(filename, default={})
    except Exception:
        return None
    if not isinstance(cached, dict) or now - float(cached.get("saved_at", 0)) >= _NAVER_DIRECTIONS_CACHE_SECONDS:
        return None
    return cached


def _naver_directions_cache_write(cache_key, now, routes):
    try:
        cache_fs = _naver_directions_cache_fs()
        filename = hashlib.sha256(cache_key.encode("utf-8")).hexdigest() + ".json"
        cache_fs.write.json(filename, dict(saved_at=now, routes=routes))
        files = cache_fs.files()
        if len(files) > _NAVER_DIRECTIONS_CACHE_LIMIT:
            for stale in sorted(files)[:len(files) - _NAVER_DIRECTIONS_CACHE_LIMIT]:
                cache_fs.delete(stale)
    except Exception:
        pass


def _naver_route_payload(data):
    if not isinstance(data, dict) or int(data.get("code", -1)) != 0:
        return []

    route_groups = data.get("route") if isinstance(data.get("route"), dict) else {}
    rows = []
    for option in ("traoptimal", "trafast", "tracomfort"):
        candidates = route_groups.get(option) if isinstance(route_groups.get(option), list) else []
        if not candidates:
            continue
        item = candidates[0] if isinstance(candidates[0], dict) else {}
        summary = item.get("summary") if isinstance(item.get("summary"), dict) else {}
        path = item.get("path") if isinstance(item.get("path"), list) else []
        if not path or summary.get("distance") is None or summary.get("duration") is None:
            continue
        rows.append(dict(
            option=option,
            path=path,
            distance=int(summary.get("distance") or 0),
            duration=int(summary.get("duration") or 0),
            toll_fare=int(summary.get("tollFare") or 0),
            taxi_fare=int(summary.get("taxiFare") or 0),
            fuel_price=int(summary.get("fuelPrice") or 0),
            guides=item.get("guide") if isinstance(item.get("guide"), list) else [],
        ))
    return rows


def naver_directions():
    start_lat = _naver_coordinate(wiz.request.query("start_lat", ""), 30, 44)
    start_lng = _naver_coordinate(wiz.request.query("start_lng", ""), 120, 135)
    goal_lat = _naver_coordinate(wiz.request.query("goal_lat", ""), 30, 44)
    goal_lng = _naver_coordinate(wiz.request.query("goal_lng", ""), 120, 135)
    if None in (start_lat, start_lng, goal_lat, goal_lng):
        wiz.response.status(400, message="유효한 국내 출발지와 목적지 좌표가 필요합니다.")
        return

    client_id = _project_env_value("NAVER_MAPS_CLIENT_ID", "NCP_MAPS_CLIENT_ID")
    client_secret = _project_env_value("NAVER_MAPS_CLIENT_SECRET", "NCP_MAPS_CLIENT_SECRET")
    if not client_id or not client_secret:
        wiz.response.status(503, message="네이버 지도 서버 인증 정보가 설정되지 않았습니다.")
        return

    cache_key = ":".join(str(round(value, 5)) for value in (start_lat, start_lng, goal_lat, goal_lng))
    now = time.time()
    cached = _naver_directions_cache_read(cache_key, now)
    if cached and now - cached.get("saved_at", 0) < _NAVER_DIRECTIONS_CACHE_SECONDS:
        wiz.response.status(200, routes=cached.get("routes", []), cache="hit")
        return

    query = urllib.parse.urlencode(dict(
        start=f"{start_lng},{start_lat}",
        goal=f"{goal_lng},{goal_lat}",
        option="traoptimal:trafast:tracomfort",
        lang="ko",
    ))
    url = f"https://maps.apigw.ntruss.com/map-direction/v1/driving?{query}"
    request = urllib.request.Request(url, headers={
        "x-ncp-apigw-api-key-id": client_id,
        "x-ncp-apigw-api-key": client_secret,
        "Accept": "application/json",
    })
    payload = None
    error_message = ""
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        error_message = f"네이버 길찾기 API가 HTTP {error.code} 오류를 반환했습니다."
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
        error_message = "네이버 길찾기 API 응답을 확인하지 못했습니다."

    if error_message:
        wiz.response.status(502, message=error_message)
        return

    routes = _naver_route_payload(payload)
    if not routes:
        message = str((payload or {}).get("message") or "자동차 경로를 찾지 못했습니다.")
        wiz.response.status(404, message=message)
        return

    _naver_directions_cache_write(cache_key, now, routes)
    wiz.response.status(200, routes=routes, cache="miss")


def _odsay_transit_cache_fs():
    root = wiz.project.fs("data")
    if not root.exists("odsay-transit-cache"):
        root.makedirs("odsay-transit-cache")
    return wiz.project.fs("data", "odsay-transit-cache")


def _odsay_transit_cache_read(cache_key, now):
    try:
        cache_fs = _odsay_transit_cache_fs()
        filename = hashlib.sha256(cache_key.encode("utf-8")).hexdigest() + ".json"
        cached = cache_fs.read.json(filename, default={})
    except Exception:
        return None
    if not isinstance(cached, dict) or now - float(cached.get("saved_at", 0)) >= _ODSAY_TRANSIT_CACHE_SECONDS:
        return None
    return cached


def _odsay_transit_cache_write(cache_key, now, routes):
    try:
        cache_fs = _odsay_transit_cache_fs()
        filename = hashlib.sha256(cache_key.encode("utf-8")).hexdigest() + ".json"
        cache_fs.write.json(filename, dict(saved_at=now, routes=routes))
        files = cache_fs.files()
        if len(files) > _ODSAY_TRANSIT_CACHE_LIMIT:
            for stale in sorted(files)[:len(files) - _ODSAY_TRANSIT_CACHE_LIMIT]:
                cache_fs.delete(stale)
    except Exception:
        pass


def _odsay_number(value, fallback=0):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return number if math.isfinite(number) else fallback


def _odsay_path_point(source, x_key="x", y_key="y"):
    if not isinstance(source, dict):
        return None
    lng = _odsay_number(source.get(x_key), None)
    lat = _odsay_number(source.get(y_key), None)
    if lng is None or lat is None or not (120 <= lng <= 135 and 30 <= lat <= 44):
        return None
    return dict(lat=lat, lng=lng)


def _odsay_append_path_point(path, point):
    if not point:
        return
    if path and abs(path[-1]["lat"] - point["lat"]) < 0.000001 and abs(path[-1]["lng"] - point["lng"]) < 0.000001:
        return
    path.append(point)


def _odsay_transit_payload(data):
    result = data.get("result") if isinstance(data, dict) and isinstance(data.get("result"), dict) else {}
    paths = result.get("path") if isinstance(result.get("path"), list) else []
    routes = []
    for path_index, raw_path in enumerate(paths[:3]):
        if not isinstance(raw_path, dict):
            continue
        info = raw_path.get("info") if isinstance(raw_path.get("info"), dict) else {}
        sub_paths = raw_path.get("subPath") if isinstance(raw_path.get("subPath"), list) else []
        steps = []
        route_path = []
        transport_step_count = 0
        line_labels = []
        for raw_step in sub_paths:
            if not isinstance(raw_step, dict):
                continue
            traffic_type = int(_odsay_number(raw_step.get("trafficType"), 3))
            lanes = raw_step.get("lane") if isinstance(raw_step.get("lane"), list) else []
            normalized_lanes = []
            for lane in lanes:
                if not isinstance(lane, dict):
                    continue
                line_name = str(lane.get("busNo") or lane.get("name") or lane.get("trainName") or "").strip()
                if line_name and line_name not in line_labels:
                    line_labels.append(line_name)
                normalized_lanes.append(dict(
                    name=line_name,
                    bus_no=str(lane.get("busNo") or "").strip(),
                    type=int(_odsay_number(lane.get("type"), 0)),
                    bus_id=str(lane.get("busID") or "").strip(),
                    subway_code=int(_odsay_number(lane.get("subwayCode"), 0)),
                ))
            if traffic_type != 3:
                transport_step_count += 1
            start_name = str(raw_step.get("startName") or raw_step.get("startStation") or "").strip()
            end_name = str(raw_step.get("endName") or raw_step.get("endStation") or "").strip()
            steps.append(dict(
                traffic_type=traffic_type,
                distance=int(round(_odsay_number(raw_step.get("distance"), 0))),
                duration=int(round(_odsay_number(raw_step.get("sectionTime"), 0))),
                station_count=int(round(_odsay_number(raw_step.get("stationCount"), 0))),
                start_name=start_name,
                end_name=end_name,
                direction=str(raw_step.get("way") or raw_step.get("direction") or "").strip(),
                lanes=normalized_lanes,
            ))
            _odsay_append_path_point(route_path, _odsay_path_point(raw_step, "startX", "startY"))
            pass_stops = raw_step.get("passStopList") if isinstance(raw_step.get("passStopList"), dict) else {}
            stations = pass_stops.get("stations") if isinstance(pass_stops.get("stations"), list) else []
            for station in stations:
                _odsay_append_path_point(route_path, _odsay_path_point(station))
            _odsay_append_path_point(route_path, _odsay_path_point(raw_step, "endX", "endY"))

        total_time = int(round(_odsay_number(info.get("totalTime"), 0)))
        total_distance = int(round(_odsay_number(info.get("totalDistance"), 0)))
        if not steps or total_time <= 0:
            continue
        routes.append(dict(
            provider="odsay",
            index=path_index,
            path_type=int(_odsay_number(raw_path.get("pathType"), 0)),
            total_time=total_time,
            total_distance=total_distance,
            total_walk=int(round(_odsay_number(info.get("totalWalk"), 0))),
            payment=int(round(_odsay_number(info.get("payment"), 0))),
            transfer_count=max(0, transport_step_count - 1),
            first_start_station=str(info.get("firstStartStation") or "").strip(),
            last_end_station=str(info.get("lastEndStation") or "").strip(),
            line_labels=line_labels,
            steps=steps,
            path=route_path,
        ))
    return routes


def odsay_transit_routes():
    start_lat = _naver_coordinate(wiz.request.query("start_lat", ""), 30, 44)
    start_lng = _naver_coordinate(wiz.request.query("start_lng", ""), 120, 135)
    goal_lat = _naver_coordinate(wiz.request.query("goal_lat", ""), 30, 44)
    goal_lng = _naver_coordinate(wiz.request.query("goal_lng", ""), 120, 135)
    if None in (start_lat, start_lng, goal_lat, goal_lng):
        wiz.response.status(400, message="유효한 국내 출발지와 목적지 좌표가 필요합니다.")
        return

    api_key = _project_env_value("ODSAY_API_KEY")
    if not api_key:
        wiz.response.status(
            503,
            message="무료 대중교통 API 키가 설정되지 않았습니다.",
            provider="odsay",
            configured=False,
        )
        return

    cache_key = ":".join(str(round(value, 5)) for value in (start_lat, start_lng, goal_lat, goal_lng))
    now = time.time()
    cached = _odsay_transit_cache_read(cache_key, now)
    if cached:
        wiz.response.status(200, routes=cached.get("routes", []), provider="odsay", cache="hit")
        return

    query = urllib.parse.urlencode(dict(
        SX=start_lng,
        SY=start_lat,
        EX=goal_lng,
        EY=goal_lat,
        OPT=0,
        SearchType=0,
        SearchPathType=0,
        apiKey=api_key,
    ))
    request = urllib.request.Request(
        "https://api.odsay.com/v1/api/searchPubTransPathT?{}".format(query),
        headers={
            "Accept": "application/json",
            "User-Agent": "GACHI-Travel/1.0",
            "Origin": "https://travel.wizide.com",
            "Referer": "https://travel.wizide.com/",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        wiz.response.status(502, message="대중교통 API가 HTTP {} 오류를 반환했습니다.".format(error.code))
        return
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
        wiz.response.status(502, message="대중교통 API 응답을 확인하지 못했습니다.")
        return

    routes = _odsay_transit_payload(payload)
    if not routes:
        error = payload.get("error") if isinstance(payload, dict) and isinstance(payload.get("error"), dict) else {}
        message = str(error.get("msg") or error.get("message") or "대중교통 경로를 찾지 못했습니다.")
        wiz.response.status(404, message=message, provider="odsay", configured=True)
        return

    _odsay_transit_cache_write(cache_key, now, routes)
    wiz.response.status(200, routes=routes, provider="odsay", cache="miss")


def _walking_route_cache_fs():
    root = wiz.project.fs("data")
    if not root.exists("walking-route-cache"):
        root.makedirs("walking-route-cache")
    return wiz.project.fs("data", "walking-route-cache")


def _walking_route_cache_read(cache_key, now):
    try:
        cache_fs = _walking_route_cache_fs()
        filename = hashlib.sha256(cache_key.encode("utf-8")).hexdigest() + ".json"
        cached = cache_fs.read.json(filename, default={})
    except Exception:
        return None
    if not isinstance(cached, dict) or now - float(cached.get("saved_at", 0)) >= _WALKING_ROUTE_CACHE_SECONDS:
        return None
    return cached


def _walking_route_cache_write(cache_key, now, routes):
    try:
        cache_fs = _walking_route_cache_fs()
        filename = hashlib.sha256(cache_key.encode("utf-8")).hexdigest() + ".json"
        cache_fs.write.json(filename, dict(saved_at=now, routes=routes))
        files = cache_fs.files()
        if len(files) > _WALKING_ROUTE_CACHE_LIMIT:
            for stale in sorted(files)[:len(files) - _WALKING_ROUTE_CACHE_LIMIT]:
                cache_fs.delete(stale)
    except Exception:
        pass


def _walking_route_usage_fs():
    root = wiz.project.fs("data")
    if not root.exists("walking-route-usage"):
        root.makedirs("walking-route-usage")
    return wiz.project.fs("data", "walking-route-usage")


def _walking_route_daily_limit():
    raw = _project_env_value("OPENROUTESERVICE_DAILY_LIMIT")
    try:
        requested = int(raw) if raw else _OPENROUTESERVICE_SAFE_DAILY_LIMIT
    except (TypeError, ValueError):
        requested = _OPENROUTESERVICE_SAFE_DAILY_LIMIT
    return max(1, min(_OPENROUTESERVICE_SAFE_DAILY_LIMIT, requested))


def _consume_openrouteservice_free_request(now):
    try:
        usage_fs = _walking_route_usage_fs()
        day = datetime.datetime.utcfromtimestamp(now).strftime("%Y-%m-%d")
        filename = "openrouteservice-{}.json".format(day)
        usage = usage_fs.read.json(filename, default={})
        count = int(usage.get("count", 0)) if isinstance(usage, dict) else 0
        limit = _walking_route_daily_limit()
        if count >= limit:
            return False, count, limit
        usage_fs.write.json(filename, dict(day=day, count=count + 1, updated_at=now, limit=limit))
        return True, count + 1, limit
    except Exception:
        # 사용량 저장소를 확인하지 못하면 과금 방지를 위해 유료 전환 가능성이 없는 OSM 대체 경로만 사용합니다.
        return False, 0, _walking_route_daily_limit()


def _consume_osm_foot_router_request(now):
    try:
        usage_fs = _walking_route_usage_fs()
        state = usage_fs.read.json("osm-foot-router.json", default={})
        last_request_at = float(state.get("last_request_at", 0)) if isinstance(state, dict) else 0
        if now - last_request_at < _OSM_FOOT_ROUTER_MIN_INTERVAL_SECONDS:
            return False
        usage_fs.write.json("osm-foot-router.json", dict(last_request_at=now))
        return True
    except Exception:
        return False


def _walking_path(points):
    path = []
    for point in points if isinstance(points, list) else []:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue
        lng = _naver_coordinate(point[0], 120, 135)
        lat = _naver_coordinate(point[1], 30, 44)
        if lat is None or lng is None:
            continue
        path.append(dict(lat=lat, lng=lng))
    return path


def _walking_instruction(maneuver_type, modifier, name, provider_step_type=None):
    road = str(name or "보행로").strip()
    maneuver_type = str(maneuver_type or "").strip().lower()
    modifier = str(modifier or "").strip().lower()
    ors_type = int(provider_step_type) if isinstance(provider_step_type, (int, float)) else None
    if maneuver_type == "depart" or ors_type == 11:
        return "{} 방면으로 출발".format(road)
    if maneuver_type == "arrive" or ors_type == 10:
        return "목적지에 도착"
    if maneuver_type in ("roundabout", "rotary") or ors_type in (7, 8):
        return "회전교차로에서 {} 방면으로 이동".format(road)
    if maneuver_type == "uturn" or modifier == "uturn" or ors_type == 9:
        return "유턴 후 {} 방면으로 이동".format(road)
    if modifier in ("left", "sharp left") or ors_type in (0, 2):
        return "좌회전 후 {} 방면으로 이동".format(road)
    if modifier == "slight left" or ors_type in (4, 12):
        return "왼쪽 방향 {} 방면으로 이동".format(road)
    if modifier in ("right", "sharp right") or ors_type in (1, 3):
        return "우회전 후 {} 방면으로 이동".format(road)
    if modifier == "slight right" or ors_type in (5, 13):
        return "오른쪽 방향 {} 방면으로 이동".format(road)
    return "{} 방면으로 직진".format(road)


def _openrouteservice_walking_payload(data):
    features = data.get("features") if isinstance(data, dict) and isinstance(data.get("features"), list) else []
    if not features or not isinstance(features[0], dict):
        return []
    feature = features[0]
    geometry = feature.get("geometry") if isinstance(feature.get("geometry"), dict) else {}
    properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    summary = properties.get("summary") if isinstance(properties.get("summary"), dict) else {}
    path = _walking_path(geometry.get("coordinates"))
    steps = []
    segments = properties.get("segments") if isinstance(properties.get("segments"), list) else []
    for segment in segments:
        raw_steps = segment.get("steps") if isinstance(segment, dict) and isinstance(segment.get("steps"), list) else []
        for step in raw_steps:
            if not isinstance(step, dict):
                continue
            step_type = step.get("type")
            name = str(step.get("name") or "보행로").strip()
            steps.append(dict(
                instruction=_walking_instruction("", "", name, step_type),
                distance=max(0, int(round(float(step.get("distance") or 0)))),
                duration_seconds=max(0, int(round(float(step.get("duration") or 0)))),
                name=name,
                maneuver_type="ors-{}".format(step_type),
            ))
    if len(path) < 2:
        return []
    duration_seconds = max(0, int(round(float(summary.get("duration") or 0))))
    total_distance = max(0, int(round(float(summary.get("distance") or 0))))
    return [dict(
        provider="openrouteservice",
        total_time=max(1, int(math.ceil(duration_seconds / 60.0))),
        duration_seconds=duration_seconds,
        total_distance=total_distance,
        path=path,
        steps=steps,
    )]


def _osm_foot_walking_payload(data):
    raw_routes = data.get("routes") if isinstance(data, dict) and isinstance(data.get("routes"), list) else []
    if not raw_routes or not isinstance(raw_routes[0], dict):
        return []
    raw_route = raw_routes[0]
    geometry = raw_route.get("geometry") if isinstance(raw_route.get("geometry"), dict) else {}
    path = _walking_path(geometry.get("coordinates"))
    steps = []
    for leg in raw_route.get("legs") if isinstance(raw_route.get("legs"), list) else []:
        for step in leg.get("steps") if isinstance(leg, dict) and isinstance(leg.get("steps"), list) else []:
            if not isinstance(step, dict):
                continue
            maneuver = step.get("maneuver") if isinstance(step.get("maneuver"), dict) else {}
            name = str(step.get("name") or "보행로").strip()
            maneuver_type = str(maneuver.get("type") or "").strip()
            modifier = str(maneuver.get("modifier") or "").strip()
            steps.append(dict(
                instruction=_walking_instruction(maneuver_type, modifier, name),
                distance=max(0, int(round(float(step.get("distance") or 0)))),
                duration_seconds=max(0, int(round(float(step.get("duration") or 0)))),
                name=name,
                maneuver_type=maneuver_type,
                maneuver_modifier=modifier,
            ))
    if len(path) < 2:
        return []
    duration_seconds = max(0, int(round(float(raw_route.get("duration") or 0))))
    total_distance = max(0, int(round(float(raw_route.get("distance") or 0))))
    return [dict(
        provider="openstreetmap",
        total_time=max(1, int(math.ceil(duration_seconds / 60.0))),
        duration_seconds=duration_seconds,
        total_distance=total_distance,
        path=path,
        steps=steps,
    )]


def _request_openrouteservice_walking(api_key, start_lat, start_lng, goal_lat, goal_lng):
    body = json.dumps(dict(
        coordinates=[[start_lng, start_lat], [goal_lng, goal_lat]],
        instructions=True,
        language="en",
        elevation=False,
    )).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openrouteservice.org/v2/directions/foot-walking/geojson",
        data=body,
        headers={
            "Authorization": api_key,
            "Accept": "application/json, application/geo+json",
            "Content-Type": "application/json",
            "User-Agent": "GACHI-Travel/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return _openrouteservice_walking_payload(json.loads(response.read().decode("utf-8")))


def _request_osm_foot_walking(start_lat, start_lng, goal_lat, goal_lng):
    coordinates = "{},{};{},{}".format(start_lng, start_lat, goal_lng, goal_lat)
    query = urllib.parse.urlencode(dict(overview="full", geometries="geojson", steps="true"))
    request = urllib.request.Request(
        "https://routing.openstreetmap.de/routed-foot/route/v1/driving/{}?{}".format(coordinates, query),
        headers={
            "Accept": "application/json",
            "User-Agent": "GACHI-Travel/1.0 (https://travel.wizide.com)",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        return _osm_foot_walking_payload(json.loads(response.read().decode("utf-8")))


def free_walking_routes():
    start_lat = _naver_coordinate(wiz.request.query("start_lat", ""), 30, 44)
    start_lng = _naver_coordinate(wiz.request.query("start_lng", ""), 120, 135)
    goal_lat = _naver_coordinate(wiz.request.query("goal_lat", ""), 30, 44)
    goal_lng = _naver_coordinate(wiz.request.query("goal_lng", ""), 120, 135)
    if None in (start_lat, start_lng, goal_lat, goal_lng):
        wiz.response.status(400, message="유효한 국내 출발지와 목적지 좌표가 필요합니다.")
        return

    now = time.time()
    coordinate_key = ":".join(str(round(value, 5)) for value in (start_lat, start_lng, goal_lat, goal_lng))
    api_key = _project_env_value("OPENROUTESERVICE_API_KEY", "ORS_API_KEY")
    providers = ["openrouteservice", "openstreetmap"] if api_key else ["openstreetmap"]
    free_limit_protected = False
    last_error = ""

    for provider in providers:
        cache_key = "{}:{}".format(provider, coordinate_key)
        cached = _walking_route_cache_read(cache_key, now)
        if cached:
            wiz.response.status(
                200,
                routes=cached.get("routes", []),
                provider=provider,
                free_only=True,
                cache="hit",
            )
            return

        try:
            if provider == "openrouteservice":
                allowed, _, _ = _consume_openrouteservice_free_request(now)
                if not allowed:
                    free_limit_protected = True
                    continue
                routes = _request_openrouteservice_walking(api_key, start_lat, start_lng, goal_lat, goal_lng)
            else:
                if not _consume_osm_foot_router_request(now):
                    last_error = "무료 보행 경로 서버 호출 간격을 보호하고 있습니다. 잠시 후 다시 시도해주세요."
                    continue
                routes = _request_osm_foot_walking(start_lat, start_lng, goal_lat, goal_lng)
        except urllib.error.HTTPError as error:
            last_error = "무료 보행 경로 서버가 HTTP {} 오류를 반환했습니다.".format(error.code)
            continue
        except (urllib.error.URLError, TimeoutError, ValueError, TypeError, json.JSONDecodeError):
            last_error = "무료 보행 경로 서버 응답을 확인하지 못했습니다."
            continue

        if routes:
            _walking_route_cache_write(cache_key, now, routes)
            wiz.response.status(
                200,
                routes=routes,
                provider=provider,
                free_only=True,
                free_limit_protected=free_limit_protected,
                cache="miss",
            )
            return
        last_error = "실제 보행로 경로를 찾지 못했습니다."

    wiz.response.status(
        503,
        routes=[],
        provider="free-walking",
        free_only=True,
        free_limit_protected=free_limit_protected,
        message=last_error or "무료 보행 경로를 잠시 사용할 수 없습니다.",
    )


def _naver_place_entities(source, prefix):
    rows = []
    decoder = json.JSONDecoder()
    pattern = re.compile(r'"' + re.escape(prefix) + r'([^"\\]+)":')
    for match in pattern.finditer(source):
        start = source.find("{", match.end())
        if start < 0:
            continue
        try:
            payload, _ = decoder.raw_decode(source[start:])
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            rows.append((match.group(1), payload))
    return rows


def _naver_place_name_key(value):
    value = re.sub(r"<[^>]+>", "", str(value or ""))
    return re.sub(r"[^0-9a-zA-Z가-힣]", "", value).lower()


def _naver_place_plain_text(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", str(value or ""))).strip()


def _naver_place_distance_km(origin_lat, origin_lng, target_lat, target_lng):
    if None in (origin_lat, origin_lng, target_lat, target_lng):
        return None
    radius = 6371.0088
    lat1 = math.radians(origin_lat)
    lat2 = math.radians(target_lat)
    delta_lat = lat2 - lat1
    delta_lng = math.radians(target_lng - origin_lng)
    haversine = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lng / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(haversine), math.sqrt(max(0, 1 - haversine)))


def _naver_place_search_rows(source, query):
    rows = []
    seen = set()
    for place_id, payload in _naver_place_entities(source, "PlaceListBusinessesItem:"):
        name = _naver_place_plain_text(payload.get("normalizedName") or payload.get("name"))
        lat = _naver_coordinate(payload.get("y"), 30, 44)
        lng = _naver_coordinate(payload.get("x"), 120, 135)
        if not name or lat is None or lng is None or place_id in seen:
            continue
        seen.add(place_id)
        road_address = _naver_place_plain_text(payload.get("roadAddress"))
        full_address = _naver_place_plain_text(payload.get("fullAddress"))
        parcel_address = _naver_place_plain_text(payload.get("address"))
        common_address = _naver_place_plain_text(payload.get("commonAddress"))
        rows.append(dict(
            id=f"naver-place-{place_id}",
            place_id=place_id,
            name=name,
            title=name,
            category=_naver_place_plain_text(payload.get("category")) or "장소",
            area=common_address,
            location=common_address,
            address=road_address or full_address or parcel_address or common_address,
            road_address=road_address,
            lat=lat,
            lng=lng,
            image=_naver_place_plain_text(payload.get("imageUrl")),
            search_query=query,
            source="naver_search",
            icon="fa-location-dot",
        ))
    return rows


def _naver_place_search_results(query, lat="", lng="", requested_limit=8):
    if len(query) < 2:
        return []

    try:
        limit = max(1, min(10, int(requested_limit)))
    except (TypeError, ValueError):
        limit = 8
    origin_lat = _naver_coordinate(lat, 30, 44)
    origin_lng = _naver_coordinate(lng, 120, 135)
    cache_key = _naver_place_name_key(query)
    cached = _NAVER_PLACE_SEARCH_CACHE.get(cache_key)
    rows = None
    if cached and time.time() - cached.get("saved_at", 0) < _NAVER_PLACE_SEARCH_CACHE_SECONDS:
        rows = cached.get("rows", [])

    if rows is None:
        try:
            url = "https://search.naver.com/search.naver?" + urllib.parse.urlencode({"query": query})
            request = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept-Language": "ko-KR,ko;q=0.9",
            })
            with urllib.request.urlopen(request, timeout=8) as response:
                source = response.read(8 * 1024 * 1024).decode("utf-8", errors="ignore")
            rows = _naver_place_search_rows(source, query)
            _NAVER_PLACE_SEARCH_CACHE[cache_key] = dict(saved_at=time.time(), rows=rows)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
            return []

    query_key = _naver_place_name_key(query)
    ranked_rows = []
    for index, item in enumerate(rows):
        row = dict(item)
        name_key = _naver_place_name_key(row.get("name"))
        if name_key == query_key:
            relevance = 0
        elif name_key.startswith(query_key) or query_key.startswith(name_key):
            relevance = 1
        elif query_key in name_key:
            relevance = 2
        else:
            relevance = 3
        distance = _naver_place_distance_km(origin_lat, origin_lng, row.get("lat"), row.get("lng"))
        row["distance_km"] = round(distance, 3) if distance is not None else None
        ranked_rows.append((relevance, distance if distance is not None else float("inf"), index, row))
    ranked_rows.sort(key=lambda item: (item[0], item[1], item[2]))
    return [item[3] for item in ranked_rows[:limit]]


def _naver_menu_price(value):
    raw = str(value or "").strip()
    if not raw:
        return "가격 정보 없음"
    digits = re.sub(r"[^0-9]", "", raw)
    if digits and re.fullmatch(r"[0-9,원₩ ]+", raw):
        return f"{int(digits):,}원"
    return raw


def naver_place_menu():
    name = wiz.request.query("name", "").strip()[:120]
    address = wiz.request.query("address", "").strip()[:180]
    if not name:
        wiz.response.status(400, message="장소명이 필요합니다.")
        return

    cache_key = _naver_place_name_key(f"{name}|{address}")
    cached = _NAVER_MENU_CACHE.get(cache_key)
    if cached and time.time() - cached.get("saved_at", 0) < _NAVER_MENU_CACHE_SECONDS:
        wiz.response.status(200, **cached.get("data", {}))
        return

    region_match = re.search(
        r"(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)",
        address,
    )
    region = region_match.group(1) if region_match else ""
    queries = [" ".join(value for value in (name, region) if value), name]
    source = ""
    try:
        for query in dict.fromkeys(queries):
            url = "https://search.naver.com/search.naver?" + urllib.parse.urlencode({"query": query})
            request = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept-Language": "ko-KR,ko;q=0.9",
            })
            with urllib.request.urlopen(request, timeout=8) as response:
                source = response.read(8 * 1024 * 1024).decode("utf-8", errors="ignore")
            if '"Menu:' in source:
                break
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
        wiz.response.status(200, menus=[], source="naver_place", message="네이버 메뉴 정보를 불러오지 못했습니다.")
        return

    target_key = _naver_place_name_key(name)
    place_id = ""
    place_name = name
    candidates = _naver_place_entities(source, "PlaceDetailBase:")
    for candidate_id, payload in candidates:
        candidate_name = str(payload.get("name") or "").strip()
        candidate_key = _naver_place_name_key(candidate_name)
        if candidate_key and (candidate_key == target_key or candidate_key in target_key or target_key in candidate_key):
            place_id = candidate_id
            place_name = candidate_name or name
            break

    menu_entities = _naver_place_entities(source, "Menu:")
    if not place_id and menu_entities:
        place_id = menu_entities[0][0].split("_", 1)[0]

    menus = []
    seen = set()
    for entity_id, payload in menu_entities:
        if place_id and not entity_id.startswith(f"{place_id}_"):
            continue
        menu_name = str(payload.get("name") or "").strip()
        if not menu_name:
            continue
        menu_key = _naver_place_name_key(menu_name)
        if not menu_key or menu_key in seen:
            continue
        seen.add(menu_key)
        images = payload.get("images") if isinstance(payload.get("images"), list) else []
        menus.append(dict(
            name=menu_name,
            price=_naver_menu_price(payload.get("price")),
            description=str(payload.get("description") or "").strip(),
            image=str(images[0] if images else "").strip(),
            recommended=bool(payload.get("recommend")),
            index=int(payload.get("index") or len(menus)),
        ))
        if len(menus) >= 30:
            break
    menus.sort(key=lambda item: item.get("index", 0))

    data = dict(menus=menus, source="naver_place", place_id=place_id, place_name=place_name)
    _NAVER_MENU_CACHE[cache_key] = dict(saved_at=time.time(), data=data)
    wiz.response.status(200, **data)


def _persist_course_places(data):
    places = data.get("places", [])
    if not isinstance(places, list):
        return data

    place_db = struct.place.db("place")
    now = datetime.datetime.now()
    normalized = []
    for item in places:
        if not isinstance(item, dict):
            normalized.append(item)
            continue

        google_place_id = str(item.get("google_place_id") or "").strip()[:128]
        requested_place_id = str(item.get("place_id") or item.get("id") or "").strip()
        current = place_db.get(google_place_id=google_place_id) if google_place_id else None
        if current is None and requested_place_id and len(requested_place_id) <= 32:
            current = place_db.get(id=requested_place_id)
        if current is not None:
            place_id = current.get("id")
        elif google_place_id:
            place_id = hashlib.md5(f"google:{google_place_id}".encode("utf-8")).hexdigest()
        elif item.get("name"):
            identity = f"builder:{requested_place_id}:{item.get('name', '')}:{item.get('latitude', '')}:{item.get('longitude', '')}"
            place_id = requested_place_id if requested_place_id and len(requested_place_id) <= 32 else hashlib.md5(identity.encode("utf-8")).hexdigest()
        else:
            normalized.append(item)
            continue

        payload = dict(
            id=place_id,
            google_place_id=google_place_id or (current.get("google_place_id", "") if current else ""),
            name=str(item.get("name") or (current.get("name") if current else "") or "여행 장소").strip()[:200],
            category=str(item.get("category") or (current.get("category") if current else "") or "여행지").strip()[:80],
            image=str(item.get("image") or (current.get("image") if current else "") or "").strip()[:500],
            address=str(item.get("address") or (current.get("address") if current else "") or "").strip()[:300],
            area=str(item.get("area") or (current.get("area") if current else "") or "").strip()[:100],
            latitude=str(item.get("latitude") or (current.get("latitude") if current else "") or "").strip()[:40],
            longitude=str(item.get("longitude") or (current.get("longitude") if current else "") or "").strip()[:40],
            google_rating=_safe_float(item.get("rating"), current.get("google_rating") if current else None),
            is_hidden=False,
            updated=now,
        )
        if current:
            place_db.update(payload, id=place_id)
        else:
            payload["created"] = now
            place_db.insert(payload)

        saved = dict(item)
        saved["place_id"] = place_id
        normalized.append(saved)

    result = dict(data)
    result["places"] = normalized
    return result


def create_builder_course():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    data = _json_loads(wiz.request.query("data", "{}"), {})
    if not isinstance(data, dict):
        wiz.response.status(400, message="코스 정보가 없습니다.")
        return

    data = _persist_course_places(data)
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

    data = _persist_course_places(data)
    data["user_id"] = user_id
    row = struct.course.update(course_id, data)
    if row is None:
        wiz.response.status(404, message="코스를 찾을 수 없습니다.")
        return

    wiz.response.status(200, row=row)


def delete_builder_course():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    course_id = wiz.request.query("course_id", "").strip()
    if not course_id:
        wiz.response.status(400, message="코스 정보가 없습니다.")
        return

    current = struct.course.get(course_id, include_places=False)
    saved_db = struct.db("saved_course")
    saved_row = saved_db.get(user_id=user_id, course_id=course_id)
    saved_route = _json_loads(saved_row.get("route_json", "{}"), {}) if saved_row else {}
    owns_current = current is not None and str(current.get("user_id") or "") == str(user_id)
    owns_saved_row = saved_row is not None and str(saved_route.get("source") or "") == "mine"
    if not owns_current and not owns_saved_row:
        wiz.response.status(404, message="삭제할 내 코스를 찾을 수 없습니다.")
        return

    original_deleted = False
    if owns_current:
        try:
            original_deleted = bool(struct.course.delete(course_id))
        except Exception:
            original_deleted = False

    if saved_row is not None:
        saved_db.delete(id=saved_row.get("id"))
    like_row = struct.db("course_like").get(user_id=user_id, course_id=course_id)
    if like_row is not None:
        struct.db("course_like").delete(id=like_row.get("id"))

    wiz.response.status(
        200,
        deleted=True,
        original_deleted=original_deleted,
        course_ids=_saved_course_ids(user_id),
        courses=_saved_course_rows(user_id)
    )


def course_execution_courses():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    _migrate_legacy_owned_courses(user_id)
    client_id = _project_env_value("NAVER_MAPS_CLIENT_ID", "NCP_MAPS_CLIENT_ID")
    wiz.response.status(
        200,
        courses=struct.course.execution_catalog(user_id),
        naver_maps_client_id=client_id,
    )


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


def zenly_meeting_active():
    status, payload = struct.zenly.active_meeting(_current_user())
    wiz.response.status(status, **payload)


def zenly_meeting_messages():
    status, payload = struct.zenly.meeting_messages(
        wiz.request.query("meeting_id", wiz.request.query("meetingId", "")),
        _current_user(),
    )
    wiz.response.status(status, **payload)


def zenly_meeting_message_send():
    status, payload = struct.zenly.send_meeting_message(
        wiz.request.query("meeting_id", wiz.request.query("meetingId", "")),
        wiz.request.query("message", ""),
        _current_user(),
    )
    wiz.response.status(status, **payload)


def zenly_meeting_end():
    status, payload = struct.zenly.end_meeting(
        wiz.request.query("meeting_id", wiz.request.query("meetingId", "")),
        _current_user(),
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
    if community_action == "report":
        report_community_post()
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
    route = _json_loads(_json_query_string("route_json", "{}"), {})
    course = struct.db("course").get(id=course_id)
    is_mine = str(route.get("source") or "") == "mine" or (
        course is not None and str(course.get("user_id") or "") == str(user_id)
    )

    if saved and is_mine:
        if exists is not None and _saved_course_is_mine(exists, user_id):
            db.delete(id=exists["id"])
        if like_exists is not None:
            like_db.delete(id=like_exists["id"])
        wiz.response.status(
            200,
            course_ids=_saved_course_ids(user_id),
            courses=_saved_course_rows(user_id),
            owned_courses=_owned_course_rows(user_id)
        )
        return

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
        wiz.request.query("thread_id", "").strip(),
        wiz.request.query("client_message_id", "").strip(),
        wiz.request.query("travel_state", "{}")
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


def chat_thread_delete():
    user_id = _current_user_id()
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")
        return

    thread_id = wiz.request.query("thread_id", "").strip()
    if not thread_id:
        wiz.response.status(400, message="삭제할 대화를 선택해주세요.")
        return
    if not ai_chat.delete_thread(user_id, thread_id):
        wiz.response.status(404, message="대화 기록을 찾을 수 없습니다.")
        return

    wiz.response.status(200, thread_id=thread_id, deleted=True)
