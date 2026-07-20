import json
import math
import os
import re
import time
import urllib.parse
import urllib.request


PLACE_SEARCH_DECLARATION = {
    "type": "function",
    "name": "place_search",
    "description": (
        "사용자의 대화 내용을 바탕으로 조건에 맞는 실제 장소를 places 데이터베이스에서 검색합니다. "
        "카페, 맛집, 관광지, 숙소 등 코스에 넣을 장소를 언급하기 전에 반드시 이 함수를 호출해서 "
        "실존 여부를 확인해야 합니다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "region": {
                "type": "string",
                "description": "검색할 지역명 (예: '부산 해운대', '서울 성수')",
            },
            "category": {
                "type": "string",
                "enum": ["관광지", "카페", "음식점", "숙박", "레포츠", "문화시설", "쇼핑", "야경", "자연"],
                "description": "장소 카테고리",
            },
            "keyword": {
                "type": "string",
                "description": "구체적인 검색어 (예: '조개구이', '감성 카페', '바다뷰'). 선택 사항.",
            },
            "mood_tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "분위기 태그 (예: ['조용한', '로맨틱한', '활기찬']). 선택 사항.",
            },
            "exclude_place_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "이미 코스에 포함되어 제외해야 할 장소 ID 목록",
            },
            "limit": {
                "type": "integer",
                "description": "반환할 최대 개수 (기본값 5)",
            },
        },
        "required": ["region", "category"],
    },
}

DIRECTIONS_LOOKUP_DECLARATION = {
    "type": "function",
    "name": "directions_lookup",
    "description": (
        "두 장소 사이의 실제 이동 방법과 소요시간을 조회합니다. 코스 제안 시 장소 간 이동시간을 "
        "언급하기 전 반드시 호출해서 정확한 값을 사용해야 합니다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "origin_place_id": {"type": "string", "description": "출발 장소의 places.id"},
            "destination_place_id": {"type": "string", "description": "도착 장소의 places.id"},
            "mode": {
                "type": "string",
                "enum": ["walking", "transit", "driving"],
                "description": "이동 수단",
            },
        },
        "required": ["origin_place_id", "destination_place_id", "mode"],
    },
}


