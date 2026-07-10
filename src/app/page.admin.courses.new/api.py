import json

admin = wiz.model("struct").admin


def _json_query(name="data", default=None):
    default = default if default is not None else {}
    raw = wiz.request.query(name, "")
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


def search_places():
    search = wiz.request.query("search", "")
    wiz.response.status(200, rows=admin.list_places(search=search, visibility="visible"))


def create_course():
    row = admin.create_course(_json_query())
    if row is None:
        wiz.response.status(400, message="코스 제목을 입력해주세요.")
        return
    wiz.response.status(200, row=row)
