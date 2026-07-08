segment = wiz.request.match("/api/signals/<id>/report")
session = wiz.model("portal/season/session").use()
raw = session.get() or {}
user = wiz.model("struct").user.get(raw.get("id", "")) if raw.get("id") else raw
status, payload = wiz.model("struct").zenly.report_signal(
    segment.id,
    user or {},
    wiz.request.query("reason", "")
)
wiz.response.status(status, **payload)
