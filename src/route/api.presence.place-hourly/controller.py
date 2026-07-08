segment = wiz.request.match("/api/presence/place/<id>/hourly")
hourly = wiz.model("struct").zenly.hourly(segment.id, wiz.request.query("hours", 12))
wiz.response.status(200, hourly=hourly)
