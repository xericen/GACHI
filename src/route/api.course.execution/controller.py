segment = wiz.request.match("/api/courses/<id>/execution")
session = wiz.model("portal/season/session").use()
struct = wiz.model("struct")

raw_user = session.get() or {}
user_id = raw_user.get("id", "")
execution = struct.course.execution(segment.id, user_id)
if execution is None:
    wiz.response.status(404, message="코스를 찾을 수 없습니다.")

wiz.response.status(200, execution=execution)
