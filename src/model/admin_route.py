import json


class AdminRoute:
    def __init__(self):
        self.admin = wiz.model("struct").admin

    def method(self):
        override = wiz.request.query("_method", "")
        if override:
            return override.upper()
        try:
            value = wiz.request.method()
            return value.upper()
        except Exception:
            pass
        try:
            return str(wiz.request.method).upper()
        except Exception:
            pass
        return "GET"

    def data(self):
        raw = wiz.request.query("data", "")
        if raw:
            try:
                return json.loads(raw)
            except Exception:
                return {}
        return dict(wiz.request.query())

    def places(self):
        wiz.response.status(200, rows=self.admin.list_places(
            search=wiz.request.query("search", ""),
            category=wiz.request.query("category", ""),
            visibility=wiz.request.query("visibility", "visible")
        ))

    def place_item(self, place_id):
        if self.method() == "DELETE":
            row = self.admin.hide_place(place_id)
        else:
            row = self.admin.update_place(place_id, self.data())
        if row is None:
            wiz.response.status(404, message="장소를 찾을 수 없습니다.")
            return
        wiz.response.status(200, row=row)

    def courses(self):
        if self.method() == "POST":
            row = self.admin.create_course(self.data())
            if row is None:
                wiz.response.status(400, message="코스 제목을 입력해주세요.")
                return
            wiz.response.status(200, row=row)
            return
        wiz.response.status(200, rows=self.admin.list_courses(
            search=wiz.request.query("search", ""),
            category=wiz.request.query("category", ""),
            visibility=wiz.request.query("visibility", "visible")
        ))

    def course_item(self, course_id):
        method = self.method()
        if method == "DELETE":
            row = self.admin.hide_course(course_id)
        elif method in ["PATCH", "POST"]:
            row = self.admin.update_course(course_id, self.data())
        else:
            row = self.admin.core.course.get(course_id, include_places=True)
        if row is None:
            wiz.response.status(404, message="코스를 찾을 수 없습니다.")
            return
        wiz.response.status(200, row=row)

    def course_featured(self, course_id):
        if self.method() not in ["PATCH", "POST"]:
            wiz.response.status(405, message="지원하지 않는 요청 방식입니다.")
            return
        data = self.data()
        is_featured = data.get("is_featured")
        if is_featured is None:
            is_featured = data.get("featured")
        row = self.admin.toggle_course_featured(course_id, is_featured)
        if row is None:
            wiz.response.status(404, message="코스를 찾을 수 없습니다.")
            return
        wiz.response.status(200, row=row)

    def course_tags(self, course_id):
        tags = self.data().get("tags", [])
        row = self.admin.update_course_tags(course_id, tags)
        if row is None:
            wiz.response.status(404, message="코스를 찾을 수 없습니다.")
            return
        wiz.response.status(200, row=row)

    def stats_overview(self):
        wiz.response.status(200, self.admin.stats_overview())

    def signups(self):
        wiz.response.status(200, self.admin.signup_trend(wiz.request.query("range", "7d")))

    def top_courses(self):
        wiz.response.status(200, self.admin.top_courses(wiz.request.query("limit", 10)))

    def filter_usage(self):
        wiz.response.status(200, self.admin.filter_usage())

    def featured(self):
        if self.method() == "POST":
            row = self.admin.add_featured(self.data())
            if row is None:
                wiz.response.status(400, message="추천 코스로 추가할 코스를 선택해주세요.")
                return
            wiz.response.status(200, row=row)
            return
        wiz.response.status(200, rows=self.admin.list_featured())

    def featured_item(self, featured_id):
        if not self.admin.remove_featured(featured_id):
            wiz.response.status(404, message="추천 항목을 찾을 수 없습니다.")
            return
        wiz.response.status(200)

    def notice(self):
        if self.method() == "POST":
            row = self.admin.create_notice(self.data())
            if row is None:
                wiz.response.status(400, message="공지 제목을 입력해주세요.")
                return
            wiz.response.status(200, row=row)
            return
        wiz.response.status(200, rows=self.admin.notices())

    def terms(self):
        if self.method() in ["PATCH", "POST"]:
            wiz.response.status(200, self.admin.save_terms(self.data()))
            return
        wiz.response.status(200, self.admin.terms())


Model = AdminRoute()