class AiTools:
    SEARCH_FIELDS = ["name", "category", "description", "overview", "address", "area"]
    CATEGORY_CONTENT_TYPES = {
        "관광지": ["12"],
        "자연": ["12"],
        "야경": ["12", "14"],
        "문화시설": ["14"],
        "레포츠": ["28"],
        "숙박": ["32"],
        "쇼핑": ["38"],
        "카페": ["39"],
        "음식점": ["39"],
    }
    CAFE_KEYWORDS = ["카페", "커피", "로스터리", "베이커리", "브런치", "디저트", "라떼"]
    SPECIFIC_NO_RELAX_KEYWORDS = ["스키", "스키장", "눈썰매", "워터파크"]
    DIRECTION_TTL_SECONDS = 60 * 60 * 24
    _direction_cache = {}

    def function_declarations(self):
        return [PLACE_SEARCH_DECLARATION, DIRECTIONS_LOOKUP_DECLARATION]

    def execute_place_search(self, input_data):
        data = input_data if isinstance(input_data, dict) else {}
        region = self._clean(data.get("region"), 80)
        category = self._clean(data.get("category"), 40)
        keyword = self._clean(data.get("keyword"), 80)
        mood_tags = self._list(data.get("mood_tags"))
        exclude_place_ids = set(self._list(data.get("exclude_place_ids")))
        limit = self._int(data.get("limit"), 5)
        limit = max(1, min(limit, 10))

        attempts = [
            ("strict", True, True, True),
            ("relaxed_mood", True, True, False),
        ]
        if keyword and not self._blocks_keyword_relax(keyword):
            attempts.append(("relaxed_keyword", True, False, False))
        if category and category not in ["레포츠"]:
            attempts.append(("relaxed_category", False, True, False))

        last_error = ""
        for attempt, use_category, use_keyword, use_mood in attempts:
            try:
                rows = self._query_places(
                    region=region,
                    category=category if use_category else "",
                    keyword=keyword if use_keyword else "",
                    mood_tags=mood_tags if use_mood else [],
                    exclude_place_ids=exclude_place_ids,
                    limit=limit,
                )
            except Exception as error:
                last_error = str(error)
                rows = []
            if rows:
                return {
                    "status": "ok" if attempt == "strict" else "relaxed",
                    "relaxation": "" if attempt == "strict" else attempt,
                    "query": {
                        "region": region,
                        "category": category,
                        "keyword": keyword,
                        "mood_tags": mood_tags,
                        "exclude_place_ids": list(exclude_place_ids),
                        "limit": limit,
                    },
                    "results": rows,
                    "message": "실제 places 데이터베이스에서 조회한 장소입니다.",
                }

        result = {
            "status": "not_found",
            "query": {
                "region": region,
                "category": category,
                "keyword": keyword,
                "mood_tags": mood_tags,
                "exclude_place_ids": list(exclude_place_ids),
                "limit": limit,
            },
            "results": [],
            "message": "조건에 맞는 실제 장소를 places 데이터베이스에서 찾지 못했습니다.",
        }
        if last_error:
            result["error"] = last_error
        return result

    def execute_directions_lookup(self, input_data):
        data = input_data if isinstance(input_data, dict) else {}
        origin_id = self._clean(data.get("origin_place_id"), 64)
        destination_id = self._clean(data.get("destination_place_id"), 64)
        mode = self._clean(data.get("mode"), 24) or "walking"
        if mode not in ["walking", "transit", "driving"]:
            mode = "walking"

        cache_key = f"{origin_id}:{destination_id}:{mode}"
        cached = self._direction_cache.get(cache_key)
        now = time.time()
        if cached and now - cached.get("created_at", 0) < self.DIRECTION_TTL_SECONDS:
            result = dict(cached["result"])
            result["cache"] = "hit"
            return result

        origin = self._get_place(origin_id)
        destination = self._get_place(destination_id)
        if not origin or not destination:
            return {
                "status": "not_found",
                "duration_minutes": None,
                "distance_meters": None,
                "mode": mode,
                "message": "출발지 또는 도착지를 places 데이터베이스에서 찾지 못했습니다.",
            }

        result = self._google_directions(origin, destination, mode)
        if result is None:
            result = self._estimated_directions(origin, destination, mode)

        self._direction_cache[cache_key] = {"created_at": now, "result": result}
        return dict(result, cache="miss")

    def execute_segment_lookup(self, input_data):
        data = input_data if isinstance(input_data, dict) else {}
        origin_lat = self._float(data.get("origin_lat"))
        origin_lng = self._float(data.get("origin_lng"))
        destination_id = self._clean(data.get("destination_place_id"), 64)
        mode = self._clean(data.get("mode"), 24) or "walking"
        if mode == "walk":
            mode = "walking"
        if mode == "car":
            mode = "driving"
        if mode not in ["walking", "transit", "driving"]:
            mode = "walking"

        if origin_lat is None or origin_lng is None:
            return {
                "status": "not_available",
                "duration_minutes": None,
                "distance_meters": None,
                "mode": mode,
                "message": "출발 좌표를 확인하지 못했습니다.",
            }

        destination = self._get_place(destination_id)
        if not destination:
            return {
                "status": "not_found",
                "duration_minutes": None,
                "distance_meters": None,
                "mode": mode,
                "message": "도착 장소를 places 데이터베이스에서 찾지 못했습니다.",
            }

        destination_coord = self._coord(destination)
        if not destination_coord:
            return {
                "status": "not_available",
                "duration_minutes": None,
                "distance_meters": None,
                "mode": mode,
                "message": "도착 장소 좌표가 없어 이동시간을 계산하지 못했습니다.",
            }

        # GPS 좌표는 초 단위로 흔들리므로 5자리 반올림 좌표를 캐시 키로 사용한다.
        origin_coord = (round(origin_lat, 5), round(origin_lng, 5))
        cache_key = f"segment:{origin_coord[0]}:{origin_coord[1]}:{destination_id}:{mode}"
        cached = self._direction_cache.get(cache_key)
        now = time.time()
        if cached and now - cached.get("created_at", 0) < self.DIRECTION_TTL_SECONDS:
            result = dict(cached["result"])
            result["cache"] = "hit"
            return result

        result = self._google_directions_coords(origin_coord, destination_coord, mode)
        if result is None:
            result = self._estimated_directions_coords(origin_coord, destination_coord, mode)

        self._direction_cache[cache_key] = {"created_at": now, "result": result}
        return dict(result, cache="miss")

    def _place_db(self):
        return wiz.model("portal/season/orm").use("place").orm

    def _get_place(self, place_id):
        if not place_id:
            return None
        db = self._place_db()
        row = db.get_or_none(db.id == place_id)
        return dict(row.__data__) if row else None

    def _query_places(self, region, category, keyword, mood_tags, exclude_place_ids, limit):
        db = self._place_db()
        condition = db.is_hidden == False

        region_condition = self._region_condition(db, region)
        if region_condition is not None:
            condition = condition & region_condition

        category_condition = self._category_condition(db, category)
        if category_condition is not None:
            condition = condition & category_condition

        keyword_condition = self._keyword_condition(db, self._tokens(keyword))
        if keyword_condition is not None:
            condition = condition & keyword_condition

        mood_condition = self._keyword_condition(db, self._tokens(" ".join(mood_tags)))
        if mood_condition is not None:
            condition = condition & mood_condition

        if exclude_place_ids:
            condition = condition & (~db.id.in_(list(exclude_place_ids)))

        rows = []
        for row in (
            db.select()
            .where(condition)
            .order_by(db.google_rating.desc(), db.google_user_ratings_total.desc(), db.updated.desc())
            .limit(300)
            .dicts()
        ):
            rows.append(dict(row))

        rows.sort(key=self._score, reverse=True)
        return [self._normalize_place(row, category) for row in rows[:limit]]

    def _region_condition(self, db, region):
        tokens = self._tokens(region)
        if not tokens:
            return None

        condition = None
        for token in tokens:
            token_condition = self._keyword_condition(
                db,
                [token],
                fields=["area", "address", "name", "category"],
            )
            if token_condition is None:
                continue
            condition = token_condition if condition is None else condition & token_condition
        return condition

    def _category_condition(self, db, category):
        content_type_ids = self.CATEGORY_CONTENT_TYPES.get(category, [])
        condition = db.content_type_id.in_(content_type_ids) if content_type_ids else None
        if category == "카페":
            include = self._keyword_condition(db, self.CAFE_KEYWORDS)
            condition = include if condition is None else condition & include
        elif category == "음식점":
            exclude = self._keyword_condition(db, self.CAFE_KEYWORDS)
            if exclude is not None:
                condition = condition & (~exclude) if condition is not None else ~exclude
        elif category == "야경":
            night = self._keyword_condition(db, ["야경", "밤", "전망", "스카이", "타워"])
            if night is not None:
                condition = condition & night if condition is not None else night
        elif category == "자연":
            nature = self._keyword_condition(db, ["공원", "해변", "바다", "산", "숲", "섬", "강"])
            if nature is not None:
                condition = condition & nature if condition is not None else nature
        return condition

    def _keyword_condition(self, db, keywords, fields=None):
        fields = fields or self.SEARCH_FIELDS
        condition = None
        for keyword in keywords or []:
            keyword = self._clean(keyword, 40)
            if not keyword:
                continue
            token_condition = None
            for field in fields:
                column = getattr(db, field)
                part = column.is_null(False) & column.contains(keyword)
                token_condition = part if token_condition is None else token_condition | part
            condition = token_condition if condition is None else condition | token_condition
        return condition

    def _normalize_place(self, row, requested_category):
        rating = self._float(row.get("google_rating"))
        return {
            "place_id": row.get("id", ""),
            "name": row.get("name", ""),
            "category": requested_category or row.get("category", ""),
            "address": row.get("address", "") or row.get("area", ""),
            "lat": self._float(row.get("latitude")),
            "lng": self._float(row.get("longitude")),
            "rating": round(rating, 1) if rating is not None else None,
            "thumbnail": row.get("image") or row.get("first_image2") or "",
            "overview_summary": self._summary(row),
            "usage_time": row.get("usage_time") or "",
            "rest_date": row.get("rest_date") or "",
        }

    def _summary(self, row):
        name = self._clean(row.get("name"), 100)
        for key in ["overview", "description"]:
            value = self._clean(row.get(key), 120)
            if value and value != name:
                return value
        address = self._clean(row.get("address"), 120)
        if address:
            return address
        return self._clean(f"{row.get('area', '')} {row.get('category', '')}", 120)

    def _score(self, row):
        rating = self._float(row.get("google_rating"))
        rating_value = rating if rating is not None else -1
        image_value = 1 if row.get("image") or row.get("first_image2") else 0
        return (
            1 if rating is not None else 0,
            rating_value,
            self._int(row.get("google_user_ratings_total"), 0),
            image_value,
            str(row.get("updated", "")),
        )

    def _google_directions(self, origin, destination, mode):
        origin_coord = self._coord(origin)
        destination_coord = self._coord(destination)
        return self._google_directions_coords(origin_coord, destination_coord, mode)

    def _google_directions_coords(self, origin_coord, destination_coord, mode):
        key = os.environ.get("GOOGLE_MAPS_API_KEY") or os.environ.get("GOOGLE_DIRECTIONS_API_KEY")
        if not key:
            return None

        if not origin_coord or not destination_coord:
            return None

        query = urllib.parse.urlencode(
            {
                "origin": f"{origin_coord[0]},{origin_coord[1]}",
                "destination": f"{destination_coord[0]},{destination_coord[1]}",
                "mode": mode,
                "language": "ko",
                "key": key,
            }
        )
        url = f"https://maps.googleapis.com/maps/api/directions/json?{query}"
        try:
            with urllib.request.urlopen(url, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception:
            return None

        if data.get("status") != "OK":
            return None
        routes = data.get("routes") or []
        legs = routes[0].get("legs") if routes else []
        if not legs:
            return None
        leg = legs[0]
        duration = leg.get("duration", {}).get("value")
        distance = leg.get("distance", {}).get("value")
        if duration is None or distance is None:
            return None
        return {
            "status": "ok",
            "duration_minutes": max(1, round(float(duration) / 60)),
            "distance_meters": int(distance),
            "mode": mode,
            "source": "google_directions",
        }

    def _estimated_directions(self, origin, destination, mode):
        origin_coord = self._coord(origin)
        destination_coord = self._coord(destination)
        if not origin_coord or not destination_coord:
            return {
                "status": "not_available",
                "duration_minutes": None,
                "distance_meters": None,
                "mode": mode,
                "message": "좌표가 없어 이동시간을 계산하지 못했습니다.",
            }

        return self._estimated_directions_coords(origin_coord, destination_coord, mode)

    def _estimated_directions_coords(self, origin_coord, destination_coord, mode):
        km = self._distance_km(origin_coord[0], origin_coord[1], destination_coord[0], destination_coord[1])
        speed_kmh = {"walking": 4.5, "transit": 25, "driving": 35}.get(mode, 4.5)
        minutes = max(1, round((km / speed_kmh) * 60))
        return {
            "status": "estimated",
            "duration_minutes": minutes,
            "distance_meters": int(round(km * 1000)),
            "mode": mode,
            "source": "haversine_fallback",
            "message": "Google Directions 조회 실패 또는 키 미설정으로 직선거리 기반 예상값을 사용했습니다.",
        }

    def _coord(self, row):
        lat = self._float(row.get("latitude"))
        lng = self._float(row.get("longitude"))
        if lat is None or lng is None:
            return None
        return lat, lng

    def _distance_km(self, lat1, lng1, lat2, lng2):
        radius = 6371
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlng / 2) ** 2
        )
        return radius * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

    def _blocks_keyword_relax(self, keyword):
        text = self._clean(keyword, 80)
        return any(token in text for token in self.SPECIFIC_NO_RELAX_KEYWORDS)

    def _tokens(self, value):
        text = self._clean(value, 120)
        if not text:
            return []
        return [token for token in re.split(r"\s+", text) if token]

    def _list(self, value):
        if isinstance(value, list):
            return [self._clean(item, 80) for item in value if self._clean(item, 80)]
        if value in [None, ""]:
            return []
        return [self._clean(value, 80)]

    def _clean(self, value, limit=120):
        text = re.sub(r"<[^>]*>", " ", str(value or ""))
        text = text.replace("&nbsp;", " ")
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > limit:
            return text[:limit].rstrip()
        return text

    def _int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default

    def _float(self, value):
        if value in [None, ""]:
            return None
        try:
            return float(value)
        except Exception:
            return None


Model = AiTools()
