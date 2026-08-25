import datetime
import hashlib
import json
import math
import os
import re
import threading
import time
import urllib.parse
import urllib.error
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
                "enum": [
                    "관광지", "자연", "전망대", "시장", "문화시설", "체험", "사진 명소",
                    "야경", "카페", "디저트", "맛집", "음식점", "숙박", "레포츠", "쇼핑",
                ],
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
        "전망대": ["12", "14"],
        "사진 명소": ["12", "14"],
        "야경": ["12", "14"],
        "문화시설": ["14"],
        "체험": ["14", "28"],
        "레포츠": ["28"],
        "숙박": ["32"],
        "시장": ["38", "39"],
        "쇼핑": ["38"],
        "카페": ["39"],
        "디저트": ["39"],
        "맛집": ["39"],
        "음식점": ["39"],
    }
    CAFE_KEYWORDS = ["카페", "커피", "로스터리", "베이커리", "브런치", "디저트", "라떼"]
    SPECIFIC_NO_RELAX_KEYWORDS = ["스키", "스키장", "눈썰매", "워터파크"]
    DIRECTION_TTL_SECONDS = 60 * 60 * 24
    TRANSIT_EXTERNAL_REQUEST_LIMIT = 8
    TRANSIT_PROVIDER_MIN_INTERVAL_SECONDS = 1.05
    _direction_cache = {}
    _transit_provider_lock = threading.Lock()
    _transit_last_request_at = 0.0
    def __init__(self):
        # wiz.model() creates a new Peewee model/database object. Reusing one
        # model per AI tools instance prevents a single itinerary request from
        # opening dozens of persistent MySQL connections.
        self._place_orm = None
        self._external_places = {}
        # Transit request budgets are isolated per itinerary generation.  A
        # process-global counter made every request after the first 24 calls
        # silently fall back to estimates until the worker restarted.
        self._transit_external_requests_by_scope = {}
        self._last_direction_provider_metric = {}

    def function_declarations(self):
        return [PLACE_SEARCH_DECLARATION, DIRECTIONS_LOOKUP_DECLARATION]

    def execute_place_search(self, input_data):
        data = input_data if isinstance(input_data, dict) else {}
        region = self._clean(data.get("region"), 80)
        category = self._clean(data.get("category"), 40)
        keyword = self._clean(data.get("keyword"), 80)
        exact_name = bool(data.get("exact_name"))
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
        if category in ["관광지", "문화시설", "쇼핑", "숙박"]:
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
                if exact_name:
                    rows = [
                        row for row in rows
                        if self._strong_name_match(keyword, row.get("name"))
                    ]
                if not rows:
                    continue
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
                    "candidate_diagnostics": self._candidate_diagnostics_from_rows(
                        rows, source="internal_database",
                    ),
                }

        if exact_name and keyword:
            external = self._tour_api_exact_place_search(region, keyword)
            external_provider = "tour_api_place_search"
            if not external:
                external = self._naver_exact_place_search(region, keyword)
                external_provider = "naver_place_search"
            if external:
                return {
                    "status": "ok",
                    "relaxation": "external_exact_name",
                    "query": {
                        "region": region, "category": category,
                        "keyword": keyword, "exact_name": True, "limit": limit,
                    },
                    "results": external[:limit],
                    "message": "정확한 장소명을 외부 장소 검색으로 확인했습니다.",
                    "external_requests": 1,
                    "external_successful_calls": 1,
                    "external_failed_calls": 0,
                    "external_retried_calls": 0,
                    "billing_external_requests": 0,
                    "external_provider": external_provider,
                    "candidate_diagnostics": self._candidate_diagnostics_from_rows(
                        external[:limit], source=external_provider,
                    ),
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
        result.update({
            "external_requests": 0,
            "external_successful_calls": 0,
            "external_failed_calls": 0,
            "external_retried_calls": 0,
            "candidate_diagnostics": self._empty_candidate_diagnostics("internal_database"),
        })
        return result

    def _strong_name_match(self, requested, candidate):
        query = re.sub(r"[^가-힣A-Za-z0-9]", "", str(requested or "")).lower()
        name = re.sub(r"[^가-힣A-Za-z0-9]", "", str(candidate or "")).lower()
        if not query or not name:
            return False
        if query == name:
            return True
        shorter, longer = min(len(query), len(name)), max(len(query), len(name))
        return len(query) >= 4 and (query in name or name in query) and shorter / longer >= 0.72

    def _tour_api_exact_place_search(self, region, keyword):
        api_key = self._project_env_value("TOUR_API_KEY")
        if not api_key:
            return []
        params = {
            "serviceKey": api_key,
            "MobileOS": "ETC",
            "MobileApp": "GACHI",
            "_type": "json",
            "numOfRows": 10,
            "pageNo": 1,
            "keyword": keyword,
        }
        request = urllib.request.Request(
            "https://apis.data.go.kr/B551011/KorService2/searchKeyword2?"
            + urllib.parse.urlencode(params),
            headers={"Accept": "application/json", "User-Agent": "GACHI-Travel/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            return []
        body = ((payload.get("response") or {}).get("body") or {}) if isinstance(payload, dict) else {}
        items = ((body.get("items") or {}).get("item") or []) if isinstance(body, dict) else []
        rows = []
        for item in items if isinstance(items, list) else []:
            name = self._clean(item.get("title"), 120)
            lat = self._float(item.get("mapy"))
            lng = self._float(item.get("mapx"))
            address = self._clean(
                " ".join(part for part in [item.get("addr1"), item.get("addr2")] if part), 180,
            )
            if (
                not self._strong_name_match(keyword, name)
                or lat is None or lng is None
                or (region and region not in address and not self._coordinate_in_named_region(region, lat, lng))
            ):
                continue
            provider_id = str(item.get("contentid") or "").strip()
            if not provider_id:
                continue
            external_id = f"tour-api-{provider_id}"
            row = {
                "place_id": external_id,
                "provider_place_id": provider_id,
                "place_provider": "tour_api",
                "name": name,
                "category": "관광지",
                "address": address,
                "lat": lat,
                "lng": lng,
                "rating": None,
                "review_count": 0,
                "thumbnail": self._clean(item.get("firstimage") or item.get("firstimage2"), 500),
                "opening_status": "영업시간 확인 필요",
                "tags": ["필수 방문"],
                "source": "tour_api_place_search",
            }
            self._external_places[external_id] = {
                **row, "id": external_id,
                "latitude": lat, "longitude": lng,
            }
            rows.append(row)
        return rows

    def _coordinate_in_named_region(self, region, lat, lng):
        bounds = {
            "서울": (37.413, 37.715, 126.734, 127.269),
            "제주": (33.05, 33.65, 126.05, 126.98),
            "부산": (34.95, 35.40, 128.75, 129.35),
        }
        key = next((name for name in bounds if name in str(region or "")), "")
        if not key:
            return True
        south, north, west, east = bounds[key]
        return south <= lat <= north and west <= lng <= east

    def _naver_exact_place_search(self, region, keyword):
        query = " ".join(part for part in [str(region or "").strip(), keyword] if part)
        try:
            url = "https://search.naver.com/search.naver?" + urllib.parse.urlencode({"query": query})
            request = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept-Language": "ko-KR,ko;q=0.9",
            })
            with urllib.request.urlopen(request, timeout=8) as response:
                source = response.read(8 * 1024 * 1024).decode("utf-8", errors="ignore")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
            return []

        rows = []
        seen = set()
        decoder = json.JSONDecoder()
        pattern = re.compile(r'"PlaceListBusinessesItem:([^"\\]+)":')
        for match in pattern.finditer(source):
            start = source.find("{", match.end())
            if start < 0:
                continue
            try:
                payload, _ = decoder.raw_decode(source[start:])
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            place_id = str(match.group(1) or "").strip()
            name = self._clean(payload.get("normalizedName") or payload.get("name"), 120)
            lat = self._float(payload.get("y"))
            lng = self._float(payload.get("x"))
            if (
                not place_id or place_id in seen or not name
                or lat is None or lng is None
                or not self._strong_name_match(keyword, name)
            ):
                continue
            seen.add(place_id)
            external_id = f"naver-place-{place_id}"
            address = self._clean(
                payload.get("roadAddress") or payload.get("fullAddress")
                or payload.get("address") or payload.get("commonAddress"), 180,
            )
            row = {
                "place_id": external_id,
                "provider_place_id": place_id,
                "place_provider": "naver_search",
                "name": name,
                "category": self._clean(payload.get("category"), 80) or "관광지",
                "address": address,
                "lat": lat,
                "lng": lng,
                "rating": None,
                "review_count": 0,
                "thumbnail": self._clean(payload.get("imageUrl"), 500),
                "opening_status": "영업시간 확인 필요",
                "tags": ["필수 방문"],
                "source": "naver_place_search",
            }
            self._external_places[external_id] = {
                **row, "id": external_id,
                "latitude": lat, "longitude": lng,
            }
            rows.append(row)
        return rows

    def _candidate_diagnostics_from_rows(self, rows, source):
        raw = set()
        coordinates = set()
        for row in rows or []:
            key = str(row.get("place_id") or row.get("id") or "")
            if not key:
                key = hashlib.sha1(str(sorted(row.items())).encode("utf-8")).hexdigest()
            raw.add(key)
            if self._float(row.get("lat", row.get("latitude"))) is not None and self._float(
                row.get("lng", row.get("longitude"))
            ) is not None:
                coordinates.add(key)
        return self._candidate_diagnostics_payload(source, raw, coordinates, raw, raw)

    def _empty_candidate_diagnostics(self, source):
        return self._candidate_diagnostics_payload(source, set(), set(), set(), set())

    def _candidate_diagnostics_payload(
        self, source, raw_keys, coordinate_keys, category_keys, returned_keys,
    ):
        return {
            "source": source,
            "raw_candidate_keys": sorted(raw_keys),
            "coordinate_validation_passed_keys": sorted(coordinate_keys),
            "category_validation_passed_keys": sorted(category_keys),
            "returned_candidate_keys": sorted(returned_keys),
            "raw_candidate_count": len(raw_keys),
            "coordinate_validation_passed_count": len(coordinate_keys),
            "category_validation_passed_count": len(category_keys),
            "returned_candidate_count": len(returned_keys),
        }

    def _project_env_value(self, *names):
        for name in names:
            value = str(os.environ.get(name) or "").strip()
            if value:
                return value
        try:
            source = wiz.project.fs().read(".env") or ""
        except Exception:
            return ""
        expected = set(names)
        for raw_line in source.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() not in expected:
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ["'", '"']:
                value = value[1:-1]
            if value:
                return value
        return ""

    def execute_directions_lookup(self, input_data):
        data = input_data if isinstance(input_data, dict) else {}
        origin_id = self._clean(data.get("origin_place_id"), 64)
        destination_id = self._clean(data.get("destination_place_id"), 64)
        mode = self._clean(data.get("mode"), 24) or "walking"
        if mode not in ["walking", "transit", "driving"]:
            mode = "walking"
        request_scope = self._clean(data.get("request_scope"), 96) or "legacy"

        cache_key = f"{origin_id}:{destination_id}:{mode}"
        cached = self._direction_cache.get(cache_key)
        now = time.time()
        cached_failure_scope = str((cached or {}).get("failure_scope") or "")
        cache_scope_matches = not cached_failure_scope or cached_failure_scope == request_scope
        if (
            cached and cache_scope_matches
            and now - cached.get("created_at", 0) < self.DIRECTION_TTL_SECONDS
        ):
            result = dict(cached["result"])
            result["cache"] = "hit"
            result.update({
                "external_requests": 0,
                "external_successful_calls": 0,
                "external_failed_calls": 0,
                "external_retried_calls": 0,
                "billing_external_requests": 0,
                "external_provider": str(result.get("external_provider") or "cache"),
            })
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

        self._last_direction_provider_metric = {}
        if mode == "transit":
            result = self._odsay_directions(origin, destination, request_scope)
        else:
            result = self._naver_directions(origin, destination, mode)
        provider_metric = dict(self._last_direction_provider_metric or {})
        external_succeeded = result is not None
        if result is None:
            result = self._estimated_directions(origin, destination, mode)
        attempted = int(provider_metric.get("http_requests") or 0)
        configured = bool(provider_metric.get("configured"))
        provider = str(provider_metric.get("provider") or "none")
        failure_code = str(provider_metric.get("failure_code") or "")
        if attempted and not external_succeeded and not failure_code:
            failure_code = "unspecified_provider_failure"
        if attempted and not external_succeeded:
            print(
                f"[travel_directions] provider={provider} status=failed "
                f"failure_code={failure_code}"
            )
        result.update({
            "external_requests": attempted,
            "external_successful_calls": 1 if external_succeeded else 0,
            "external_failed_calls": 1 if attempted and not external_succeeded else 0,
            "external_retried_calls": 0,
            "billing_external_requests": attempted,
            "external_provider": provider,
            "external_provider_configured": configured,
            "external_provider_skip_reason": str(provider_metric.get("skip_reason") or ""),
            "external_provider_failure_code": failure_code,
        })

        # A provider failure is useful as an in-request negative cache, but it
        # must not suppress provider retries for every itinerary for 24 hours.
        failure_scope = (
            request_scope
            if mode == "transit" and configured and not external_succeeded
            else ""
        )
        self._direction_cache[cache_key] = {
            "created_at": now, "result": result, "failure_scope": failure_scope,
        }
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

        result = self._naver_directions_coords(origin_coord, destination_coord, mode)
        if result is None:
            result = self._estimated_directions_coords(origin_coord, destination_coord, mode)

        self._direction_cache[cache_key] = {"created_at": now, "result": result}
        return dict(result, cache="miss")

    def _place_db(self):
        if self._place_orm is None:
            self._place_orm = wiz.model("portal/season/orm").use("place").orm
        return self._place_orm

    def _get_place(self, place_id):
        if not place_id:
            return None
        cached = self._external_places.get(place_id)
        if cached:
            return dict(cached)
        try:
            db = self._place_db()
            row = db.get_or_none(db.id == place_id)
            return dict(row.__data__) if row else None
        except Exception:
            return None

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
            .order_by(db.provider_rating.desc(), db.provider_user_ratings_total.desc(), db.updated.desc())
            .limit(300)
            .dicts()
        ):
            value = dict(row)
            if not self._is_low_quality_candidate(value, category):
                rows.append(value)

        rows.sort(key=self._score, reverse=True)
        return [self._normalize_place(row, category) for row in rows[:limit]]

    def _is_low_quality_candidate(self, row, category):
        name = self._clean(row.get("name"), 120)
        if category in ["음식점", "맛집"]:
            return any(token in name for token in [
                "박물관", "미술관", "전시관", "기념관", "공원", "전망대", "수목원",
            ])
        if category in ["카페", "디저트"]:
            has_cafe_word = any(token in name for token in self.CAFE_KEYWORDS)
            return not has_cafe_word and any(token in name for token in [
                "박물관", "미술관", "전시관", "기념관", "공원", "전망대", "수목원",
            ])
        if category not in ["관광지", "자연", "전망대", "문화시설", "체험", "사진 명소", "야경"]:
            return False
        blocked = ["화장실", "주차장", "사우나", "모텔", "편의점", "관리사무소", "매표소"]
        return any(token in name for token in blocked)

    def _region_condition(self, db, region):
        tokens = self._tokens(region)
        if not tokens:
            return None

        condition = None
        for token in tokens:
            token_condition = self._keyword_condition(
                db,
                [token],
                fields=["area", "address"],
            )
            if token_condition is None:
                continue
            condition = token_condition if condition is None else condition & token_condition
        return condition

    def _category_condition(self, db, category):
        content_type_ids = self.CATEGORY_CONTENT_TYPES.get(category, [])
        condition = db.content_type_id.in_(content_type_ids) if content_type_ids else None
        if category in ["카페", "디저트"]:
            include = self._keyword_condition(db, self.CAFE_KEYWORDS)
            condition = include if condition is None else condition & include
            if category == "디저트":
                dessert = self._keyword_condition(db, ["디저트", "베이커리", "빵", "케이크", "아이스크림"])
                condition = condition & dessert if dessert is not None else condition
        elif category in ["음식점", "맛집"]:
            exclude = self._keyword_condition(db, self.CAFE_KEYWORDS)
            if exclude is not None:
                condition = condition & (~exclude) if condition is not None else ~exclude
        elif category == "야경":
            night = self._keyword_condition(db, ["야경", "밤", "전망", "스카이", "타워"], fields=["name", "category", "description", "overview"])
            if night is not None:
                condition = condition & night if condition is not None else night
        elif category == "자연":
            nature = self._keyword_condition(db, ["공원", "해변", "바다", "산책", "수목원", "숲", "섬", "호수", "계곡"], fields=["name", "category", "description", "overview"])
            if nature is not None:
                condition = condition & nature if condition is not None else nature
        elif category == "전망대":
            view = self._keyword_condition(db, ["전망", "스카이", "타워", "전망대", "케이블카"], fields=["name", "category", "description", "overview"])
            if view is not None:
                condition = condition & view if condition is not None else view
        elif category == "사진 명소":
            photo = self._keyword_condition(db, ["포토", "사진", "벽화", "해변", "정원", "전망", "촬영지"], fields=["name", "category", "description", "overview"])
            if photo is not None:
                condition = condition & photo if condition is not None else photo
        elif category == "시장":
            market = self._keyword_condition(db, ["시장", "마켓", "상가", "먹거리"], fields=["name", "category", "description", "overview"])
            if market is not None:
                condition = condition & market if condition is not None else market
        elif category == "체험":
            experience = self._keyword_condition(db, ["체험", "공방", "클래스", "박물관", "아쿠아리움", "레포츠"], fields=["name", "category", "description", "overview"])
            if experience is not None:
                condition = condition & experience if condition is not None else experience
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
        rating = self._float(row.get("provider_rating"))
        category = self._refine_category(row, requested_category or row.get("category", ""))
        tags = self._place_tags(row, category)
        return {
            "place_id": row.get("id", ""),
            "name": row.get("name", ""),
            "category": category,
            "address": row.get("address", "") or row.get("area", ""),
            "lat": self._float(row.get("latitude")),
            "lng": self._float(row.get("longitude")),
            "rating": round(rating, 1) if rating is not None else None,
            "review_count": self._int(row.get("provider_user_ratings_total"), 0),
            "thumbnail": row.get("image") or row.get("first_image2") or "",
            "overview_summary": self._summary(row),
            "usage_time": row.get("usage_time") or "",
            "rest_date": row.get("rest_date") or "",
            "opening_status": "영업시간 확인 필요" if not row.get("usage_time") else "운영시간 제공",
            "tags": tags,
            "representative_menu": self._representative_menu(row, category),
            "estimated_cost": self._estimated_cost(category),
            "admin_area": self._admin_area(row.get("address") or row.get("area") or ""),
        }

    def _refine_category(self, row, requested_category):
        text = self._clean(" ".join([
            str(row.get("name") or ""), str(row.get("category") or ""),
            str(row.get("description") or ""), str(row.get("overview") or ""),
        ]), 500)
        if any(token in text for token in ["미술관", "박물관", "전시관", "문화센터", "기념관"]):
            return "문화시설"
        if any(token in text for token in ["전망대", "스카이", "타워"]):
            return "전망대" if requested_category != "야경" else "야경"
        if any(token in text for token in ["시장", "마켓"]):
            return "시장"
        return requested_category

    def _place_tags(self, row, category):
        text = self._clean(" ".join([
            str(row.get("name") or ""), str(row.get("category") or ""),
            str(row.get("description") or ""), str(row.get("overview") or ""),
        ]), 500)
        tags = []
        rules = [
            ("오션뷰", ["바다", "해변", "오션", "해안"]),
            ("사진명소", ["포토", "사진", "전망", "야경", "벽화"]),
            ("데이트", ["감성", "로맨틱", "야경", "카페"]),
            ("가족추천", ["가족", "아이", "공원", "박물관", "체험"]),
            ("로컬추천", ["시장", "향토", "전통", "골목"]),
            ("실내", ["박물관", "미술관", "아쿠아리움", "전시", "공방"]),
        ]
        for label, keywords in rules:
            if any(keyword in text for keyword in keywords):
                tags.append(label)
        if category and category not in tags:
            tags.append(category)
        return tags[:4]

    def _representative_menu(self, row, category):
        if category not in ["음식점", "맛집", "카페", "디저트", "시장"]:
            return ""
        text = self._clean(row.get("detail_intro") or row.get("overview") or row.get("description"), 800)
        match = re.search(r"(?:대표\s*메뉴|메뉴|취급\s*메뉴)\s*[:：]?\s*([^/|,\\n]{2,40})", text)
        if match:
            return self._clean(match.group(1), 40)
        defaults = {"카페": "커피", "디저트": "시그니처 디저트", "시장": "지역 먹거리"}
        return defaults.get(category, "대표 메뉴 확인")

    def _estimated_cost(self, category):
        return {
            "음식점": 18000, "맛집": 20000, "카페": 9000, "디저트": 8000,
            "시장": 15000, "체험": 25000, "레포츠": 35000, "문화시설": 10000,
            "전망대": 12000,
        }.get(category, 0)

    def _admin_area(self, address):
        tokens = self._clean(address, 120).split()
        for token in tokens:
            if token.endswith(("구", "군", "읍", "면", "동")):
                return token
        for token in tokens:
            if token.endswith("시"):
                return token
        return tokens[1] if len(tokens) > 1 else (tokens[0] if tokens else "")

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
        rating = self._float(row.get("provider_rating"))
        rating_value = rating if rating is not None else -1
        image_value = 1 if row.get("image") or row.get("first_image2") else 0
        return (
            1 if rating is not None else 0,
            rating_value,
            self._int(row.get("provider_user_ratings_total"), 0),
            image_value,
            str(row.get("updated", "")),
        )

    def _naver_directions(self, origin, destination, mode):
        origin_coord = self._coord(origin)
        destination_coord = self._coord(destination)
        return self._naver_directions_coords(origin_coord, destination_coord, mode)

    def _naver_directions_coords(self, origin_coord, destination_coord, mode):
        client_id = self._project_env_value("NAVER_MAPS_CLIENT_ID", "NCP_MAPS_CLIENT_ID")
        client_secret = self._project_env_value("NAVER_MAPS_CLIENT_SECRET", "NCP_MAPS_CLIENT_SECRET")
        self._last_direction_provider_metric = {
            "provider": "naver_directions",
            "configured": bool(client_id and client_secret),
            "http_requests": 0,
        }
        if not client_id or not client_secret or mode != "driving":
            self._last_direction_provider_metric["skip_reason"] = (
                "unsupported_mode" if mode != "driving" else "provider_not_configured"
            )
            return None

        if not origin_coord or not destination_coord:
            self._last_direction_provider_metric["skip_reason"] = "missing_coordinates"
            return None

        query = urllib.parse.urlencode(
            {
                "start": f"{origin_coord[1]},{origin_coord[0]}",
                "goal": f"{destination_coord[1]},{destination_coord[0]}",
                "option": "traoptimal",
                "lang": "ko",
            }
        )
        url = f"https://maps.apigw.ntruss.com/map-direction/v1/driving?{query}"
        request = urllib.request.Request(url, headers={
            "x-ncp-apigw-api-key-id": client_id,
            "x-ncp-apigw-api-key": client_secret,
            "Accept": "application/json",
        })
        self._last_direction_provider_metric["http_requests"] = 1
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception:
            return None

        if int(data.get("code", -1)) != 0:
            return None
        routes = (data.get("route") or {}).get("traoptimal") or []
        summary = routes[0].get("summary") if routes else None
        if not summary:
            return None
        duration = summary.get("duration")
        distance = summary.get("distance")
        if duration is None or distance is None:
            return None
        return {
            "status": "ok",
            "duration_minutes": max(1, round(float(duration) / 60000)),
            "distance_meters": int(distance),
            "mode": mode,
            "source": "naver_directions",
        }

    def _odsay_directions(self, origin, destination, request_scope="legacy"):
        return self._odsay_directions_coords(
            self._coord(origin), self._coord(destination), request_scope,
        )

    def _odsay_directions_coords(self, origin_coord, destination_coord, request_scope="legacy"):
        api_key = self._project_env_value("ODSAY_API_KEY")
        self._last_direction_provider_metric = {
            "provider": "odsay_transit",
            "configured": bool(api_key),
            "http_requests": 0,
        }
        if not api_key:
            self._last_direction_provider_metric["skip_reason"] = "provider_not_configured"
            return None
        if not origin_coord or not destination_coord:
            self._last_direction_provider_metric["skip_reason"] = "missing_coordinates"
            return None
        request_scope = self._clean(request_scope, 96) or "legacy"
        scoped_requests = int(
            self._transit_external_requests_by_scope.get(request_scope) or 0
        )
        if scoped_requests >= self.TRANSIT_EXTERNAL_REQUEST_LIMIT:
            self._last_direction_provider_metric["skip_reason"] = "request_budget_exhausted"
            return None

        query = urllib.parse.urlencode({
            "SX": origin_coord[1], "SY": origin_coord[0],
            "EX": destination_coord[1], "EY": destination_coord[0],
            "OPT": 0, "SearchType": 0, "SearchPathType": 0,
            "apiKey": api_key,
        })
        request = urllib.request.Request(
            "https://api.odsay.com/v1/api/searchPubTransPathT?{}".format(query),
            headers={
                "Accept": "application/json",
                "User-Agent": "GACHI-Travel/1.0",
                "Origin": "https://travel.wizide.com",
                "Referer": "https://travel.wizide.com/",
            },
            method="GET",
        )
        self._transit_external_requests_by_scope[request_scope] = scoped_requests + 1
        if len(self._transit_external_requests_by_scope) > 128:
            oldest_scope = next(iter(self._transit_external_requests_by_scope))
            if oldest_scope != request_scope:
                self._transit_external_requests_by_scope.pop(oldest_scope, None)
        self._last_direction_provider_metric["http_requests"] = 1
        try:
            # ODsay rejects burst traffic with HTTP 400.  Serialize billable
            # calls across requests and honor its observed one-call-per-second
            # boundary so provider failures are not mistaken for no routes.
            with self._transit_provider_lock:
                wait_seconds = self.TRANSIT_PROVIDER_MIN_INTERVAL_SECONDS - (
                    time.monotonic() - self._transit_last_request_at
                )
                if wait_seconds > 0:
                    time.sleep(wait_seconds)
                self._transit_last_request_at = time.monotonic()
                with urllib.request.urlopen(request, timeout=8) as response:
                    payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            provider_code = ""
            try:
                error_payload = json.loads(error.read().decode("utf-8"))
                provider_code = str((error_payload.get("error") or {}).get("code") or "")
            except Exception:
                provider_code = ""
            self._last_direction_provider_metric["failure_code"] = (
                f"provider_{provider_code}" if provider_code else f"http_{error.code}"
            )
            return None
        except (urllib.error.URLError, TimeoutError):
            self._last_direction_provider_metric["failure_code"] = "network_or_timeout"
            return None
        except (ValueError, json.JSONDecodeError):
            self._last_direction_provider_metric["failure_code"] = "invalid_json"
            return None
        paths = ((payload.get("result") or {}).get("path") or []) if isinstance(payload, dict) else []
        info = (paths[0].get("info") or {}) if paths else {}
        # ODsay returns totalDistance as a JSON float (for example 2329.0).
        # int("2329.0") previously converted valid routes into failures.
        duration = int(round(self._float(info.get("totalTime")) or 0))
        distance = int(round(self._float(info.get("totalDistance")) or 0))
        if duration <= 0 or distance <= 0:
            error = payload.get("error") if isinstance(payload, dict) else {}
            provider_code = error.get("code") if isinstance(error, dict) else ""
            self._last_direction_provider_metric["failure_code"] = (
                f"provider_{provider_code}" if provider_code else "route_not_found"
            )
            return None
        return {
            "status": "ok",
            "duration_minutes": duration,
            "distance_meters": distance,
            "mode": "transit",
            "source": "odsay_transit",
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
            "message": "NAVER Directions 조회 실패 또는 지원하지 않는 이동수단이라 직선거리 기반 예상값을 사용했습니다.",
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
