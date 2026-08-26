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
                item_type = str(place.get("item_type") or place.get("itemType") or "place").strip() or "place"
                day = self._int(place.get("day"), 1)
                day_label = str(place.get("day_label") or place.get("dayLabel") or f"{day}일차").strip()
                schedule_date = str(place.get("date") or "").strip()
                item_meta = dict(
                    item_type=item_type,
                    day=day,
                    day_label=day_label,
                    date=schedule_date,
                    name=str(place.get("name") or "").strip(),
                    area=str(place.get("area") or "").strip(),
                    address=str(place.get("address") or "").strip(),
                    category=str(place.get("category") or "").strip(),
                    image=str(place.get("image") or "").strip(),
                    latitude=place.get("latitude", place.get("lat")),
                    longitude=place.get("longitude", place.get("lng")),
                )
                if memo.startswith("__gachi_item__"):
                    try:
                        stored_meta = json.loads(memo[len("__gachi_item__"):])
                    except Exception:
                        stored_meta = {}
                    if isinstance(stored_meta, dict):
                        item_meta.update(stored_meta)
                        memo = str(stored_meta.get("memo") or "")[:1000]
            else:
                place_id = place
                order_index = index
                visit_time = ""
                memo = ""
                item_type = "place"
                item_meta = dict(item_type="place", day=1, day_label="1일차", date="")
            place_id = str(place_id or "").strip()
            if not place_id:
                continue
            items.append(dict(
                place_id=place_id,
                order_index=order_index,
                visit_time=visit_time,
                memo=memo,
                item_type=item_type,
                item_meta=item_meta,
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
            if self.db("place").get(id=place_id) is None and item.get("item_type") == "place":
                continue
            stored_memo = item.get("memo", "")
            meta = dict(item.get("item_meta") or {})
            if (
                meta.get("item_type") != "place"
                or meta.get("day", 1) > 1
                or meta.get("day_label", "1일차") != "1일차"
                or meta.get("date")
            ):
                meta["memo"] = stored_memo
                stored_memo = "__gachi_item__" + json.dumps(meta, ensure_ascii=False)
            self.db("course_place").insert(dict(
                course_id=course_id,
                place_id=place_id,
                order_index=order_index,
                visit_time=item.get("visit_time", ""),
                memo=stored_memo,
                created=now
            ))
            seen.add(place_id)
            order_index += 1

    def _places_for_ids(self, place_ids, place_meta=None):
        place_meta = place_meta or {}
        places = []
        for place_id in place_ids:
            row = self.db("place").get(id=place_id)
            meta = place_meta.get(place_id, {})
            if row is None and meta.get("item_type") != "place":
                row = dict(
                    id=place_id,
                    name=meta.get("name", "일정"),
                    category=meta.get("category", "기타 일정"),
                    address=meta.get("address", ""),
                    area=meta.get("area", ""),
                    image=meta.get("image", ""),
                    latitude=meta.get("latitude"),
                    longitude=meta.get("longitude"),
                )
            if row is None:
                continue
            row["is_hidden"] = bool(row.get("is_hidden"))
            row["rating"] = self._float_or_none(row.get("provider_rating"))
            row["user_ratings_total"] = self._int(row.get("provider_user_ratings_total"), 0)
            row["title"] = row.get("name", "")
            row["addr"] = row.get("address", "")
            row["mapx"] = row.get("longitude", "")
            row["mapy"] = row.get("latitude", "")
            row["first_image"] = row.get("image", "")
            row["order_index"] = meta.get("order_index", len(places) + 1)
            row["visit_time"] = meta.get("visit_time", "")
            row["memo"] = meta.get("memo", "")
            row["item_type"] = meta.get("item_type", "place")
            row["day"] = meta.get("day", 1)
            row["day_label"] = meta.get("day_label", "1일차")
            row["date"] = meta.get("date", "")
            places.append(row)
        return places

    def _course_place_meta(self, course_id):
        rows = self.db("course_place").rows(course_id=course_id, orderby="order_index", order="ASC")
        result = {}
        for row in rows:
            if not row.get("place_id"):
                continue
            memo = str(row.get("memo") or "")
            extra = {}
            if memo.startswith("__gachi_item__"):
                try:
                    extra = json.loads(memo[len("__gachi_item__"):])
                except Exception:
                    extra = {}
                memo = str(extra.pop("memo", ""))
            result[row.get("place_id")] = dict(
                order_index=row.get("order_index"),
                visit_time=row.get("visit_time", ""),
                memo=memo,
                **extra,
            )
        return result

    def course_like_count(self, course_id):
        course = self.db("course").get(id=course_id)
        owner_id = str(course.get("user_id") or "") if course else ""

        likes = 0
        for row in self.db("course_like").rows(course_id=course_id):
            if owner_id and str(row.get("user_id") or "") == owner_id:
                continue
            likes += 1

        saved = 0
        for row in self.db("saved_course").rows(course_id=course_id):
            try:
                route = json.loads(row.get("route_json") or "{}")
            except Exception:
                route = {}
            if not isinstance(route, dict):
                route = {}
            is_mine = str(route.get("source") or "") == "mine" or (
                owner_id and str(row.get("user_id") or "") == owner_id
            )
            if not is_mine:
                saved += 1

        return max(likes, saved)

    def calculate_rating(self, course_id=None, place_ids=None):
        if place_ids is None and course_id:
            course = self.db("course").get(id=course_id)
            fallback = self._load_list(course.get("place_ids")) if course else []
            place_ids = self._course_place_ids(course_id, fallback)
        ratings = []
        for place in self._places_for_ids(place_ids or []):
            rating = self._float_or_none(place.get("provider_rating"))
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

    def create(self, data, course_id=""):
        title = str(data.get("title", "")).strip()
        if not title:
            return None
        now = self.now()
        payload, place_items = self._payload(data)
        payload["title"] = title
        payload["created"] = now
        payload["updated"] = now
        course_id = str(course_id or "").strip()
        if course_id and len(course_id) <= 32 and self.db("course").get(id=course_id) is None:
            payload["id"] = course_id
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

    def delete(self, course_id):
        current = self.db("course").get(id=course_id)
        if current is None:
            return False
        for table_name in ["course_place", "featured_course", "saved_course", "course_like", "course_checkin"]:
            try:
                self.db(table_name).delete(course_id=str(course_id))
            except Exception:
                pass
        self.db("course").delete(id=course_id)
        return self.db("course").get(id=course_id) is None

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
        tags = self._load_list(row.get("tags"))
        archive_tag = "__gachi_archived__"
        row["archived"] = archive_tag in tags
        row["tags"] = [tag for tag in tags if tag != archive_tag]

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
        for stored in self.db("course").rows(user_id=user_id, orderby="updated", order="DESC", dump=80):
            course = self.normalize(stored)
            rows.append(dict(
                id=course.get("id", ""),
                title=course.get("title", "새 여행 코스"),
                location=course.get("region", ""),
                summary=course.get("description", ""),
                duration=course.get("duration", ""),
                source="mine",
                place_count=len(course.get("place_ids", [])),
            ))
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
