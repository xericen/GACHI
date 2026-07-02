import json

struct = wiz.model("struct")
admin = struct.admin
ai_model = wiz.model("ai_chat")


def _json_query(name="data", default=None):
    default = default if default is not None else {}
    raw = wiz.request.query(name, "")
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


def overview():
    wiz.response.status(200, admin.stats_overview())


def signups():
    wiz.response.status(200, admin.signup_trend(wiz.request.query("range", "7d")))


def top_courses():
    wiz.response.status(200, admin.top_courses(wiz.request.query("limit", 10)))


def filter_usage():
    wiz.response.status(200, admin.filter_usage())


def model_settings():
    wiz.response.status(200, ai_model.admin_settings())


def save_model_settings():
    try:
        settings = ai_model.update_admin_settings(_json_query())
    except ValueError as error:
        wiz.response.status(400, message=str(error))
        return
    except Exception:
        wiz.response.status(500, message="AI 모델 설정을 저장하지 못했습니다.")
        return
    wiz.response.status(200, settings)


def users():
    wiz.response.status(200, rows=admin.users(
        search=wiz.request.query("search", ""),
        role=wiz.request.query("role", "")
    ))


def update_user_role():
    row = admin.update_user_role(
        wiz.request.query("id", ""),
        wiz.request.query("role", "user")
    )
    if row is None:
        wiz.response.status(404, message="사용자를 찾을 수 없습니다.")
        return
    wiz.response.status(200, row=row)


def delete_user():
    result = admin.delete_user(wiz.request.query("id", ""))
    if result is None:
        wiz.response.status(404, message="사용자를 찾을 수 없습니다.")
        return
    if result.get("error"):
        wiz.response.status(400, message=result.get("message", "사용자를 삭제할 수 없습니다."))
        return
    wiz.response.status(200)


def places():
    visibility = wiz.request.query("visibility", "visible")
    area = wiz.request.query("area", "")
    summary_only = wiz.request.query("summary_only", "") in ["1", "true", "yes"]
    summary = admin.place_area_summary(visibility=visibility)
    wiz.response.status(200,
        rows=[] if summary_only else admin.list_places(
            search=wiz.request.query("search", ""),
            category=wiz.request.query("category", ""),
            visibility=visibility
        ),
        categories=[] if summary_only else admin.place_categories(),
        area_summary=summary,
        area_detail=admin.place_area_detail(area=area, visibility=visibility) if area else None
    )


def place_area_summary():
    wiz.response.status(200, admin.place_area_summary(
        visibility=wiz.request.query("visibility", "visible")
    ))


def update_place():
    row = admin.update_place(wiz.request.query("id", ""), _json_query())
    if row is None:
        wiz.response.status(404, message="장소를 찾을 수 없습니다.")
        return
    wiz.response.status(200, row=row)


def hide_place():
    row = admin.hide_place(wiz.request.query("id", ""))
    if row is None:
        wiz.response.status(404, message="장소를 찾을 수 없습니다.")
        return
    wiz.response.status(200, row=row)


def courses():
    wiz.response.status(200,
        rows=admin.list_courses(
            search=wiz.request.query("search", ""),
            category=wiz.request.query("category", ""),
            visibility=wiz.request.query("visibility", "visible")
        ),
        categories=admin.course_categories(),
        places=admin.list_places(visibility="visible")
    )


def create_course():
    row = admin.create_course(_json_query())
    if row is None:
        wiz.response.status(400, message="코스 제목을 입력해주세요.")
        return
    wiz.response.status(200, row=row)


def update_course():
    row = admin.update_course(wiz.request.query("id", ""), _json_query())
    if row is None:
        wiz.response.status(404, message="코스를 찾을 수 없습니다.")
        return
    wiz.response.status(200, row=row)


def toggle_course_featured():
    data = _json_query()
    value = data.get("is_featured")
    if value is None:
        value = data.get("featured")
    row = admin.toggle_course_featured(wiz.request.query("id", ""), value)
    if row is None:
        wiz.response.status(404, message="코스를 찾을 수 없습니다.")
        return
    wiz.response.status(200, row=row)


def hide_course():
    row = admin.hide_course(wiz.request.query("id", ""))
    if row is None:
        wiz.response.status(404, message="코스를 찾을 수 없습니다.")
        return
    wiz.response.status(200, row=row)


def update_course_tags():
    row = admin.update_course_tags(wiz.request.query("id", ""), _json_query("tags", []))
    if row is None:
        wiz.response.status(404, message="코스를 찾을 수 없습니다.")
        return
    wiz.response.status(200, row=row)


def search_places():
    wiz.response.status(200, rows=admin.list_places(
        search=wiz.request.query("search", ""),
        visibility="visible"
    ))


def featured():
    wiz.response.status(200, rows=admin.list_featured())


def add_featured():
    row = admin.add_featured(_json_query())
    if row is None:
        wiz.response.status(400, message="추천 코스로 추가할 코스를 선택해주세요.")
        return
    wiz.response.status(200, row=row)


def reorder_featured():
    wiz.response.status(200, rows=admin.reorder_featured(_json_query("items", [])))


def remove_featured():
    if not admin.remove_featured(wiz.request.query("id", "")):
        wiz.response.status(404, message="추천 항목을 찾을 수 없습니다.")
        return
    wiz.response.status(200)


def notices():
    wiz.response.status(200, rows=admin.notices())


def save_notice():
    row = admin.create_notice(_json_query())
    if row is None:
        wiz.response.status(400, message="공지 제목을 입력해주세요.")
        return
    wiz.response.status(200, row=row)


def terms():
    if wiz.request.query("scope", "") == "models":
        wiz.response.status(200, ai_model.admin_settings())
        return
    wiz.response.status(200, admin.terms())


def save_terms():
    if wiz.request.query("scope", "") == "models":
        try:
            settings = ai_model.update_admin_settings(_json_query())
        except ValueError as error:
            wiz.response.status(400, message=str(error))
            return
        except Exception:
            wiz.response.status(500, message="AI 모델 설정을 저장하지 못했습니다.")
            return
        wiz.response.status(200, settings)
        return
    wiz.response.status(200, admin.save_terms(_json_query()))
