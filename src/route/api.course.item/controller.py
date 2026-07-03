import json


def _method():
    override = wiz.request.query("_method", "")
    if override:
        return override.upper()
    try:
        return wiz.request.method().upper()
    except Exception:
        pass
    try:
        return str(wiz.request.method).upper()
    except Exception:
        pass
    return "GET"


def _data():
    raw = wiz.request.query("data", "")
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            return {}
    return dict(wiz.request.query())


segment = wiz.request.match("/api/courses/<id>")
struct = wiz.model("struct")
method = _method()

if segment.id == "popular":
    limit = wiz.request.query("limit", 4)
    rows = struct.course.popular(limit)
    wiz.response.status(200, rows=rows)

if method in ["PATCH", "POST"]:
    row = struct.course.update(segment.id, _data())
else:
    row = struct.course.get(segment.id, include_places=True)

if row is None or (method == "GET" and row.get("is_hidden")):
    wiz.response.status(404, message="코스를 찾을 수 없습니다.")

wiz.response.status(200, row=row)
