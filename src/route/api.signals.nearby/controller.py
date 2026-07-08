session = wiz.model("portal/season/session").use()
user = session.get() or {}
payload = wiz.model("struct").zenly.nearby_signals(
    lat=wiz.request.query("lat", ""),
    lng=wiz.request.query("lng", ""),
    radius=wiz.request.query("radius", 1500),
    user_id=user.get("id", "")
)
wiz.response.status(200, **payload)
