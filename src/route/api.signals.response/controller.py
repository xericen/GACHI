segment = wiz.request.match("/api/signals/<id>/responses/<responseId>")
session = wiz.model("portal/season/session").use()
raw = session.get() or {}
user = wiz.model("struct").user.get(raw.get("id", "")) if raw.get("id") else raw
status, payload = wiz.model("struct").zenly.update_response(
    segment.id,
    segment.responseId,
    wiz.request.query("status", ""),
    user or {}
)
wiz.response.status(status, **payload)
