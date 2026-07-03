import datetime
import json


class Course:
    def __init__(self, core):
        self.core = core

    def now(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def db(self, name):
        return self.core.db(name)

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

    def _bool(self, value):
        if isinstance(value, str):
            return value.lower() in ["1", "true", "yes", "y", "on"]
        return bool(value)

    def _int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default

    def _float_or_none(self, value):
        if value in [None, ""]:
            return None
        try:
            return float(value)
        except Exception:
            return None

    def _duration_label(self, duration_type, duration_value):
        value = str(duration_value or "").strip()
        if not value:
            return ""
        if duration_type == "hours":
            return value if "시간" in value else f"{value}시간"
        return value

    def _course_place_ids(self, course_id, fallback=None):
        rows = self.db("course_place").rows(course_id=course_id, orderby="order_index", order="ASC")
        place_ids = [row.get("place_id") for row in rows if row.get("place_id")]
        if place_ids:
            return place_ids
        return fallback or []

    def _normalize_place_items(self, places):
        items = []
        if not isinstance(places, list):
            return items
        for index, place in enumerate(places, start=1):
            if isinstance(place, dict):
                place_id = place.get("place_id") or place.get("placeId") or place.get("id")
                order_index = self._int(place.get("order_index", place.get("order", index)), index)
                visit_time = str(place.get("visit_time") or place.get("visitTime") or "").strip()
                memo = str(place.get("memo") or "")[:1000]
            else:
                place_id = place
                order_index = index
                visit_time = ""
                memo = ""
            place_id = str(place_id or "").strip()
            if not place_id:
                continue
            items.append(dict(
                place_id=place_id,
                order_index=order_index,
                visit_time=visit_time,
                memo=memo,
            ))
        items.sort(key=lambda item: item.get("order_index") or 0)
        return items

    def _sync_course_places(self, course_id, places):
        self.db("course_place").delete(course_id=course_id)
        now = self.now()
        seen = set()
        items = self._normalize_place_items(places)
        order_index = 1
        for item in items:
            place_id = item.get("place_id")
            if not place_id or place_id in seen:
                continue
            if self.db("place").get(id=place_id) is None:
                continue
            self.db("course_place").insert(dict(
                course_id=course_id,
                place_id=place_id,
                order_index=order_index,
                visit_time=item.get("visit_time", ""),
                memo=item.get("memo", ""),
                created=now
            ))
            seen.add(place_id)
            order_index += 1

    def _places_for_ids(self, place_ids, place_meta=None):
        place_meta = place_meta or {}
        places = []
        for place_id in place_ids:
            row = self.db("place").get(id=place_id)
            if row is None:
                continue
            meta = place_meta.get(place_id, {})
            row["is_hidden"] = bool(row.get("is_hidden"))
            row["rating"] = self._float_or_none(row.get("google_rating"))
            row["user_ratings_total"] = self._int(row.get("google_user_ratings_total"), 0)
            row["title"] = row.get("name", "")
            row["addr"] = row.get("address", "")
            row["mapx"] = row.get("longitude", "")
            row["mapy"] = row.get("latitude", "")
            row["first_image"] = row.get("image", "")
            row["order_index"] = meta.get("order_index", len(places) + 1)
            row["visit_time"] = meta.get("visit_time", "")
            row["memo"] = meta.get("memo", "")
            places.append(row)
        return places

    def _course_place_meta(self, course_id):
        rows = self.db("course_place").rows(course_id=course_id, orderby="order_index", order="ASC")
        return {
            row.get("place_id"): dict(
                order_index=row.get("order_index"),
                visit_time=row.get("visit_time", ""),
                memo=row.get("memo", ""),
            )
            for row in rows
            if row.get("place_id")
        }

    def course_like_count(self, course_id):
        likes = self.db("course_like").count(course_id=course_id) or 0
        saved = self.db("saved_course").count(course_id=course_id) or 0
        return max(likes, saved)

    def calculate_rating(self, course_id=None, place_ids=None):
        if place_ids is None and course_id:
            course = self.db("course").get(id=course_id)
            fallback = self._load_list(course.get("place_ids")) if course else []
            place_ids = self._course_place_ids(course_id, fallback)
        ratings = []
        for place in self._places_for_ids(place_ids or []):
            rating = self._float_or_none(place.get("google_rating"))
            if rating:
                ratings.append(rating)
        if not ratings:
            return None
        return round(sum(ratings) / len(ratings), 1)

    def recalculate_rating(self, course_id):
        rating = self.calculate_rating(course_id=course_id)
        self.db("course").update(dict(rating=rating, updated=self.now()), id=course_id)
        return rating

    def _cover_from_places(self, place_ids):
        for place in self._places_for_ids(place_ids):
            image = place.get("image", "")
            if image:
                return image
        return ""

    def _payload(self, data, current=None):
        current = current or {}
        duration_type = data.get("duration_type", current.get("duration_type", "hours"))
        if duration_type not in ["hours", "overnight"]:
            duration_type = "hours"

        place_items = self._normalize_place_items(data.get("places", []))
        place_ids = data.get("place_ids", current.get("place_ids", []))
        if isinstance(place_ids, str):
            place_ids = self._load_list(place_ids)
        if not isinstance(place_ids, list):
            place_ids = []
        if place_items:
            place_ids = [item.get("place_id") for item in place_items if item.get("place_id")]
        elif place_ids:
            place_items = self._normalize_place_items(place_ids)

        cover_image = data.get("cover_image", data.get("image", current.get("cover_image", current.get("image", ""))))
        if not cover_image:
            cover_image = self._cover_from_places(place_ids)

        payload = {}
        allowed = [
            "title", "region", "category", "description", "display_order",
            "is_hidden", "is_featured", "is_public", "duration_value",
            "companion_type", "user_id"
        ]
        for key in allowed:
            if key in data:
                payload[key] = data[key]
        payload["duration_type"] = duration_type
        payload["cover_image"] = cover_image or ""
        payload["image"] = data.get("image", cover_image or "")
        payload["place_ids"] = self._dump_list(place_ids)

        tags = data.get("tags", current.get("tags", []))
        payload["tags"] = self._dump_list(tags)

        if "display_order" in payload:
            payload["display_order"] = self._int(payload["display_order"], 0)
        if "is_hidden" in payload:
            payload["is_hidden"] = self._bool(payload["is_hidden"])
        if "is_featured" in payload:
            payload["is_featured"] = self._bool(payload["is_featured"])
        if "is_public" in payload:
            payload["is_public"] = self._bool(payload["is_public"])
            if "is_hidden" not in payload:
                payload["is_hidden"] = not payload["is_public"]
        payload["rating"] = self.calculate_rating(place_ids=place_ids)
        return payload, place_items

    def create(self, data):
        title = str(data.get("title", "")).strip()
        if not title:
            return None
        now = self.now()
        payload, place_items = self._payload(data)
        payload["title"] = title
        payload["created"] = now
        payload["updated"] = now
        course_id = self.db("course").insert(payload)
        self._sync_course_places(course_id, place_items)
        return self.get(course_id, include_places=True)

    def update(self, course_id, data):
        current = self.db("course").get(id=course_id)
        if current is None:
            return None
        payload, place_items = self._payload(data, current=current)
        payload["updated"] = self.now()
        self.db("course").update(payload, id=course_id)
        if "place_ids" in data or "places" in data:
            self._sync_course_places(course_id, place_items)
        return self.get(course_id, include_places=True)

    def hide(self, course_id):
        return self.update(course_id, dict(is_hidden=True))

    def toggle_featured(self, course_id, is_featured=None):
        current = self.db("course").get(id=course_id)
        if current is None:
            return None
        if is_featured is None:
            is_featured = not bool(current.get("is_featured"))
        self.db("course").update(dict(is_featured=self._bool(is_featured), updated=self.now()), id=course_id)
        return self.get(course_id)

    def get(self, course_id, include_places=False):
        row = self.db("course").get(id=course_id)
        if row is None:
            return None
        return self.normalize(row, include_places=include_places)

    def list_admin(self, search="", category="", visibility="visible"):
        db = self.db("course").orm
        query = db.select()
        if search:
            query = query.where((db.title.contains(search)) | (db.description.contains(search)) | (db.region.contains(search)))
        if category:
            query = query.where(db.category == category)
        if visibility == "hidden":
            query = query.where(db.is_hidden == True)
        elif visibility != "all":
            query = query.where(db.is_hidden == False)
        query = query.order_by(db.display_order.asc(), db.updated.desc())
        return [self.normalize(dict(row)) for row in query.dicts()]

    def popular(self, limit=4):
        limit = max(1, min(self._int(limit, 4), 20))
        featured_rows = self.db("featured_course").rows()
        featured_ids = set([row.get("course_id") for row in featured_rows if row.get("course_id")])

        db = self.db("course").orm
        query = db.select().where(db.is_hidden == False)
        rows = []
        for row in query.dicts():
            data = dict(row)
            if not data.get("is_featured") and data.get("id") not in featured_ids:
                continue
            normalized = self.normalize(data)
            rows.append(normalized)

        rows.sort(key=lambda row: (
            -self._int(row.get("like_count"), 0),
            self._int(row.get("display_order"), 0),
            str(row.get("updated", ""))
        ))
        return rows[:limit]

    def normalize(self, row, include_places=False):
        row["is_hidden"] = bool(row.get("is_hidden"))
        row["is_featured"] = bool(row.get("is_featured"))
        row["is_public"] = bool(row.get("is_public", not row.get("is_hidden")))
        row["companion_type"] = row.get("companion_type", "")
        fallback_place_ids = self._load_list(row.get("place_ids"))
        place_ids = self._course_place_ids(row.get("id"), fallback_place_ids)
        row["place_ids"] = place_ids
        row["tags"] = self._load_list(row.get("tags"))

        places = self._places_for_ids(place_ids, self._course_place_meta(row.get("id")))
        if include_places:
            row["places"] = places

        if not row.get("region") and places:
            row["region"] = places[0].get("area", "")
        if not row.get("cover_image"):
            row["cover_image"] = row.get("image", "") or self._cover_from_places(place_ids)
        if not row.get("image"):
            row["image"] = row.get("cover_image", "")

        if not row.get("duration_value"):
            row["duration_value"] = "4" if row.get("duration_type", "hours") == "hours" else "1박 2일"
        if not row.get("duration_type"):
            row["duration_type"] = "hours"

        calculated_rating = self.calculate_rating(place_ids=place_ids)
        rating = calculated_rating if calculated_rating is not None else self._float_or_none(row.get("rating"))
        row["rating"] = round(rating, 1) if rating is not None else None
        row["duration"] = self._duration_label(row.get("duration_type"), row.get("duration_value"))
        row["like_count"] = self.course_like_count(row.get("id"))
        row["saved_count"] = row["like_count"]
        row["location"] = row.get("region", "")
        row["summary"] = row.get("description", "")
        return row

    def execution_catalog(self, user_id):
        if not user_id:
            return []

        rows = []
        seen = set()
        for row in self.db("course").rows(user_id=user_id, orderby="updated", order="DESC", dump=80):
            course = self.normalize(row)
            seen.add(course.get("id"))
            rows.append(dict(
                id=course.get("id", ""),
                title=course.get("title", "새 여행 코스"),
                location=course.get("region", ""),
                summary=course.get("description", ""),
                duration=course.get("duration", ""),
                source="mine",
                place_count=len(course.get("place_ids", [])),
            ))

        for row in self.db("saved_course").rows(user_id=user_id, orderby="updated", order="DESC", dump=80):
            course_id = row.get("course_id", "")
            if course_id in seen:
                continue
            places = self._load_list(row.get("places_json"))
            if not places:
                try:
                    places = json.loads(row.get("places_json") or "[]")
                except Exception:
                    places = []
            rows.append(dict(
                id=course_id,
                title=row.get("title", "저장한 코스"),
                location=row.get("location", ""),
                summary=row.get("summary", ""),
                duration=row.get("duration", ""),
                source="saved",
                place_count=len(places) if isinstance(places, list) else 0,
            ))
            seen.add(course_id)
        return rows

    def execution(self, course_id, user_id=""):
        course = self.db("course").get(id=course_id)
        checkins = self._execution_checkin_map(course_id, user_id)
        if course is not None:
            data = self.normalize(course, include_places=True)
            places = [
                self._execution_place_from_db(row, index + 1, checkins)
                for index, row in enumerate(data.get("places", []))
            ]
            return self._execution_payload(data, places, "course")

        saved = self.db("saved_course").get(course_id=course_id, user_id=user_id) if user_id else None
        if saved is None:
            saved = self.db("saved_course").get(course_id=course_id)
        if saved is None:
            return None

        places = []
        try:
            saved_places = json.loads(saved.get("places_json") or "[]")
        except Exception:
            saved_places = []
        if not isinstance(saved_places, list):
            saved_places = []
        for index, place in enumerate(saved_places, start=1):
            places.append(self._execution_place_from_saved(place, index, checkins))

        course_data = dict(
            id=saved.get("course_id", ""),
            title=saved.get("title", "저장한 코스"),
            region=saved.get("location", ""),
            category="여행",
            duration=saved.get("duration", ""),
            summary=saved.get("summary", ""),
        )
        return self._execution_payload(course_data, places, "saved")

    def checkin(self, course_id, place_id, user_id, method="manual", lat="", lng=""):
        if not user_id or not course_id or not place_id:
            return None
        method = method if method in ["auto", "manual"] else "manual"
        now = self.now()
        db = self.db("course_checkin")
        try:
            db.orm.create_table(safe=True)
        except Exception:
            pass

        data = dict(
            user_id=user_id,
            course_id=course_id,
            place_id=place_id,
            method=method,
            lat=str(lat or ""),
            lng=str(lng or ""),
            checked_at=now,
        )
        current = db.get(user_id=user_id, course_id=course_id, place_id=place_id)
        if current:
            db.update(data, id=current["id"])
            data["id"] = current["id"]
        else:
            data["id"] = db.insert(data)
        try:
            self.core.zenly.record_presence(place_id, amount=1)
        except Exception:
            pass
        return data

    def _execution_checkin_map(self, course_id, user_id):
        if not user_id:
            return {}
        db = self.db("course_checkin")
        try:
            db.orm.create_table(safe=True)
        except Exception:
            pass
        rows = db.rows(user_id=user_id, course_id=course_id, dump=500)
        return {row.get("place_id"): row for row in rows if row.get("place_id")}

    def _execution_payload(self, course, places, source):
        checked = len([place for place in places if place.get("checked")])
        return dict(
            course=dict(
                id=course.get("id", ""),
                title=course.get("title", "새 여행 코스"),
                region=course.get("region", course.get("location", "")),
                category=course.get("category", "여행"),
                duration=course.get("duration", ""),
                summary=course.get("summary", course.get("description", "")),
                source=source,
            ),
            places=places,
            progress=dict(
                checked=checked,
                total=len(places),
            ),
        )

    def _execution_place_from_db(self, row, order, checkins):
        place_id = row.get("id", "")
        checkin = checkins.get(place_id, {})
        category_label, category_key = self._execution_category(row.get("category", ""), row.get("content_type_id", ""))
        return dict(
            place_id=place_id,
            order=order,
            name=row.get("name", ""),
            category=row.get("category", ""),
            category_label=category_label,
            category_key=category_key,
            address=row.get("address", "") or row.get("area", ""),
            lat=self._float_or_none(row.get("latitude")),
            lng=self._float_or_none(row.get("longitude")),
            hours=row.get("usage_time", "") or row.get("rest_date", "") or "확인 필요",
            memo=row.get("memo", ""),
            visit_time=row.get("visit_time", ""),
            rating=row.get("rating", ""),
            image=row.get("image", "") or row.get("first_image2", ""),
            icon=self._execution_icon(category_key),
            checked=bool(checkin),
            checked_at=str(checkin.get("checked_at", "")) if checkin else "",
            checkin_method=checkin.get("method", "") if checkin else "",
        )

    def _execution_place_from_saved(self, row, order, checkins):
        row = row if isinstance(row, dict) else {}
        place_id = str(row.get("place_id") or row.get("id") or f"saved-{order}").strip()
        checkin = checkins.get(place_id, {})
        category_label, category_key = self._execution_category(row.get("tag", row.get("category", "")), "")
        return dict(
            place_id=place_id,
            order=order,
            name=row.get("name", ""),
            category=row.get("tag", row.get("category", "")),
            category_label=category_label,
            category_key=category_key,
            address=row.get("area", row.get("address", "")),
            lat=self._float_or_none(row.get("lat")),
            lng=self._float_or_none(row.get("lng")),
            hours=row.get("time", "") or "확인 필요",
            memo=row.get("memo", ""),
            visit_time=row.get("time", ""),
            rating=row.get("rating", ""),
            image=row.get("image", ""),
            icon=self._execution_icon(category_key),
            checked=bool(checkin),
            checked_at=str(checkin.get("checked_at", "")) if checkin else "",
            checkin_method=checkin.get("method", "") if checkin else "",
        )

    def _execution_category(self, category, content_type_id):
        text = str(category or "")
        if "카페" in text or "커피" in text:
            return "카페", "cafe"
        if "맛" in text or "음식" in text or "식당" in text or str(content_type_id) == "39":
            return "맛집", "food"
        if "산책" in text or "공원" in text or "해변" in text or "숲" in text:
            return "산책", "walk"
        if "숙" in text or str(content_type_id) == "32":
            return "숙소", "stay"
        if "쇼핑" in text or str(content_type_id) == "38":
            return "쇼핑", "shopping"
        return "명소", "landmark"

    def _execution_icon(self, category_key):
        icons = dict(
            cafe="fa-mug-saucer",
            food="fa-utensils",
            walk="fa-person-walking",
            stay="fa-bed",
            shopping="fa-bag-shopping",
            landmark="fa-location-dot",
        )
        return icons.get(category_key, "fa-location-dot")


Model = Course
