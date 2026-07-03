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


struct = wiz.model("struct")

if _method() == "POST":
    row = struct.course.create(_data())
    if row is None:
        wiz.response.status(400, message="코스 제목을 입력해주세요.")
    wiz.response.status(200, row=row)

rows = struct.course.list_admin(
    search=wiz.request.query("search", ""),
    category=wiz.request.query("category", ""),
    visibility=wiz.request.query("visibility", "visible")
)
wiz.response.status(200, rows=rows)
