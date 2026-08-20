import base64
import json
import os
import urllib.parse
import urllib.request


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


def _static_course_map_data(raw_points):
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
    span = max(
        max(point["lat"] for point in points) - min(point["lat"] for point in points),
        max(point["lng"] for point in points) - min(point["lng"] for point in points)
    )
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


kind = wiz.request.query("kind", "").strip()
if kind == "course_static_map":
    status = 200
    message = ""
    image_data_url = ""
    try:
        image_data_url = _static_course_map_data(wiz.request.query("points", "[]"))
    except ValueError:
        status = 400
        message = "지도 좌표가 필요합니다."
    except Exception:
        status = 502
        message = "NAVER 지도 이미지를 불러오지 못했습니다."

    if status != 200:
        wiz.response.status(status, message=message)
    wiz.response.status(200, image_data_url=image_data_url)


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
