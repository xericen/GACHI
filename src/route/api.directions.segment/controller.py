ai_tools = wiz.model("ai_tools")

segment = ai_tools.execute_segment_lookup(dict(
    origin_lat=wiz.request.query("origin_lat", ""),
    origin_lng=wiz.request.query("origin_lng", ""),
    destination_place_id=wiz.request.query("destination_place_id", "").strip(),
    mode=wiz.request.query("mode", "walking").strip(),
))

if segment.get("status") == "not_available":
    wiz.response.status(400, message=segment.get("message", "구간 정보를 계산하지 못했습니다."))
elif segment.get("status") == "not_found":
    wiz.response.status(404, message="도착 장소를 찾을 수 없습니다.")
else:
    wiz.response.status(200, segment=segment)
