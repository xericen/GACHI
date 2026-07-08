import json


def _data():
    raw = wiz.request.query("data", "")
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    return dict(wiz.request.query())


segment = wiz.request.match("/api/courses/<id>/checkin")
session = wiz.model("portal/season/session").use()
struct = wiz.model("struct")

raw_user = session.get() or {}
user_id = raw_user.get("id", "")
if not user_id:
    wiz.response.status(401, message="로그인이 필요합니다.")

payload = _data()
place_id = str(payload.get("place_id") or payload.get("placeId") or "").strip()
method = str(payload.get("method") or "manual").strip()
if not place_id:
    wiz.response.status(400, message="체크인할 장소 정보가 필요합니다.")

row = struct.course.checkin(
    course_id=segment.id,
    place_id=place_id,
    user_id=user_id,
    method=method,
    lat=payload.get("lat", ""),
    lng=payload.get("lng", ""),
)
if row is None:
    wiz.response.status(400, message="체크인을 저장하지 못했습니다.")

wiz.response.status(200, checkin=row, execution=struct.course.execution(segment.id, user_id))
