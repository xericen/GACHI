struct = wiz.model("struct")
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
else:
    wiz.response.status(200, touched=True)
