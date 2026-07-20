import copy
import datetime
import math
import re
import time


Types = wiz.model("ai_harness/types")


class TravelItineraryEngine:
    CATEGORY_ORDER = ["관광지", "음식점", "카페", "음식점", "야경"]
    VISIT_MINUTES = {
        "음식점": 75,
        "카페": 60,
        "관광지": 90,
        "자연": 90,
        "문화시설": 90,
        "야경": 75,
        "쇼핑": 75,
        "레포츠": 120,
    }
    MODE_MAP = {"대중교통": "transit", "자동차": "driving", "도보": "walking"}

    def __init__(self, tools):
        self.tools = tools

    def generate(self, state):
        started = time.monotonic()
        days = max(1, min(int(state.get("days") or 1), 14))
        excluded = set(state.get("collected_place_ids") or [])
        categories = self._categories(state)
        pools = {}
        tool_logs = []
        warnings = []
        relaxations = []
        must_visit_results = []

        for keyword in state.get("must_visit_places") or []:
            results, logs, attempts = self._search(state, "관광지", 3, excluded, keyword_override=keyword)
            tool_logs.extend(logs)
            relaxations.extend(attempts)
            candidate = next((row for row in results if str(row.get("place_id") or "") not in excluded), None)
            if candidate:
                must_visit_results.append(dict(candidate, requested_category="관광지"))
                excluded.add(str(candidate.get("place_id") or ""))
            else:
                warnings.append(f"필수 방문 장소 '{keyword}' 검색 결과 부족")

        for category in list(dict.fromkeys(categories)):
            needed = max(days * categories.count(category) * 2, days + 2)
            results, logs, attempts = self._search(state, category, needed, excluded)
            pools[category] = results
            tool_logs.extend(logs)
            relaxations.extend(attempts)
            if not results:
                warnings.append(f"{category} 검색 결과 부족")

        itinerary_days = []
        used = set(excluded)
        previous_anchor = None
        for day_index in range(days):
            selected = []
            if day_index < len(must_visit_results):
                required_place = must_visit_results[day_index]
                selected.append(required_place)
                used.add(str(required_place.get("place_id") or ""))
                previous_anchor = self._coord(required_place) or previous_anchor
            for category in categories[:4]:
                if len(selected) >= 4:
                    break
                candidate = self._pick_nearest(pools.get(category, []), used, previous_anchor)
                if candidate is None:
                    candidate = self._pick_from_similar(pools, category, used, previous_anchor)
                if candidate is None:
                    continue
                selected.append(dict(candidate, requested_category=category))
                used.add(str(candidate.get("place_id") or ""))
                previous_anchor = self._coord(candidate) or previous_anchor

            if len(selected) < 2:
                warnings.append(f"{day_index + 1}일차 장소 검색 결과 부족")
                continue
            day, route_logs, route_warnings = self._assemble_day(state, day_index, days, selected)
            tool_logs.extend(route_logs)
            warnings.extend(route_warnings)
            itinerary_days.append(day)

        if len(itinerary_days) != days:
            return {
                "ok": False,
                "failure_stage": "place_search",
                "message": "요청한 모든 날짜에 넣을 실제 장소를 충분히 찾지 못했어요. 지역이나 취향 범위를 조금 넓혀주세요.",
                "warnings": self._unique(warnings or ["장소 검색 결과 부족"]),
                "tool_logs": tool_logs,
                "metadata": {"relaxations": relaxations, "elapsed_ms": self._ms(started)},
            }

        draft = {
            "title": f"{state.get('region') or '여행'} {days}일 코스",
            "region": state.get("region") or "",
            "days": itinerary_days,
            "transport": state.get("transport") or "대중교통",
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metadata": {
                "source": "deterministic_places_engine",
                "relaxations": relaxations,
                "elapsed_ms": self._ms(started),
            },
        }
        return {
            "ok": True,
            "draft": draft,
            "warnings": self._unique(warnings),
            "tool_logs": tool_logs,
            "metadata": draft["metadata"],
        }

    def revise(self, state, prompt, intent):
        draft = copy.deepcopy(state.get("itinerary_draft") or {})
        days = draft.get("days") if isinstance(draft.get("days"), list) else []
        if not days:
            return self.generate(state)
        requested_days = max(1, int(state.get("days") or len(days)))
        if requested_days != len(days):
            regenerated_state = copy.deepcopy(state)
            regenerated_state["collected_place_ids"] = []
            return self.generate(regenerated_state)

        target_day = self._target_day(prompt, len(days))
        day_indexes = [target_day] if target_day is not None else list(range(len(days)))
        category = self._category_from_prompt(prompt)
        changed = False

        if intent == "remove_place":
            for index in day_indexes:
                before = list(days[index].get("places") or [])
                days[index]["places"] = [place for place in before if not self._matches_remove(place, prompt, category)]
                changed = changed or len(before) != len(days[index]["places"])
        elif intent == "revise_course" and "너무 많" in prompt:
            for index in day_indexes:
                places = list(days[index].get("places") or [])
                if len(places) > 3:
                    days[index]["places"] = places[:3]
                    changed = True
        elif intent in ["replace_place", "add_place"]:
            index = target_day if target_day is not None else 0
            places = list(days[index].get("places") or [])
            replace_index = self._find_place_index(places, prompt, category) if intent == "replace_place" else len(places)
            excludes = set(state.get("collected_place_ids") or [])
            excludes.update(str(place.get("place_id") or "") for day in days for place in day.get("places") or [])
            requested_name = self._place_name_from_prompt(prompt)
            results, logs, attempts = self._search(
                state,
                category or "관광지",
                3,
                excludes,
                keyword_override=requested_name,
            )
            if not results:
                return {
                    "ok": False,
                    "failure_stage": "place_search",
                    "message": "교체할 실제 장소를 찾지 못했어요. 다른 카테고리나 지역을 알려주세요.",
                    "warnings": ["대체 장소 검색 결과 부족"],
                    "tool_logs": logs,
                    "metadata": {"relaxations": attempts},
                }
            new_place = dict(results[0], requested_category=category or results[0].get("category") or "관광지")
            if intent == "replace_place" and 0 <= replace_index < len(places):
                places[replace_index] = new_place
            else:
                places.append(new_place)
            days[index]["places"] = places
            changed = True

        if intent == "change_schedule" or state.get("transport") != draft.get("transport"):
            changed = True

        if not changed:
            return {
                "ok": False,
                "failure_stage": "revision_target",
                "message": "수정할 날짜나 장소를 찾지 못했어요. 예: ‘둘째 날 카페를 바꿔줘’처럼 말해주세요.",
                "warnings": ["수정 대상 불명확"],
                "tool_logs": [],
                "metadata": {},
            }

        rebuilt_days = []
        all_logs = []
        warnings = []
        for index, day in enumerate(days):
            raw_places = [self._place_from_draft(place) for place in day.get("places") or []]
            rebuilt, logs, day_warnings = self._assemble_day(state, index, len(days), raw_places)
            rebuilt_days.append(rebuilt)
            all_logs.extend(logs)
            warnings.extend(day_warnings)
        draft["days"] = rebuilt_days
        draft["transport"] = state.get("transport") or "대중교통"
        draft["generated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draft.setdefault("metadata", {})["revision"] = intent
        return {"ok": True, "draft": draft, "warnings": self._unique(warnings), "tool_logs": all_logs, "metadata": draft["metadata"]}

    def _search(self, state, category, limit, excludes, keyword_override=""):
        region = str(state.get("region") or "").strip()
        preferences = list(state.get("preferences") or [])
        keyword = str(keyword_override or "").strip() or self._keyword(category, preferences)
        mood_tags = [item for item in preferences if item not in ["맛집", "카페"]]
        regions = [region]
        parent = self._parent_region(region)
        if parent and parent != region:
            regions.append(parent)
        logs = []
        attempts = []
        for search_region in regions:
            args = {
                "region": search_region,
                "category": category,
                "keyword": keyword,
                "mood_tags": mood_tags,
                "exclude_place_ids": list(excludes),
                "limit": min(10, max(1, int(limit))),
            }
            data = self.tools.execute_place_search(args)
            logs.append(self._tool_log("place_search", args, data, len(logs)))
            attempts.append({
                "category": category,
                "region": search_region,
                "status": data.get("status", "error"),
                "relaxation": data.get("relaxation", ""),
            })
            rows = [
                row for row in data.get("results", []) or []
                if str(row.get("place_id") or "").strip()
                and str(row.get("place_id") or "") not in excludes
            ]
            if rows:
                return rows, logs, attempts
        return [], logs, attempts

    def _assemble_day(self, state, day_index, total_days, selected):
        mode = self.MODE_MAP.get(state.get("transport"), "transit")
        start = state.get("arrival_time") if day_index == 0 else "10:00"
        end = state.get("departure_time") if day_index == total_days - 1 else "21:00"
        cursor = self._minutes(start or "10:00", 600)
        end_minutes = self._minutes(end or "21:00", 1260)
        places = []
        logs = []
        warnings = []
        previous = None
        total_distance = 0
        total_move = 0

        for index, place in enumerate(selected):
            move = None
            if previous is not None:
                args = {
                    "origin_place_id": previous.get("place_id", ""),
                    "destination_place_id": place.get("place_id", ""),
                    "mode": mode,
                }
                move = self.tools.execute_directions_lookup(args)
                logs.append(self._tool_log("directions_lookup", args, move, len(logs)))
                duration = move.get("duration_minutes")
                if duration is None:
                    duration = self._fallback_minutes(previous, place, mode)
                    move = dict(move or {})
                    move["duration_minutes"] = duration
                    move["distance_meters"] = self._distance_meters(previous, place)
                    move["source"] = "haversine_fallback"
                    warnings.append("이동 경로 계산 실패로 직선거리 예상값 사용")
                if move.get("status") != "ok":
                    warnings.append("일부 이동시간은 예상값")
                cursor += int(duration or 0)
                total_move += int(duration or 0)
                total_distance += int(move.get("distance_meters") or self._distance_meters(previous, place))

            category = str(place.get("requested_category") or place.get("category") or "관광지")
            visit_minutes = self.VISIT_MINUTES.get(category, 75)
            cursor, opening_warning = self._apply_opening_hours(cursor, place.get("usage_time"))
            if opening_warning:
                warnings.append(f"{place.get('name') or '장소'}: {opening_warning}")
            if cursor + visit_minutes > end_minutes and len(places) >= 2:
                warnings.append(f"{day_index + 1}일차 출발 시간 제약으로 마지막 장소 제외")
                break
            row = {
                "place_id": str(place.get("place_id") or ""),
                "name": str(place.get("name") or ""),
                "category": category,
                "address": str(place.get("address") or ""),
                "lat": place.get("lat"),
                "lng": place.get("lng"),
                "thumbnail": str(place.get("thumbnail") or ""),
                "usage_time": str(place.get("usage_time") or ""),
                "rest_date": str(place.get("rest_date") or ""),
                "time": self._clock(cursor),
                "duration_minutes": visit_minutes,
                "activity": self._activity(category),
                "move_from_previous": self._move_payload(move, mode),
            }
            places.append(row)
            cursor += visit_minutes
            previous = place

        return {
            "day": day_index + 1,
            "label": f"{day_index + 1}일차",
            "date": self._day_date(state.get("start_date"), day_index),
            "start_time": start or "10:00",
            "end_time": self._clock(min(cursor, end_minutes)),
            "places": places,
            "total_move_minutes": total_move,
            "total_distance_meters": total_distance,
        }, logs, warnings

    def _categories(self, state):
        preferences = set(state.get("preferences") or [])
        excluded = set(state.get("excluded_preferences") or [])
        first = "자연" if preferences.intersection({"바다", "자연"}) else ("문화시설" if "문화" in preferences else "관광지")
        third = "카페" if "카페" in preferences and "카페" not in excluded else "관광지"
        fourth = "야경" if "야경" in preferences and "야경" not in excluded else "음식점"
        categories = [first, "음식점", third, fourth]
        return [category for category in categories if not (category == "카페" and "카페" in excluded)]

    def _pick_nearest(self, rows, used, anchor):
        candidates = [row for row in rows if str(row.get("place_id") or "") not in used]
        if not candidates:
            return None
        if anchor is None:
            return candidates[0]
        return min(candidates, key=lambda row: self._coord_distance(anchor, self._coord(row)))

    def _pick_from_similar(self, pools, category, used, anchor):
        alternatives = {
            "카페": ["관광지", "문화시설"],
            "야경": ["관광지", "자연"],
            "자연": ["관광지"],
            "문화시설": ["관광지"],
            "음식점": [],
        }
        for candidate_category in alternatives.get(category, ["관광지"]):
            place = self._pick_nearest(pools.get(candidate_category, []), used, anchor)
            if place is not None:
                return place
        return None

    def _category_from_prompt(self, prompt):
        text = str(prompt or "")
        if "카페" in text:
            return "카페"
        if any(token in text for token in ["맛집", "음식점", "식당", "점심", "저녁"]):
            return "음식점"
        if any(token in text for token in ["바다", "자연", "공원", "해변"]):
            return "자연"
        if any(token in text for token in ["문화", "박물관", "미술관"]):
            return "문화시설"
        if "야경" in text:
            return "야경"
        return "관광지"

    def _place_name_from_prompt(self, prompt):
        text = str(prompt or "")
        match = re.search(
            r"(?:(?:첫째|둘째|셋째)\s*날|\d+일차)?\s*([가-힣A-Za-z0-9 ]{2,30}?)(?:을|를)?\s*"
            r"(?:넣어줘|넣어 줘|추가해줘|추가해 줘|다른 곳으로 바꿔줘)",
            text,
        )
        if not match:
            return ""
        value = match.group(1).strip()
        return "" if value in ["장소", "카페", "맛집", "관광지"] else value

    def _target_day(self, prompt, total):
        text = str(prompt or "")
        mapping = {"첫째": 0, "첫날": 0, "1일차": 0, "둘째": 1, "둘째 날": 1, "2일차": 1, "셋째": 2, "3일차": 2}
        for token, index in mapping.items():
            if token in text and index < total:
                return index
        match = re.search(r"(\d+)\s*일차", text)
        if match:
            return max(0, min(int(match.group(1)) - 1, total - 1))
        return None

    def _matches_remove(self, place, prompt, category):
        if str(place.get("name") or "") in str(prompt or ""):
            return True
        return bool(category and str(place.get("category") or "") == category)

    def _find_place_index(self, places, prompt, category):
        for index, place in enumerate(places):
            if str(place.get("name") or "") in str(prompt or ""):
                return index
        for index, place in enumerate(places):
            if str(place.get("category") or "") == category:
                return index
        return 0 if places else -1

    def _place_from_draft(self, place):
        return {
            "place_id": place.get("place_id", ""),
            "name": place.get("name", ""),
            "category": place.get("category", ""),
            "requested_category": place.get("category", ""),
            "address": place.get("address", ""),
            "lat": place.get("lat"),
            "lng": place.get("lng"),
            "thumbnail": place.get("thumbnail", ""),
            "usage_time": place.get("usage_time", ""),
            "rest_date": place.get("rest_date", ""),
        }

    def _apply_opening_hours(self, cursor, usage_time):
        text = str(usage_time or "")
        match = re.search(r"(\d{1,2}):(\d{2})\s*(?:~|-|–)\s*(\d{1,2}):(\d{2})", text)
        if not match:
            return cursor, ""
        opens = int(match.group(1)) * 60 + int(match.group(2))
        closes = int(match.group(3)) * 60 + int(match.group(4))
        if closes <= opens:
            closes += 24 * 60
        if cursor < opens:
            return opens, "운영 시작시간에 맞춰 방문시간 조정"
        if cursor >= closes:
            return cursor, "표시된 운영시간 이후일 수 있어 확인 필요"
        return cursor, ""

    def _tool_log(self, name, arguments, data, iteration):
        return Types.ToolLog(
            call=Types.ToolCall(id=f"server-{name}-{iteration}", name=name, arguments=dict(arguments or {})),
            result=Types.ToolResult(status=str(data.get("status") or "ok"), data=dict(data or {})),
            iteration=iteration,
            duration_ms=0,
            phase="server_planner",
        )

    def _move_payload(self, move, mode):
        move = move or {}
        return {
            "mode": move.get("mode") or mode,
            "duration_minutes": move.get("duration_minutes"),
            "distance_meters": move.get("distance_meters"),
            "status": move.get("status") or ("start" if not move else "not_available"),
            "source": move.get("source") or "",
        }

    def _fallback_minutes(self, origin, destination, mode):
        km = self._distance_meters(origin, destination) / 1000.0
        speed = {"walking": 4.5, "transit": 25, "driving": 35}.get(mode, 25)
        return max(1, round(km / speed * 60))

    def _distance_meters(self, origin, destination):
        one = self._coord(origin)
        two = self._coord(destination)
        if not one or not two:
            return 0
        radius = 6371000
        dlat = math.radians(two[0] - one[0])
        dlng = math.radians(two[1] - one[1])
        value = math.sin(dlat / 2) ** 2 + math.cos(math.radians(one[0])) * math.cos(math.radians(two[0])) * math.sin(dlng / 2) ** 2
        return int(radius * 2 * math.atan2(math.sqrt(value), math.sqrt(max(0, 1 - value))))

    def _coord_distance(self, one, two):
        if not one or not two:
            return float("inf")
        return (one[0] - two[0]) ** 2 + (one[1] - two[1]) ** 2

    def _coord(self, row):
        try:
            return float(row.get("lat")), float(row.get("lng"))
        except Exception:
            return None

    def _keyword(self, category, preferences):
        relevant = [item for item in preferences if item not in ["카페", "맛집"]]
        if category == "음식점" and "맛집" in preferences:
            return "맛집"
        if category == "카페":
            return "카페"
        return relevant[0] if relevant else ""

    def _parent_region(self, region):
        tokens = str(region or "").split()
        return tokens[0] if len(tokens) > 1 else region

    def _activity(self, category):
        return {
            "음식점": "식사",
            "카페": "카페 휴식",
            "자연": "자연 산책",
            "문화시설": "문화 관람",
            "야경": "야경 감상",
            "쇼핑": "쇼핑",
        }.get(category, "여행지 둘러보기")

    def _minutes(self, value, default):
        try:
            hour, minute = str(value).split(":", 1)
            return int(hour) * 60 + int(minute)
        except Exception:
            return default

    def _clock(self, minutes):
        minutes = max(0, int(minutes or 0))
        return f"{(minutes // 60) % 24:02d}:{minutes % 60:02d}"

    def _day_date(self, start, offset):
        try:
            return (datetime.date.fromisoformat(start) + datetime.timedelta(days=offset)).isoformat()
        except Exception:
            return ""

    def _unique(self, values):
        rows = []
        for value in values or []:
            value = str(value or "").strip()
            if value and value not in rows:
                rows.append(value)
        return rows

    def _ms(self, started):
        return max(0, int((time.monotonic() - started) * 1000))


Model = TravelItineraryEngine
