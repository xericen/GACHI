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


def _row_with_day_metadata(struct, row):
    if not isinstance(row, dict) or not row.get("id") or not isinstance(row.get("places"), list):
        return row
    metadata = {}
    for link in struct.db("course_place").rows(course_id=row.get("id"), orderby="order_index", order="ASC"):
        memo = str(link.get("memo") or "")
        if not memo.startswith("__gachi_item__"):
            continue
        try:
            meta = json.loads(memo[len("__gachi_item__"):])
        except Exception:
            meta = {}
        if isinstance(meta, dict) and link.get("place_id"):
            metadata[str(link.get("place_id"))] = meta
    if not metadata:
        return row
    places = []
    for place in row.get("places", []):
        item = dict(place) if isinstance(place, dict) else {}
        place_id = str(item.get("place_id") or item.get("id") or "")
        meta = metadata.get(place_id, {})
        if meta:
            try:
                day = max(1, int(meta.get("day") or 1))
            except Exception:
                day = 1
            item.update(dict(
                day=day,
                day_label=str(meta.get("day_label") or f"{day}일차"),
                date=str(meta.get("date") or ""),
                item_type=str(meta.get("item_type") or "place"),
                memo=str(meta.get("memo") or item.get("memo") or ""),
            ))
        places.append(item)
    result = dict(row)
    result["places"] = places
    return result


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

row = _row_with_day_metadata(struct, row)

if row is None or (method == "GET" and row.get("is_hidden")):
    wiz.response.status(404, message="코스를 찾을 수 없습니다.")

wiz.response.status(200, row=row)
