import datetime
import json
import re
import bcrypt
import peewee as pw


class Admin:
    def __init__(self, core):
        self.core = core

    def now(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def today(self):
        return datetime.date.today()

    def db(self, name):
        return self.core.db(name)

    def ensure_schema(self):
        self._ensure_user_role_column()
        self._ensure_course_schema()
        self._ensure_admin_user()
        self._backfill_course_places()
        self._ensure_default_featured_courses()
        self._remove_legacy_example_content()

    def _ensure_user_role_column(self):
        try:
            model = self.db("user").orm
            database = model._meta.database
            columns = [column.name for column in database.get_columns(model._meta.table_name)]
            if "role" not in columns:
                database.execute_sql(
                    "ALTER TABLE `user` ADD COLUMN `role` VARCHAR(16) NOT NULL DEFAULT 'user'"
                )
                database.execute_sql("CREATE INDEX `user_role` ON `user` (`role`)")
        except Exception:
            pass

    def _ensure_columns(self, model_name, specs):
        try:
            model = self.db(model_name).orm
            database = model._meta.database
            table = model._meta.table_name
            columns = [column.name for column in database.get_columns(table)]
            for name, ddl in specs:
                if name in columns:
                    continue
                database.execute_sql(f"ALTER TABLE `{table}` ADD COLUMN {ddl}")
        except Exception:
            pass

    def _ensure_course_schema(self):
        self._ensure_columns("course", [
            ("region", "`region` VARCHAR(100) NOT NULL DEFAULT ''"),
            ("user_id", "`user_id` VARCHAR(32) NOT NULL DEFAULT ''"),
            ("companion_type", "`companion_type` VARCHAR(20) NOT NULL DEFAULT ''"),
            ("cover_image", "`cover_image` VARCHAR(500) NOT NULL DEFAULT ''"),
            ("duration_type", "`duration_type` VARCHAR(16) NOT NULL DEFAULT 'hours'"),
            ("duration_value", "`duration_value` VARCHAR(50) NOT NULL DEFAULT ''"),
            ("rating", "`rating` DOUBLE NULL"),
            ("is_featured", "`is_featured` TINYINT(1) NOT NULL DEFAULT 0"),
            ("is_public", "`is_public` TINYINT(1) NOT NULL DEFAULT 1"),
        ])
        self._ensure_columns("course_place", [
            ("visit_time", "`visit_time` VARCHAR(20) NOT NULL DEFAULT ''"),
            ("memo", "`memo` TEXT NULL"),
        ])
        self._ensure_columns("saved_course", [
            ("places_json", "`places_json` LONGTEXT NULL"),
            ("route_json", "`route_json` LONGTEXT NULL"),
        ])
        self._ensure_columns("place", [
            ("first_image2", "`first_image2` VARCHAR(500) NOT NULL DEFAULT ''"),
            ("overview", "`overview` TEXT NULL"),
            ("zipcode", "`zipcode` VARCHAR(20) NOT NULL DEFAULT ''"),
            ("cpyrht_div_cd", "`cpyrht_div_cd` VARCHAR(20) NOT NULL DEFAULT ''"),
            ("ldong_regn_cd", "`ldong_regn_cd` VARCHAR(10) NOT NULL DEFAULT ''"),
            ("ldong_signgu_cd", "`ldong_signgu_cd` VARCHAR(10) NOT NULL DEFAULT ''"),
            ("lcls_systm1", "`lcls_systm1` VARCHAR(20) NOT NULL DEFAULT ''"),
            ("lcls_systm2", "`lcls_systm2` VARCHAR(20) NOT NULL DEFAULT ''"),
            ("lcls_systm3", "`lcls_systm3` VARCHAR(20) NOT NULL DEFAULT ''"),
            ("tourapi_created_time", "`tourapi_created_time` VARCHAR(20) NOT NULL DEFAULT ''"),
            ("tourapi_modified_time", "`tourapi_modified_time` VARCHAR(20) NOT NULL DEFAULT ''"),
            ("usage_time", "`usage_time` TEXT NULL"),
            ("rest_date", "`rest_date` TEXT NULL"),
            ("parking_info", "`parking_info` TEXT NULL"),
            ("infocenter", "`infocenter` VARCHAR(200) NOT NULL DEFAULT ''"),
            ("detail_intro", "`detail_intro` LONGTEXT NULL"),
            ("detail_hydrated_at", "`detail_hydrated_at` VARCHAR(20) NOT NULL DEFAULT ''"),
            ("detail_hydrate_error", "`detail_hydrate_error` TEXT NULL"),
            ("google_place_id", "`google_place_id` VARCHAR(128) NOT NULL DEFAULT ''"),
            ("google_rating", "`google_rating` DOUBLE NULL"),
            ("google_user_ratings_total", "`google_user_ratings_total` INT NOT NULL DEFAULT 0"),
            ("google_rating_cached_at", "`google_rating_cached_at` VARCHAR(20) NOT NULL DEFAULT ''"),
        ])

    def _backfill_course_places(self):
        try:
            rows = self.db("course").rows(orderby="display_order,created", order="ASC")
            for course in rows:
                course_id = course.get("id")
                if not course_id or self.db("course_place").count(course_id=course_id):
                    continue
                for index, place_id in enumerate(self._load_list(course.get("place_ids")), start=1):
                    if not place_id:
                        continue
                    self.db("course_place").insert(dict(
                        course_id=course_id,
                        place_id=place_id,
                        order_index=index,
                        created=self.now()
                    ))
        except Exception:
            pass

    def _ensure_default_featured_courses(self):
        try:
            if self.db("course").count(is_featured=True):
                return
            featured_rows = self.db("featured_course").rows()
            if featured_rows:
                for row in featured_rows:
                    course_id = row.get("course_id")
                    if course_id:
                        self.db("course").update(dict(is_featured=True, updated=self.now()), id=course_id)
                return
            rows = self.db("course").rows(is_hidden=False, orderby="display_order,created", order="ASC", page=1, dump=4)
            for row in rows:
                self.db("course").update(dict(is_featured=True, updated=self.now()), id=row.get("id"))
        except Exception:
            pass

    def _ensure_admin_user(self):
        try:
            bootstrap = wiz.model("auth_config").bootstrap_admin()
            if bootstrap is None:
                return

            user = self.core.user.db.get(email=bootstrap["email"])
            if user is None:
                self.core.user.create(bootstrap)
                return

            payload = dict(
                name=bootstrap["name"],
                mobile=bootstrap["mobile"],
                role="admin",
                updated=self.now()
            )
            if not self._password_matches(user.get("password", ""), bootstrap["password"]):
                payload["password"] = self._hash_password(bootstrap["password"])
            self.core.user.db.update(payload, id=user["id"])
        except Exception:
            pass

    def _hash_password(self, password):
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _password_matches(self, hashed, password):
        try:
            if isinstance(hashed, str):
                hashed = hashed.encode("utf-8")
            return bcrypt.checkpw(password.encode("utf-8"), hashed)
        except Exception:
            return False

    def _remove_legacy_example_content(self):
        """Remove the old UI/demo records while preserving user-created content."""
        try:
            example_courses = []
            for row in self.db("course").rows():
                description = str(row.get("description") or "").strip()
                tags = self._load_list(row.get("tags"))
                if description.startswith("[더미]") or "더미" in tags:
                    example_courses.append(row.get("id"))

            for course_id in [value for value in example_courses if value]:
                self.db("course_place").delete(course_id=course_id)
                self.db("featured_course").delete(course_id=course_id)
                self.db("saved_course").delete(course_id=str(course_id))
                self.db("course").delete(id=course_id)

            legacy_course_ids = {
                "course-seongsu-date",
                "course-busan-haeundae",
                "course-jeju-aewol",
            }
            for row in self.db("saved_course").rows():
                course_id = str(row.get("course_id") or "").strip().lower()
                if course_id.startswith(("rec-", "list-")) or course_id in legacy_course_ids:
                    self.db("saved_course").delete(id=row.get("id"))

            example_places = []
            for row in self.db("place").rows():
                external_id = str(row.get("tourapi_id") or "").strip().upper()
                description = str(row.get("description") or "").strip()
                if external_id.startswith("DUMMY-") or description.startswith("[더미]"):
                    example_places.append(row.get("id"))

            for place_id in [value for value in example_places if value]:
                self.db("course_place").delete(place_id=place_id)
                self.db("place").delete(id=place_id)
        except Exception:
            pass

    def _dump_list(self, value):
        if isinstance(value, str):
            value = [item.strip() for item in value.split(",") if item.strip()]
        if not isinstance(value, list):
            value = []
        return json.dumps(value, ensure_ascii=False)

    def _load_list(self, value):
        if isinstance(value, list):
            return value
        try:
            parsed = json.loads(value or "[]")
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []

    def _public_user(self, row):
        row.pop("password", None)
        row["joined"] = str(row.get("created", ""))[:10]
        return row

    def users(self, search="", role=""):
        db = self.db("user").orm
        query = db.select()
        if search:
            query = query.where((db.name.contains(search)) | (db.email.contains(search)))
        if role:
            query = query.where(db.role == role)
        query = query.order_by(db.created.desc())
        return [self._public_user(dict(row)) for row in query.dicts()]

    def update_user_role(self, user_id, role):
        if role not in ["user", "admin", "editor", "viewer"]:
            return None
        user = self.db("user").get(id=user_id)
        if user is None:
            return None
        self.db("user").update(dict(role=role, updated=self.now()), id=user_id)
        return self._public_user(self.db("user").get(id=user_id))

    def delete_user(self, user_id):
        user = self.db("user").get(id=user_id)
        if user is None:
            return None
        if user.get("id") == self.core.session.get("id", ""):
            return dict(error="self", message="현재 로그인한 관리자 계정은 삭제할 수 없습니다.")
        if user.get("role") == "admin":
            return dict(error="protected", message="관리자 계정은 삭제할 수 없습니다.")
        try:
            self.db("saved_course").delete(user_id=user_id)
        except Exception:
            pass
        self.db("user").delete(id=user_id)
        return dict(ok=True)

    def list_places(self, search="", category="", visibility="visible"):
        db = self.db("place").orm
        query = db.select()
        if search:
            query = query.where(
                (db.name.contains(search)) |
                (db.description.contains(search)) |
                (db.overview.contains(search)) |
                (db.usage_time.contains(search)) |
                (db.address.contains(search)) |
                (db.area.contains(search))
            )
        if category:
            query = query.where(db.category == category)
        if visibility == "hidden":
            query = query.where(db.is_hidden == True)
        elif visibility != "all":
            query = query.where(db.is_hidden == False)
        query = query.order_by(db.updated.desc(), db.name.asc())
        return [self._normalize_place(dict(row)) for row in query.dicts()]

    def place_area_summary(self, visibility="visible"):
        db = self.db("place").orm
        count_expr = pw.fn.COUNT(db.id)
        query = db.select(db.area, count_expr.alias("count"))
        if visibility == "hidden":
            query = query.where(db.is_hidden == True)
        elif visibility != "all":
            query = query.where(db.is_hidden == False)
        query = query.group_by(db.area).order_by(count_expr.desc(), db.area.asc())

        total = 0
        rows = []
        for row in query.dicts():
            count = int(row.get("count") or 0)
            total += count
            rows.append(dict(
                area=(row.get("area") or "").strip() or "지역 미지정",
                count=count
            ))
        return dict(total=total, rows=rows)

    def place_area_detail(self, area="", visibility="visible"):
        db = self.db("place").orm
        query = db.select(db.area, db.address, db.category)
        if area:
            query = query.where(db.area == area)
        if visibility == "hidden":
            query = query.where(db.is_hidden == True)
        elif visibility != "all":
            query = query.where(db.is_hidden == False)

        total = 0
        category_counts = {}
        district_map = {}
        for row in query.dicts():
            total += 1
            category = (row.get("category") or "").strip() or "기타"
            district = self._place_district_label(row.get("address", ""))
            category_counts[category] = category_counts.get(category, 0) + 1
            if district not in district_map:
                district_map[district] = dict(area=district, count=0, categories={})
            district_map[district]["count"] += 1
            district_map[district]["categories"][category] = district_map[district]["categories"].get(category, 0) + 1

        districts = []
        for item in district_map.values():
            item["categories"] = self._sorted_count_rows(item["categories"])
            districts.append(item)
        districts.sort(key=lambda item: (-item["count"], item["area"]))

        return dict(
            area=area,
            total=total,
            categories=self._sorted_count_rows(category_counts),
            districts=districts
        )

    def _sorted_count_rows(self, counts):
        rows = [dict(name=name, count=count) for name, count in counts.items()]
        rows.sort(key=lambda item: (-item["count"], item["name"]))
        return rows

    def _place_district_label(self, address):
        tokens = re.split(r"\s+", address or "")
        for token in tokens:
            token = token.strip().strip("(),")
            if not token:
                continue
            if (
                "특별시" in token or
                "광역시" in token or
                "특별자치" in token or
                token.endswith("도")
            ):
                continue
            if token.endswith(("시", "군", "구")):
                return token
        return "세부 지역 미지정"

    def place_categories(self):
        rows = self.db("place").rows(fields="category", groupby="category", orderby="category")
        return [row["category"] for row in rows if row.get("category")]

    def update_place(self, place_id, data):
        if not place_id or self.db("place").get(id=place_id) is None:
            return None
        allowed = [
            "tourapi_id", "content_type_id", "name", "category", "description",
            "overview", "image", "first_image2", "address", "area", "phone",
            "usage_time", "rest_date", "parking_info", "infocenter", "latitude", "longitude",
            "zipcode", "cpyrht_div_cd", "ldong_regn_cd", "ldong_signgu_cd",
            "lcls_systm1", "lcls_systm2", "lcls_systm3",
            "tourapi_created_time", "tourapi_modified_time",
            "detail_intro", "detail_hydrated_at", "detail_hydrate_error",
            "google_place_id", "google_rating", "google_user_ratings_total",
            "google_rating_cached_at", "is_hidden"
        ]
        payload = {key: data[key] for key in allowed if key in data}
        payload["updated"] = self.now()
        self.db("place").update(payload, id=place_id)
        return self._normalize_place(self.db("place").get(id=place_id))

    def hide_place(self, place_id):
        return self.update_place(place_id, dict(is_hidden=True))

    def _normalize_place(self, row):
        row["is_hidden"] = bool(row.get("is_hidden"))
        row["title"] = row.get("name", "")
        row["addr"] = row.get("address", "")
        row["mapx"] = row.get("longitude", "")
        row["mapy"] = row.get("latitude", "")
        row["first_image"] = row.get("image", "")
        return row

    def list_courses(self, search="", category="", visibility="visible"):
        return self.core.course.list_admin(search=search, category=category, visibility=visibility)

    def course_categories(self):
        rows = self.db("course").rows(fields="category", groupby="category", orderby="category")
        return [row["category"] for row in rows if row.get("category")]

    def update_course(self, course_id, data):
        return self.core.course.update(course_id, data)

    def create_course(self, data):
        return self.core.course.create(data)

    def hide_course(self, course_id):
        return self.core.course.hide(course_id)

    def toggle_course_featured(self, course_id, is_featured=None):
        return self.core.course.toggle_featured(course_id, is_featured)

    def update_course_tags(self, course_id, tags):
        return self.update_course(course_id, dict(tags=tags))

    def _normalize_course(self, row):
        return self.core.course.normalize(row)

    def list_featured(self):
        rows = self.db("featured_course").rows(orderby="display_order,updated", order="ASC")
        featured = []
        for row in rows:
            course = self.db("course").get(id=row.get("course_id"))
            if course:
                course = self._normalize_course(course)
                row["course_title"] = course.get("title", "")
                row["course_category"] = course.get("category", "")
                row["course_image"] = course.get("image", "")
                row["course_tags"] = course.get("tags", [])
            featured.append(row)
        return featured

    def add_featured(self, data):
        course_id = data.get("course_id", "")
        if not course_id or self.db("course").get(id=course_id) is None:
            return None
        now = self.now()
        row = dict(
            course_id=course_id,
            display_order=int(data.get("display_order") or 0),
            starts_at=data.get("starts_at", ""),
            ends_at=data.get("ends_at", ""),
            created=now,
            updated=now
        )
        item_id = self.db("featured_course").insert(row)
        self.db("course").update(dict(is_featured=True, updated=now), id=course_id)
        return self.db("featured_course").get(id=item_id)

    def reorder_featured(self, items):
        for index, item in enumerate(items):
            item_id = item.get("id")
            if item_id:
                self.db("featured_course").update(
                    dict(display_order=index + 1, updated=self.now()),
                    id=item_id
                )
        return self.list_featured()

    def remove_featured(self, featured_id):
        row = self.db("featured_course").get(id=featured_id)
        if row is None:
            return False
        self.db("featured_course").delete(id=featured_id)
        course_id = row.get("course_id")
        if course_id and not self.db("featured_course").count(course_id=course_id):
            self.db("course").update(dict(is_featured=False, updated=self.now()), id=course_id)
        return True

    def notices(self):
        rows = self.db("notice").rows(orderby="updated", order="DESC")
        for row in rows:
            row["is_active"] = bool(row.get("is_active"))
        return rows

    def create_notice(self, data):
        now = self.now()
        row = dict(
            title=data.get("title", "").strip(),
            content=data.get("content", "").strip(),
            starts_at=data.get("starts_at", ""),
            ends_at=data.get("ends_at", ""),
            is_active=True,
            created=now,
            updated=now
        )
        if not row["title"]:
            return None
        item_id = self.db("notice").insert(row)
        return self.db("notice").get(id=item_id)

    def terms(self):
        return dict(
            terms=self._setting("terms", ""),
            privacy=self._setting("privacy", "")
        )

    def save_terms(self, data):
        self._save_setting("terms", data.get("terms", ""))
        self._save_setting("privacy", data.get("privacy", ""))
        return self.terms()

    def _setting(self, key, default=""):
        row = self.db("app_setting").get(key=key)
        return row.get("value", default) if row else default

    def _save_setting(self, key, value):
        now = self.now()
        row = self.db("app_setting").get(key=key)
        payload = dict(key=key, value=value, updated=now)
        if row is None:
            self.db("app_setting").insert(payload)
        else:
            self.db("app_setting").update(payload, id=row["id"])

    def log_filter_event(self, filter_key, filter_value, user_id=""):
        if not filter_key or not filter_value:
            return
        self.db("filter_event").insert(dict(
            user_id=user_id or "",
            filter_key=filter_key,
            filter_value=filter_value,
            created=self.now()
        ))

    def stats_overview(self):
        return dict(
            total_users=self.db("user").count() or 0,
            total_courses=self.db("course").count(is_hidden=False) or 0,
            today_dau=self._active_users(days=1),
            week_wau=self._active_users(days=7)
        )

    def signup_trend(self, range_key="7d"):
        days = 7
        if range_key == "30d":
            days = 30
        elif range_key == "90d":
            days = 90
        start = self.today() - datetime.timedelta(days=days - 1)
        db = self.db("user").orm
        date_expr = pw.fn.DATE(db.created)
        query = (
            db.select(date_expr.alias("date"), pw.fn.COUNT(db.id).alias("count"))
            .where(db.created >= start.strftime("%Y-%m-%d 00:00:00"))
            .group_by(date_expr)
        )
        counts = {str(row["date"]): row["count"] for row in query.dicts()}
        rows = []
        for offset in range(days):
            day = start + datetime.timedelta(days=offset)
            key = day.strftime("%Y-%m-%d")
            rows.append(dict(date=key, count=counts.get(key, 0)))
        return rows

    def top_courses(self, limit=10):
        limit = max(1, min(int(limit or 10), 50))
        rows = self.core.course.list_admin(visibility="visible")
        rows.sort(key=lambda row: -int(row.get("saved_count") or 0))
        return [dict(
            course_id=row.get("id"),
            title=row.get("title", ""),
            category=row.get("category", ""),
            saved_count=row.get("saved_count", 0)
        ) for row in rows[:limit]]

    def filter_usage(self):
        event = self.db("filter_event").orm
        count_expr = pw.fn.COUNT(event.id)
        query = (
            event.select(event.filter_key, event.filter_value, count_expr.alias("count"))
            .group_by(event.filter_key, event.filter_value)
            .order_by(event.filter_key.asc(), count_expr.desc())
        )
        grouped = dict(companion=[], schedule=[], location=[])
        for row in query.dicts():
            key = row.get("filter_key", "")
            grouped.setdefault(key, []).append(dict(
                value=row.get("filter_value", ""),
                count=row.get("count", 0)
            ))
        return grouped

    def _active_users(self, days=1):
        start = datetime.datetime.now() - datetime.timedelta(days=days)
        user_ids = set()
        try:
            saved = self.db("saved_course").orm
            query = saved.select(saved.user_id).where(saved.updated >= start).distinct()
            user_ids.update([row.user_id for row in query if row.user_id])
        except Exception:
            pass
        try:
            event = self.db("filter_event").orm
            query = event.select(event.user_id).where(event.created >= start).distinct()
            user_ids.update([row.user_id for row in query if row.user_id])
        except Exception:
            pass
        return len(user_ids)


Model = Admin
