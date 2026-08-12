import copy
import datetime
import math
import re
import time


Types = wiz.model("ai_harness/types")


class TravelItineraryEngine:
    EASY_ROUTE_POLICY_PROMPT = (
        "가까운 장소를 같은 권역으로 묶고, 다음 일정 위치까지 미리 고려해 "
        "왕복·지그재그·불필요한 우회를 줄인 한 방향의 쉬운 동선으로 구성한다."
    )
    ROUTE_LOOKAHEAD_WEIGHT = 0.65
    ROUTE_BACKTRACK_WEIGHT = 4.0
    CATEGORY_ORDER = [
        "관광지", "자연", "전망대", "시장", "문화시설", "체험", "사진 명소",
        "야경", "카페", "디저트", "맛집", "음식점", "쇼핑",
    ]
    VISIT_MINUTES = {
        "음식점": 75,
        "맛집": 75,
        "카페": 60,
        "디저트": 50,
        "관광지": 90,
        "자연": 90,
        "전망대": 70,
        "시장": 90,
        "문화시설": 90,
        "체험": 120,
        "사진 명소": 60,
        "야경": 75,
        "쇼핑": 75,
        "레포츠": 120,
    }
    MODE_MAP = {"대중교통": "transit", "자동차": "driving", "도보": "walking"}
    MAX_LEG_MINUTES = {"walking": 15, "transit": 30, "driving": 40}
    MAX_DAY_DISTANCE_METERS = {"walking": 10000, "transit": 35000, "driving": 60000}
    MAX_DAY_MOVE_MINUTES = {"walking": 90, "transit": 150, "driving": 180}
    REQUIRED_SCHEDULE_SLOTS = [
        "breakfast", "morning_attraction", "lunch", "afternoon_cafe",
        "afternoon_activity", "dinner", "evening_activity",
    ]
    CATEGORY_GROUP = {
        "음식점": "food", "맛집": "food", "시장": "market", "카페": "cafe", "디저트": "cafe",
        "관광지": "sight", "자연": "nature", "전망대": "view", "사진 명소": "photo",
        "문화시설": "culture", "체험": "experience", "레포츠": "experience", "야경": "night",
        "쇼핑": "shopping",
    }

    def __init__(self, tools):
        self.tools = tools

    def generate(self, state):
        started = time.monotonic()
        days = max(1, min(int(state.get("days") or 1), 14))
        excluded = set(state.get("collected_place_ids") or [])
        day_plans = [self._day_plan(state, index, days) for index in range(days)]
        categories = [category for plan in day_plans for category in plan.get("categories") or []]
        pools = {}
        tool_logs = []
        warnings = []
        relaxations = []
        shortage_categories = []
        must_visit_results = []

        for keyword in state.get("must_visit_places") or []:
            results, logs, attempts = self._search(state, "관광지", 3, excluded, keyword_override=keyword)
            tool_logs.extend(logs)
            relaxations.extend(attempts)
            candidate = next((row for row in results if str(row.get("place_id") or "") not in excluded), None)
            if candidate:
                must_visit_results.append(dict(candidate, requested_category="관광지"))
                self._mark_used(excluded, candidate)
            else:
                warnings.append(f"필수 방문 장소 '{keyword}' 검색 결과 부족")

        search_categories = sorted(
            set(categories),
            key=lambda value: self.CATEGORY_ORDER.index(value) if value in self.CATEGORY_ORDER else len(self.CATEGORY_ORDER),
        )
        for category in search_categories:
            needed = max(categories.count(category) * 2, days + 2)
            results, logs, attempts = self._search_many(state, category, needed, excluded)
            pools[category] = results
            tool_logs.extend(logs)
            relaxations.extend(attempts)
            if not results:
                warnings.append(f"{category} 검색 결과 부족")
                shortage_categories.append(category)

        itinerary_days = []
        used = set(excluded)
        for day_index in range(days):
            plan = day_plans[day_index]
            selected = []
            seed_slot = next(
                (slot for slot in plan["slots"] if slot["key"] == "morning_attraction"),
                plan["slots"][0] if plan["slots"] else None,
            )
            cluster_seed = self._pick_cluster_anchor(
                pools.get(seed_slot["category"], []) if seed_slot else [],
                pools, plan, used, state,
            )
            previous_anchor = self._coord(cluster_seed) if cluster_seed else None
            required_place = must_visit_results[day_index] if day_index < len(must_visit_results) else None
            for slot_index, slot in enumerate(plan["slots"]):
                category = slot["category"]
                candidate = None
                if required_place is not None and slot["key"] in ["morning_attraction", "afternoon_activity"]:
                    candidate = required_place
                    required_place = None
                if (
                    candidate is None
                    and cluster_seed is not None
                    and seed_slot is not None
                    and slot["key"] == seed_slot["key"]
                    and not self._is_used(cluster_seed, used)
                ):
                    candidate = cluster_seed
                if candidate is None:
                    previous_route_anchor = self._coord(selected[-2]) if len(selected) >= 2 else None
                    next_slot = plan["slots"][slot_index + 1] if slot_index + 1 < len(plan["slots"]) else None
                    next_rows = pools.get(next_slot["category"], []) if next_slot else []
                    candidate = (
                        self._pick_easy_route_candidate(
                            pools.get(category, []), used, previous_anchor,
                            previous_route_anchor, next_rows, state,
                        )
                        if previous_anchor is not None
                        else self._pick_cluster_anchor(pools.get(category, []), pools, plan, used, state)
                    )
                if candidate is None:
                    candidate = self._pick_from_similar(pools, category, used, previous_anchor, state)
                if candidate is None and previous_anchor is not None:
                    nearby, nearby_logs, nearby_attempts = self._search_nearby(
                        state, category, used, previous_anchor,
                    )
                    tool_logs.extend(nearby_logs)
                    relaxations.extend(nearby_attempts)
                    if nearby is not None:
                        candidate = nearby
                        pools.setdefault(category, []).append(nearby)
                if candidate is None:
                    shortage_categories.append(category)
                    continue
                selected.append(self._decorate_slot(candidate, slot, category))
                self._mark_used(used, candidate)
                previous_anchor = self._coord(candidate) or previous_anchor

            if len(selected) < len(plan["slots"]):
                warnings.append(f"{day_index + 1}일차 장소 검색 결과 부족")
                continue
            day, route_logs, route_warnings = self._assemble_day(
                state, day_index, days, selected, pools=pools, used=used, plan=plan,
            )
            tool_logs.extend(route_logs)
            warnings.extend(route_warnings)
            missing_slots = self._missing_schedule_slots(day)
            if missing_slots:
                warnings.append(f"{day_index + 1}일차 필수 일정 누락: {', '.join(missing_slots)}")
                continue
            itinerary_days.append(day)

        if len(itinerary_days) != days:
            shortage_categories = self._unique(shortage_categories)
            return {
                "ok": False,
                "failure_stage": "place_search",
                "message": self._place_search_failure_message(state, shortage_categories),
                "failure_reason": {
                    "code": "insufficient_route_candidates",
                    "region": str(state.get("region") or "").strip(),
                    "days": days,
                    "transport": str(state.get("transport") or "대중교통").strip(),
                    "required_places_per_day": len(self.REQUIRED_SCHEDULE_SLOTS),
                    "shortage_categories": shortage_categories,
                },
                "warnings": self._unique(warnings or ["장소 검색 결과 부족"]),
                "tool_logs": tool_logs,
                "metadata": {"relaxations": relaxations, "elapsed_ms": self._ms(started)},
            }

        quality = self._validate_quality(state, itinerary_days)
        draft = {
            "title": f"{state.get('region') or '여행'} {days}일 코스",
            "region": state.get("region") or "",
            "days": itinerary_days,
            "transport": state.get("transport") or "대중교통",
            "traveler_style": self._traveler_style(state),
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "quality": quality,
            "metadata": {
                "source": "deterministic_places_engine",
                "relaxations": relaxations,
                "elapsed_ms": self._ms(started),
                "route_policy": {
                    "prompt": self.EASY_ROUTE_POLICY_PROMPT,
                    "strategy": "cluster_lookahead_no_backtrack",
                    "max_leg_minutes": self.MAX_LEG_MINUTES,
                    "max_day_distance_meters": self.MAX_DAY_DISTANCE_METERS,
                },
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
        patch_logs = []
        patch_warnings = []
        enhanced = self._enhanced_revision(state, days, day_indexes, prompt, category)

        if enhanced["handled"]:
            changed = enhanced["changed"]
            patch_logs.extend(enhanced["tool_logs"])
            patch_warnings.extend(enhanced["warnings"])
        elif intent == "remove_place":
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
                places[replace_index] = self._copy_slot_metadata(new_place, self._place_from_draft(places[replace_index]))
            else:
                places.append(dict(
                    new_place,
                    itinerary_slot="extra_activity",
                    itinerary_label="추가 일정",
                    planned_duration_minutes=60,
                ))
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
        all_logs = list(patch_logs)
        warnings = list(patch_warnings)
        for index, day in enumerate(days):
            raw_places = [self._place_from_draft(place) for place in day.get("places") or []]
            plan = self._day_plan(state, index, len(days), preferred_theme=day.get("theme"))
            rebuilt, logs, day_warnings = self._assemble_day(state, index, len(days), raw_places, plan=plan)
            rebuilt_days.append(rebuilt)
            all_logs.extend(logs)
            warnings.extend(day_warnings)
        draft["days"] = rebuilt_days
        draft["transport"] = state.get("transport") or "대중교통"
        draft["generated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draft["traveler_style"] = self._traveler_style(state)
        draft["quality"] = self._validate_quality(state, rebuilt_days)
        draft.setdefault("metadata", {})["revision"] = enhanced.get("patch_type") or intent
        return {"ok": True, "draft": draft, "warnings": self._unique(warnings), "tool_logs": all_logs, "metadata": draft["metadata"]}

    def _search(self, state, category, limit, excludes, keyword_override=""):
        region = str(state.get("region") or "").strip()
        preferences = list(state.get("preferences") or [])
        keyword = str(keyword_override or "").strip() or self._keyword(category, preferences)
        mood_tags = self._mood_tags(category, preferences)
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

    def _place_search_failure_message(self, state, shortage_categories):
        region = str(state.get("region") or "해당 지역").strip()
        transport = str(state.get("transport") or "대중교통").strip()
        days = max(1, min(int(state.get("days") or 1), 14))
        categories = self._unique(shortage_categories)
        category_text = "·".join(categories[:4]) if categories else "일부 일정"
        return (
            f"입력한 여행 조건은 충분해요. {region} {days}일 코스를 하루 "
            f"{len(self.REQUIRED_SCHEDULE_SLOTS)}곳씩 중복 없이 구성하는 과정에서, "
            f"{transport} 동선 안의 {category_text} 후보를 필요한 수만큼 찾지 못했어요."
        )

    def _search_many(self, state, category, limit, excludes, keyword_override=""):
        rows = []
        logs = []
        attempts = []
        search_excludes = set(excludes or [])
        target = max(1, int(limit or 1))
        while len(rows) < target and len(logs) < 8:
            batch, batch_logs, batch_attempts = self._search(
                state, category, min(10, target - len(rows)), search_excludes,
                keyword_override=keyword_override,
            )
            logs.extend(batch_logs)
            attempts.extend(batch_attempts)
            fresh = [row for row in batch if str(row.get("place_id") or "") not in search_excludes]
            if not fresh:
                break
            rows.extend(fresh)
            for row in fresh:
                place_id = str(row.get("place_id") or "")
                if place_id:
                    search_excludes.add(place_id)
        return rows, logs, attempts

    def _assemble_day(self, state, day_index, total_days, selected, pools=None, used=None, plan=None):
        mode = self.MODE_MAP.get(state.get("transport"), "transit")
        start = state.get("arrival_time") if day_index == 0 else "09:00"
        end = state.get("departure_time") if day_index == total_days - 1 else "21:30"
        cursor = self._minutes(start or "09:00", 540)
        end_minutes = self._minutes(end or "21:30", 1290)
        places = []
        logs = []
        warnings = []
        previous = None
        total_distance = 0
        total_move = 0
        total_cost = 0
        total_stay = 0
        used = used if isinstance(used, set) else {
            str(place.get("place_id") or "") for place in selected if str(place.get("place_id") or "")
        }
        plan = plan or self._day_plan(state, day_index, total_days)

        for index, place in enumerate(selected):
            place = dict(place or {})
            category = str(place.get("requested_category") or place.get("category") or "관광지")
            if places and self._category_group(places[-1].get("category")) == self._category_group(category):
                warnings.append(f"{place.get('name') or category}: 같은 유형 연속 배치를 제외")
                continue
            move = None
            if previous is not None:
                move, move_log = self._lookup_move(previous, place, mode, len(logs))
                logs.append(move_log)
                duration = move.get("duration_minutes")
                if duration is None:
                    duration = self._fallback_minutes(previous, place, mode)
                    move = dict(move or {})
                    move["duration_minutes"] = duration
                    move["distance_meters"] = self._distance_meters(previous, place)
                    move["source"] = "haversine_fallback"
                    warnings.append("이동 경로 계산 실패로 직선거리 예상값 사용")
                move = self._prefer_short_walk(previous, place, move, mode)
                duration = move.get("duration_minutes")
                if int(duration or 0) > self.MAX_LEG_MINUTES[mode]:
                    replacement, replacement_move, replacement_logs = self._replacement_for_leg(
                        state, previous, category, pools or {}, used, mode, len(logs), place,
                    )
                    logs.extend(replacement_logs)
                    if replacement is not None:
                        original_id = str(place.get("place_id") or "")
                        if original_id:
                            used.discard(original_id)
                        place = self._copy_slot_metadata(replacement, place)
                        self._mark_used(used, place)
                        move = replacement_move
                        duration = move.get("duration_minutes")
                        warnings.append(f"과도한 이동 구간을 같은 권역의 {place.get('name') or category}(으)로 자동 교체")
                    else:
                        warnings.append(f"{place.get('name') or category}: {duration}분 이동으로 일정에서 제외")
                        continue
                if move.get("status") != "ok":
                    warnings.append("일부 이동시간은 예상값")
                leg_distance = int(move.get("distance_meters") or self._distance_meters(previous, place))
                if (
                    total_distance + leg_distance > self.MAX_DAY_DISTANCE_METERS[mode]
                    or total_move + int(duration or 0) > self.MAX_DAY_MOVE_MINUTES[mode]
                ):
                    warnings.append(f"{place.get('name') or category}: 하루 이동 한도를 넘어 일정에서 제외")
                    continue
                cursor += int(duration or 0)
                total_move += int(duration or 0)
                total_distance += leg_distance

            target_minutes = self._minutes(place.get("target_time"), cursor)
            cursor = max(cursor, target_minutes)
            visit_minutes = int(place.get("planned_duration_minutes") or self.VISIT_MINUTES.get(category, 75))
            cursor, opening_warning = self._apply_opening_hours(cursor, place.get("usage_time"))
            if opening_warning:
                warnings.append(f"{place.get('name') or '장소'}: {opening_warning}")
            if cursor + visit_minutes > end_minutes and len(places) >= 2:
                warnings.append(f"{day_index + 1}일차 출발 시간 제약으로 마지막 장소 제외")
                break
            opening_status = self._opening_status(cursor, place.get("usage_time"), place.get("rest_date"))
            cost = self._place_cost(place, category)
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
                "time_period": str(place.get("itinerary_label") or self._time_period(cursor, category)),
                "time_period_icon": self._time_period_icon(cursor, category),
                "schedule_slot": str(place.get("itinerary_slot") or ""),
                "target_time": str(place.get("target_time") or ""),
                "duration_minutes": visit_minutes,
                "duration_label": f"약 {visit_minutes}분",
                "activity": self._activity(category),
                "rating": place.get("rating"),
                "review_count": int(place.get("review_count") or 0),
                "opening_status": opening_status,
                "tags": self._unique(list(place.get("tags") or []) + self._place_tags(place, category, state))[:4],
                "representative_menu": str(place.get("representative_menu") or ""),
                "estimated_cost": cost,
                "admin_area": str(place.get("admin_area") or self._admin_area(place.get("address"))),
                "move_from_previous": self._move_payload(move, mode),
            }
            places.append(row)
            cursor += visit_minutes
            total_cost += cost
            total_stay += visit_minutes
            previous = place

        day = {
            "day": day_index + 1,
            "label": f"{day_index + 1}일차",
            "date": self._day_date(state.get("start_date"), day_index),
            "start_time": start or "10:00",
            "end_time": self._clock(min(cursor, end_minutes)),
            "places": places,
            "total_move_minutes": total_move,
            "total_distance_meters": total_distance,
            "total_stay_minutes": total_stay,
            "expected_cost": total_cost,
            "expected_cost_label": self._won(total_cost),
            "expected_move_time": self._duration_label(total_move),
            "theme": plan.get("theme") or "가까운 권역 핵심 여행",
            "today_recommendation": plan.get("recommendation") or "가까운 장소를 천천히 둘러보세요.",
            "recommendation_reason": self._recommendation_reason(state, places, total_move),
            "caution": self._day_caution(places, warnings),
            "weather": "출발 전 현지 예보와 야외 장소 운영 여부를 확인하세요.",
            "traveler_style": self._traveler_style(state),
            "return_plan": {
                "label": self._return_label(state, total_days),
                "time": self._clock(min(cursor, end_minutes)),
                "note": "숙소 또는 다음 이동지까지 자연스럽게 연결되는 마무리 동선",
            },
        }
        day["description"] = self._day_description(state, day)
        day["quality_score"] = self._day_quality_score(day)
        return day, logs, warnings

    def _categories(self, state):
        return list(self._day_plan(state, 0, max(1, int(state.get("days") or 1)))["categories"])

    def _day_plan(self, state, day_index, total_days, preferred_theme=""):
        preferences = set(state.get("preferences") or [])
        excluded = set(state.get("excluded_preferences") or [])
        style = self._traveler_style(state)
        rainy = "실내" in preferences or "비 오는 날" in preferences
        if rainy:
            morning_category = "문화시설"
            afternoon_category = "체험"
            evening_category = "문화시설"
            theme = "비 오는 날에도 편안한 실내 감성 여행"
        elif day_index == 0:
            morning_category = "자연" if preferences.intersection({"바다", "자연"}) else "관광지"
            afternoon_category = "사진 명소" if "사진 명소" in preferences else "체험"
            evening_category = "야경" if "야경" in preferences else "전망대"
            theme = "도착 후 대표 명소와 가까운 풍경 산책"
        elif day_index == total_days - 1 and total_days > 1:
            morning_category = "시장"
            afternoon_category = "쇼핑"
            evening_category = "전망대"
            theme = "로컬 시장과 기념품을 즐기는 여유로운 귀가 동선"
        else:
            morning_category = "사진 명소"
            afternoon_category = "문화시설" if "문화" in preferences else "체험"
            evening_category = "야경" if "야경" in preferences else "전망대"
            theme = "감성 명소와 로컬 미식을 잇는 하루"
        if style in ["가족", "아이 동반", "부모님"]:
            afternoon_category = "문화시설"
            evening_category = "전망대"
            theme = f"{style} 여행에 맞춘 편안한 핵심 코스"
        if style == "혼자":
            afternoon_category = "문화시설" if not rainy else afternoon_category
            evening_category = "전망대" if not rainy else evening_category
            theme = "혼자서도 안전하고 이동이 편한 핵심 여행"
        cafe_category = "디저트" if "카페" in excluded and "디저트" not in excluded else "카페"
        slots = [
            self._slot("breakfast", "아침·브런치", "음식점", "09:00", 60),
            self._slot("morning_attraction", "오전 핵심", morning_category, "10:20", 75),
            self._slot("lunch", "점심 식사", "맛집", "12:20", 60),
            self._slot("afternoon_cafe", "오후 카페", cafe_category, "14:00", 50),
            self._slot("afternoon_activity", "오후 핵심·체험", afternoon_category, "15:10", 90),
            self._slot("dinner", "저녁 식사", "음식점", "17:30", 60),
            self._slot("evening_activity", "저녁 활동", evening_category, "19:00", 60),
        ]
        slots = [slot for slot in slots if slot["category"] not in excluded]
        categories = [slot["category"] for slot in slots]
        return {
            "theme": str(preferred_theme or theme),
            "categories": categories,
            "slots": slots,
            "recommendation": self._theme_recommendation(style, categories, day_index, total_days),
        }

    def _slot(self, key, label, category, target_time, duration_minutes):
        return {
            "key": key,
            "label": label,
            "category": category,
            "target_time": target_time,
            "duration_minutes": duration_minutes,
        }

    def _decorate_slot(self, candidate, slot, category):
        return dict(
            candidate,
            requested_category=str(category or candidate.get("requested_category") or candidate.get("category") or "관광지"),
            itinerary_slot=slot.get("key"),
            itinerary_label=slot.get("label"),
            target_time=slot.get("target_time"),
            planned_duration_minutes=slot.get("duration_minutes"),
        )

    def _copy_slot_metadata(self, candidate, original):
        result = dict(candidate or {})
        for key in [
            "requested_category", "itinerary_slot", "itinerary_label",
            "target_time", "planned_duration_minutes",
        ]:
            if original.get(key) not in [None, ""]:
                result[key] = original.get(key)
        return result

    def _unique_categories(self, plans):
        categories = []
        for plan in plans:
            for category in plan.get("categories") or []:
                if category not in categories:
                    categories.append(category)
        return categories

    def _pick_nearest(self, rows, used, anchor):
        candidates = [row for row in rows if not self._is_used(row, used)]
        if not candidates:
            return None
        if anchor is None:
            return candidates[0]
        return min(candidates, key=lambda row: self._coord_distance(anchor, self._coord(row)))

    def _pick_best(self, rows, used, anchor, state):
        candidates = [row for row in rows if not self._is_used(row, used)]
        if not candidates:
            return None
        if anchor is None:
            return max(candidates, key=self._place_quality_value)
        mode = self.MODE_MAP.get(state.get("transport"), "transit")
        anchor_area = self._admin_area(anchor.get("address") if isinstance(anchor, dict) else "")
        candidates.sort(key=lambda row: (
            0 if anchor_area and self._admin_area(row.get("address")) == anchor_area else 1,
            self._coord_distance(anchor, self._coord(row)),
            -self._place_quality_value(row),
        ))
        target_minutes = self._candidate_target_minutes(mode)
        within = [
            row for row in candidates
            if self._fallback_minutes_from_coord(anchor, row, mode) <= target_minutes
        ]
        return within[0] if within else None

    def _pick_easy_route_candidate(self, rows, used, anchor, previous_anchor, next_rows, state):
        candidates = [row for row in rows if not self._is_used(row, used) and self._coord(row)]
        if not candidates:
            return None
        if anchor is None:
            return max(candidates, key=self._place_quality_value)
        mode = self.MODE_MAP.get(state.get("transport"), "transit")
        target_minutes = self._candidate_target_minutes(mode)
        candidates = [
            row for row in candidates
            if self._fallback_minutes_from_coord(anchor, row, mode) <= target_minutes
        ]
        if not candidates:
            return None
        future = [
            row for row in next_rows or []
            if not self._is_used(row, used) and self._coord(row)
        ]
        anchor_area = self._admin_area(anchor.get("address") if isinstance(anchor, dict) else "")

        def score(row):
            coord = self._coord(row)
            current_distance = self._coord_distance(anchor, coord)
            lookahead_distance = min(
                (self._coord_distance(coord, self._coord(next_row)) for next_row in future),
                default=0,
            )
            backtrack_penalty = self._route_backtrack_penalty(
                previous_anchor, anchor, coord, current_distance,
            )
            area_penalty = 0 if not anchor_area or self._admin_area(row.get("address")) == anchor_area else 1
            route_cost = (
                current_distance
                + lookahead_distance * self.ROUTE_LOOKAHEAD_WEIGHT
                + backtrack_penalty
            )
            return area_penalty, route_cost, -self._place_quality_value(row)

        return min(candidates, key=score)

    def _route_backtrack_penalty(self, previous, current, candidate, distance):
        if not previous or not current or not candidate:
            return 0
        incoming = (current[0] - previous[0], current[1] - previous[1])
        outgoing = (candidate[0] - current[0], candidate[1] - current[1])
        incoming_size = math.hypot(*incoming)
        outgoing_size = math.hypot(*outgoing)
        if incoming_size <= 0 or outgoing_size <= 0:
            return 0
        cosine = (
            incoming[0] * outgoing[0] + incoming[1] * outgoing[1]
        ) / (incoming_size * outgoing_size)
        if cosine >= -0.15:
            return 0
        return distance * (1 + abs(cosine) * self.ROUTE_BACKTRACK_WEIGHT)

    def _search_nearby(self, state, category, used, anchor):
        mode = self.MODE_MAP.get(state.get("transport"), "transit")
        target_minutes = self._candidate_target_minutes(mode)
        logs = []
        attempts = []
        search_categories = [category] + self._similar_categories(category)
        for search_category in self._unique(search_categories):
            args = {
                "region": state.get("region") or "",
                "category": search_category,
                "keyword": self._keyword(search_category, state.get("preferences") or []),
                "mood_tags": self._mood_tags(
                    search_category, state.get("preferences") or [],
                ) if search_category == category else [],
                "exclude_place_ids": list(used),
                "limit": 10,
                "near_lat": anchor[0],
                "near_lng": anchor[1],
                "radius_meters": self._nearby_radius_meters(mode),
                "force_external": True,
            }
            data = self.tools.execute_place_search(args)
            logs.append(self._tool_log("place_search", args, data, len(logs)))
            rows = [
                row for row in data.get("results") or []
                if not self._is_used(row, used)
                and self._fallback_minutes_from_coord(anchor, row, mode) <= target_minutes
            ]
            print(
                "[travel_itinerary] nearby_search "
                f"category={search_category} status={data.get('status', 'error')} "
                f"relaxation={data.get('relaxation', '')} candidates={len(data.get('results') or [])} "
                f"eligible={len(rows)} radius={args['radius_meters']}"
            )
            attempts.append({
                "category": search_category,
                "region": state.get("region") or "",
                "status": data.get("status", "error"),
                "relaxation": data.get("relaxation", ""),
                "nearby": True,
            })
            rows.sort(key=lambda row: (
                self._fallback_minutes_from_coord(anchor, row, mode),
                -self._place_quality_value(row),
            ))
            if rows:
                return dict(rows[0], requested_category=category), logs, attempts
        return None, logs, attempts

    def _candidate_target_minutes(self, mode):
        return {"walking": 12, "transit": 4, "driving": 10}.get(mode, 4)

    def _nearby_radius_meters(self, mode):
        return {"walking": 1000, "transit": 1500, "driving": 5000}.get(mode, 1500)

    def _pick_cluster_anchor(self, rows, pools, plan, used, state):
        candidates = [row for row in rows if not self._is_used(row, used)]
        if not candidates:
            return None
        mode = self.MODE_MAP.get(state.get("transport"), "transit")
        target_minutes = self._candidate_target_minutes(mode)
        next_categories = list(plan.get("categories") or [])[1:]
        scored = []
        for candidate in candidates:
            area = self._admin_area(candidate.get("address"))
            coverage = 0
            nearby_count = 0
            cluster_spread = 0
            for category in next_categories:
                nearby = [
                    row for row in pools.get(category, [])
                    if not self._is_used(row, used)
                    and self._fallback_minutes(candidate, row, mode) <= target_minutes
                ]
                if nearby:
                    coverage += 1
                    nearby_count += sum(1 for row in nearby if area and self._admin_area(row.get("address")) == area)
                    cluster_spread += min(self._distance_meters(candidate, row) for row in nearby)
            scored.append((coverage, nearby_count, cluster_spread, self._place_quality_value(candidate), candidate))
        scored.sort(key=lambda item: (-item[0], -item[1], item[2], -item[3]))
        return scored[0][4]

    def _pick_from_similar(self, pools, category, used, anchor, state=None):
        for candidate_category in self._similar_categories(category):
            place = self._pick_best(pools.get(candidate_category, []), used, anchor, state or {})
            if place is not None:
                return dict(place, requested_category=category)
        return None

    def _similar_categories(self, category):
        alternatives = {
            "카페": ["디저트"],
            "디저트": ["카페"],
            "야경": ["전망대", "사진 명소", "자연"],
            "전망대": ["사진 명소", "관광지"],
            "사진 명소": ["전망대", "자연", "관광지"],
            "자연": ["관광지", "사진 명소"],
            "문화시설": ["체험", "관광지"],
            "체험": ["문화시설", "관광지"],
            "시장": ["쇼핑", "관광지"],
            "맛집": ["음식점"],
            "음식점": ["맛집"],
        }
        return alternatives.get(category, ["관광지"])

    def _category_from_prompt(self, prompt):
        text = str(prompt or "")
        if any(token in text for token in ["디저트", "베이커리", "빵집"]):
            return "디저트"
        if "카페" in text:
            return "카페"
        if any(token in text for token in ["시장", "마켓"]):
            return "시장"
        if any(token in text for token in ["맛집", "음식점", "식당", "점심", "저녁", "한식", "양식"]):
            return "맛집"
        if any(token in text for token in ["사진", "포토", "인생샷"]):
            return "사진 명소"
        if any(token in text for token in ["체험", "공방", "클래스"]):
            return "체험"
        if any(token in text for token in ["전망", "전망대"]):
            return "전망대"
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
            "rating": place.get("rating"),
            "review_count": place.get("review_count", 0),
            "opening_status": place.get("opening_status", ""),
            "tags": list(place.get("tags") or []),
            "representative_menu": place.get("representative_menu", ""),
            "estimated_cost": place.get("estimated_cost", 0),
            "admin_area": place.get("admin_area", ""),
            "itinerary_slot": place.get("schedule_slot") or place.get("itinerary_slot", ""),
            "itinerary_label": place.get("time_period") or place.get("itinerary_label", ""),
            "target_time": place.get("target_time", ""),
            "planned_duration_minutes": place.get("duration_minutes") or place.get("planned_duration_minutes", 0),
        }

    def _enhanced_revision(self, state, days, day_indexes, prompt, category):
        text = str(prompt or "")
        result = {"handled": False, "changed": False, "tool_logs": [], "warnings": [], "patch_type": ""}
        cuisine = ""
        if "양식" in text:
            cuisine = "양식"
        elif "한식" in text and "말고" not in text:
            cuisine = "한식"
        indoor = any(token in text for token in ["비 오는", "비오는", "실내 위주", "실내 중심"])
        low_walking = any(token in text for token in ["걷는 거 적게", "걷기 적게", "덜 걷", "이동량 줄", "많이 안 걷"])
        add_photo = any(token in text for token in ["사진 찍기 좋은", "사진 명소", "포토 스팟", "인생샷"])
        add_night = "야경" in text and any(token in text for token in ["꼭", "추가", "넣어", "포함"])
        budget_patch = "예산" in text and self._budget_won(state.get("budget")) > 0
        if not any([cuisine, indoor, low_walking, add_photo, add_night, budget_patch]):
            return result

        result["handled"] = True
        all_ids = {
            str(place.get("place_id") or "")
            for day in days for place in day.get("places") or []
            if str(place.get("place_id") or "")
        }

        if cuisine:
            target = day_indexes[0] if day_indexes else 0
            places = list(days[target].get("places") or [])
            food_index = next((
                index for index, place in enumerate(places)
                if self._category_group(place.get("category")) == "food" and 11 <= self._hour(place.get("time")) <= 15
            ), next((index for index, place in enumerate(places) if self._category_group(place.get("category")) == "food"), -1))
            changed, logs = self._search_patch_place(state, places, food_index, "맛집", cuisine, all_ids)
            result["changed"] = changed
            result["tool_logs"].extend(logs)
            result["patch_type"] = "meal_cuisine"

        elif add_photo or add_night:
            target = day_indexes[0] if day_indexes else 0
            places = list(days[target].get("places") or [])
            requested = "야경" if add_night else "사진 명소"
            keyword = "야경" if add_night else "사진 명소"
            changed, logs = self._search_patch_place(state, places, len(places), requested, keyword, all_ids)
            result["changed"] = changed
            result["tool_logs"].extend(logs)
            result["patch_type"] = "add_night" if add_night else "add_photo_spot"

        elif indoor:
            outdoor_groups = {"sight", "nature", "view", "photo", "night"}
            for day_index in day_indexes:
                places = list(days[day_index].get("places") or [])
                targets = [index for index, place in enumerate(places) if self._category_group(place.get("category")) in outdoor_groups]
                for order, place_index in enumerate(targets[:2]):
                    requested = "문화시설" if order % 2 == 0 else "체험"
                    changed, logs = self._search_patch_place(state, places, place_index, requested, "실내", all_ids)
                    result["changed"] = result["changed"] or changed
                    result["tool_logs"].extend(logs)
            result["patch_type"] = "rainy_indoor"

        elif low_walking:
            for day_index in day_indexes:
                places = list(days[day_index].get("places") or [])
                if len(places) < 2:
                    continue
                anchor_area = self._admin_area(places[0].get("address"))
                farthest_index = max(
                    range(1, len(places)),
                    key=lambda index: self._distance_meters(places[index - 1], places[index]),
                )
                requested = str(places[farthest_index].get("category") or category or "관광지")
                changed, logs = self._search_patch_place(state, places, farthest_index, requested, anchor_area, all_ids)
                result["changed"] = result["changed"] or changed
                result["tool_logs"].extend(logs)
            result["patch_type"] = "low_walking"

        elif budget_patch:
            total_budget = self._budget_won(state.get("budget"))
            per_day = max(10000, total_budget // max(1, len(days)))
            for day_index in day_indexes:
                places = list(days[day_index].get("places") or [])
                if sum(self._place_cost(place, place.get("category")) for place in places) <= per_day:
                    result["changed"] = True
                while sum(self._place_cost(place, place.get("category")) for place in places) > per_day:
                    expensive = [
                        (self._place_cost(place, place.get("category")), index)
                        for index, place in enumerate(places)
                        if self._place_cost(place, place.get("category")) > 0
                    ]
                    if not expensive:
                        break
                    _, place_index = max(expensive)
                    requested = "시장" if self._category_group(places[place_index].get("category")) == "food" else "자연"
                    changed, logs = self._search_patch_place(state, places, place_index, requested, "가성비", all_ids)
                    result["changed"] = result["changed"] or changed
                    result["tool_logs"].extend(logs)
                    if not changed:
                        break
            result["patch_type"] = "budget_limit"

        if not result["changed"]:
            result["warnings"].append("요청 조건에 맞는 대체 장소 검색 결과 부족")
        return result

    def _search_patch_place(self, state, places, index, category, keyword, all_ids):
        results, logs, _ = self._search(state, category, 6, all_ids, keyword_override=keyword)
        if not results:
            return False, logs
        anchor = places[index - 1] if index > 0 and index - 1 < len(places) else None
        candidate = self._pick_best(results, set(), self._coord(anchor) if anchor else None, state) or results[0]
        candidate = dict(candidate, requested_category=category)
        if index < len(places):
            candidate = self._copy_slot_metadata(candidate, self._place_from_draft(places[index]))
        else:
            candidate.update({
                "itinerary_slot": "extra_activity",
                "itinerary_label": "추가 일정",
                "planned_duration_minutes": 60,
            })
        candidate_id = str(candidate.get("place_id") or "")
        if index < len(places):
            old_id = str(places[index].get("place_id") or "")
            if old_id:
                all_ids.discard(old_id)
            places[index] = candidate
        else:
            places.append(candidate)
        if candidate_id:
            all_ids.add(candidate_id)
        return True, logs

    def _lookup_move(self, origin, destination, mode, iteration):
        args = {
            "origin_place_id": origin.get("place_id", ""),
            "destination_place_id": destination.get("place_id", ""),
            "mode": mode,
        }
        move = self.tools.execute_directions_lookup(args)
        return move, self._tool_log("directions_lookup", args, move, iteration)

    def _replacement_for_leg(self, state, previous, category, pools, used, mode, iteration, original):
        candidates = [
            row for row in pools.get(category, [])
            if not self._is_used(row, used)
        ]
        if not candidates:
            candidates = [
                dict(row, requested_category=alternative)
                for alternative in self._similar_categories(category)
                for row in pools.get(alternative, [])
                if not self._is_used(row, used)
            ]
        previous_area = self._admin_area(previous.get("address"))
        candidates.sort(key=lambda row: (
            0 if previous_area and self._admin_area(row.get("address")) == previous_area else 1,
            self._distance_meters(previous, row),
            -self._place_quality_value(row),
        ))
        logs = []
        for candidate in candidates[:10]:
            candidate = dict(candidate, requested_category=str(candidate.get("requested_category") or candidate.get("category") or category))
            move, log = self._lookup_move(previous, candidate, mode, iteration + len(logs))
            logs.append(log)
            duration = move.get("duration_minutes")
            if duration is None:
                duration = self._fallback_minutes(previous, candidate, mode)
                move = dict(move or {}, duration_minutes=duration, distance_meters=self._distance_meters(previous, candidate), source="haversine_fallback")
            move = self._prefer_short_walk(previous, candidate, move, mode)
            duration = move.get("duration_minutes")
            if int(duration or 0) <= self.MAX_LEG_MINUTES[mode]:
                return candidate, move, logs

        previous_coord = self._coord(previous)
        if previous_coord:
            for search_category in self._unique([category] + self._similar_categories(category)):
                args = {
                    "region": state.get("region") or "",
                    "category": search_category,
                    "keyword": self._keyword(search_category, state.get("preferences") or []),
                    "mood_tags": self._mood_tags(search_category, state.get("preferences") or []),
                    "exclude_place_ids": list(used),
                    "limit": 10,
                    "near_lat": previous_coord[0],
                    "near_lng": previous_coord[1],
                    "radius_meters": self._nearby_radius_meters(mode),
                    "force_external": True,
                }
                data = self.tools.execute_place_search(args)
                logs.append(self._tool_log("place_search", args, data, iteration + len(logs)))
                nearby_rows = sorted(
                    data.get("results") or [],
                    key=lambda row: self._fallback_minutes(previous, row, mode),
                )
                nearby_rows = [
                    row for row in nearby_rows
                    if self._fallback_minutes(previous, row, mode)
                    <= self._candidate_target_minutes(mode)
                ]
                for row in nearby_rows[:10]:
                    candidate = dict(row, requested_category=category)
                    move, log = self._lookup_move(previous, candidate, mode, iteration + len(logs))
                    logs.append(log)
                    duration = move.get("duration_minutes")
                    if duration is None:
                        duration = self._fallback_minutes(previous, candidate, mode)
                        move = dict(
                            move or {},
                            duration_minutes=duration,
                            distance_meters=self._distance_meters(previous, candidate),
                            source="haversine_fallback",
                        )
                    move = self._prefer_short_walk(previous, candidate, move, mode)
                    duration = move.get("duration_minutes")
                    if int(duration or 0) <= self.MAX_LEG_MINUTES[mode]:
                        pools.setdefault(category, []).append(candidate)
                        return candidate, move, logs
        return None, None, logs

    def _prefer_short_walk(self, origin, destination, move, requested_mode):
        move = dict(move or {})
        if requested_mode != "transit":
            return move
        duration = int(move.get("duration_minutes") or 0)
        if duration <= self.MAX_LEG_MINUTES["transit"]:
            return move
        walking_minutes = self._fallback_minutes(origin, destination, "walking")
        if walking_minutes > self.MAX_LEG_MINUTES["walking"]:
            return move
        return {
            "status": "estimated",
            "duration_minutes": walking_minutes,
            "distance_meters": self._distance_meters(origin, destination),
            "mode": "walking",
            "source": "short_walk_connection",
        }

    def _validate_quality(self, state, days):
        places = [place for day in days for place in day.get("places") or []]
        ids = [str(place.get("place_id") or "") for place in places]
        names = [self._normalized_name(place.get("name")) for place in places if self._normalized_name(place.get("name"))]
        duplicate_count = max(0, len(ids) - len(set(ids))) + max(0, len(names) - len(set(names)))
        consecutive_count = sum(
            1 for day in days for one, two in zip(day.get("places") or [], (day.get("places") or [])[1:])
            if self._category_group(one.get("category")) == self._category_group(two.get("category"))
        )
        opening_conflicts = sum(1 for place in places if "종료" in str(place.get("opening_status") or ""))
        dense_days = sum(1 for day in days if int(day.get("total_stay_minutes") or 0) + int(day.get("total_move_minutes") or 0) > 720)
        missing_slot_days = sum(1 for day in days if self._missing_schedule_slots(day))
        meal_days_ok = all(
            sum(1 for place in day.get("places") or [] if self._category_group(place.get("category")) == "food") >= 2
            for day in days
        )
        cafe_days_ok = all(
            any(self._category_group(place.get("category")) == "cafe" for place in day.get("places") or [])
            for day in days
        )
        mode = self.MODE_MAP.get(state.get("transport"), "transit")
        excessive_days = sum(1 for day in days if int(day.get("total_distance_meters") or 0) > self.MAX_DAY_DISTANCE_METERS[mode])
        route_backtracks = sum(self._route_backtrack_count(day.get("places") or []) for day in days)
        total_cost = sum(int(day.get("expected_cost") or 0) for day in days)
        budget = self._budget_won(state.get("budget"))
        budget_ok = not budget or total_cost <= budget
        rated_places = sum(1 for place in places if place.get("rating") not in [None, "", 0])
        place_data_rate = round(rated_places / max(1, len(places)) * 100)
        preference_rate = self._preference_fulfillment(state, places)
        data_penalty = round((100 - place_data_rate) * 0.1)
        score = max(0, min(100, 100 - duplicate_count * 15 - consecutive_count * 8 - opening_conflicts * 8 - dense_days * 8 - missing_slot_days * 20 - excessive_days * 15 - route_backtracks * 6 - data_penalty - (10 if not budget_ok else 0)))
        score = max(0, min(100, round(score * 0.65 + preference_rate * 0.35)))
        return {
            "score": score,
            "condition_fulfillment_rate": preference_rate,
            "place_data_completeness_rate": place_data_rate,
            "total_expected_cost": total_cost,
            "total_expected_cost_label": self._won(total_cost),
            "checks": {
                "distance_ok": excessive_days == 0,
                "simple_route_ok": route_backtracks == 0,
                "no_duplicate_places": duplicate_count == 0,
                "category_variety_ok": consecutive_count == 0,
                "opening_hours_ok": opening_conflicts == 0,
                "density_ok": dense_days == 0,
                "schedule_complete": missing_slot_days == 0,
                "daily_meals_ok": meal_days_ok,
                "daily_cafe_ok": cafe_days_ok,
                "return_route_ok": all(bool(day.get("return_plan")) for day in days),
                "place_data_quality_ok": place_data_rate >= 50,
                "budget_ok": budget_ok,
                "user_conditions_ok": preference_rate >= 80,
            },
            "route_backtrack_count": route_backtracks,
        }

    def _route_backtrack_count(self, places):
        coords = [self._coord(place) for place in places]
        coords = [coord for coord in coords if coord]
        count = 0
        for previous, current, candidate in zip(coords, coords[1:], coords[2:]):
            incoming = (current[0] - previous[0], current[1] - previous[1])
            outgoing = (candidate[0] - current[0], candidate[1] - current[1])
            incoming_size = math.hypot(*incoming)
            outgoing_size = math.hypot(*outgoing)
            if incoming_size <= 0 or outgoing_size <= 0:
                continue
            cosine = (
                incoming[0] * outgoing[0] + incoming[1] * outgoing[1]
            ) / (incoming_size * outgoing_size)
            if cosine < -0.5:
                count += 1
        return count

    def _preference_fulfillment(self, state, places):
        preferences = list(state.get("preferences") or [])
        if not preferences:
            return 100
        text = " ".join(
            str(value)
            for place in places
            for value in [place.get("category"), place.get("activity"), " ".join(place.get("tags") or [])]
        )
        aliases = {
            "바다": ["바다", "자연", "오션뷰"], "자연": ["자연", "공원", "산책"],
            "맛집": ["맛집", "음식점", "시장", "식사"], "카페": ["카페", "디저트"],
            "감성카페": ["카페", "디저트", "데이트"],
            "문화": ["문화시설", "문화"], "야경": ["야경", "전망대"],
            "쇼핑": ["쇼핑", "시장"], "액티비티": ["체험", "레포츠"],
            "사진 명소": ["사진 명소", "사진명소", "전망대"], "실내": ["실내", "문화시설", "체험"],
        }
        matched = sum(1 for preference in preferences if any(token in text for token in aliases.get(preference, [preference])))
        return round(matched / max(1, len(preferences)) * 100)

    def _traveler_style(self, state):
        companions = list(state.get("companions") or [])
        for label in ["아이 동반", "부모님", "연인", "가족", "친구", "혼자"]:
            if label in companions:
                return label
        return "취향 중심"

    def _theme_recommendation(self, style, categories, day_index, total_days):
        if day_index == 0:
            return "첫날은 도착 피로를 고려해 대표 명소와 식사를 가까운 권역에 묶었어요."
        if day_index == total_days - 1:
            return "마지막 날은 시장과 쇼핑을 중심으로 귀가 전 부담이 적게 구성했어요."
        if style in ["아이 동반", "부모님", "가족"]:
            return "긴 이동보다 머무는 시간을 늘리고 쉬어갈 장소를 함께 배치했어요."
        return "사진 명소와 로컬 맛집, 휴식 장소를 리듬감 있게 연결했어요."

    def _recommendation_reason(self, state, places, total_move):
        areas = self._unique([place.get("admin_area") or self._admin_area(place.get("address")) for place in places])
        area_text = "·".join(areas[:2]) if areas else str(state.get("region") or "가까운 권역")
        return f"이동을 줄이기 위해 {area_text} 중심으로 묶었고, 예상 이동시간을 {self._duration_label(total_move)} 안으로 조정했어요."

    def _day_description(self, state, day):
        places = day.get("places") or []
        if not places:
            return ["조건에 맞는 장소를 다시 찾고 있어요."]
        first = places[0].get("name") or "첫 장소"
        food = next((place for place in places if self._category_group(place.get("category")) in ["food", "market"]), None)
        rest = next((place for place in places if self._category_group(place.get("category")) == "cafe"), None)
        last = places[-1].get("name") or "마지막 장소"
        area = places[0].get("admin_area") or self._admin_area(places[0].get("address")) or state.get("region") or "가까운 권역"
        lines = [f"오늘은 이동을 최소화하기 위해 {area} 주변으로 동선을 묶었습니다."]
        lines.append(f"오전에는 {first}에서 하루의 테마를 여유롭게 시작합니다.")
        if food:
            menu = food.get("representative_menu") or "지역 대표 메뉴"
            lines.append(f"식사는 {food.get('name')}의 {menu}를 중심으로 로컬 분위기를 느낄 수 있게 추천했습니다.")
        if rest:
            lines.append(f"오후에는 {rest.get('name')}에서 쉬어가며 다음 일정의 피로를 줄였습니다.")
        lines.append(f"마지막에는 {last}을(를) 배치해 되돌아가는 이동 없이 하루를 마무리하도록 구성했습니다.")
        return lines[:5]

    def _day_caution(self, places, warnings):
        if any("운영" in warning for warning in warnings):
            return "운영시간이 바뀔 수 있으니 방문 직전 확인하세요."
        if any(place.get("opening_status") == "영업시간 확인 필요" for place in places):
            return "일부 장소는 영업시간 정보가 없어 방문 전에 확인이 필요해요."
        return "주말과 성수기에는 식당·체험 장소 대기시간을 20분 정도 여유 있게 잡으세요."

    def _day_quality_score(self, day):
        places = day.get("places") or []
        consecutive = sum(
            1 for one, two in zip(places, places[1:])
            if self._category_group(one.get("category")) == self._category_group(two.get("category"))
        )
        penalty = consecutive * 10
        if int(day.get("total_move_minutes") or 0) > 120:
            penalty += 15
        penalty += len(self._missing_schedule_slots(day)) * 8
        return max(0, 100 - penalty)

    def _missing_schedule_slots(self, day):
        present = {str(place.get("schedule_slot") or "") for place in day.get("places") or []}
        return [slot for slot in self.REQUIRED_SCHEDULE_SLOTS if slot not in present]

    def _return_label(self, state, total_days):
        area = str(state.get("accommodation_area") or "").strip()
        if area:
            return f"{area} 숙소"
        return "귀환" if total_days == 1 else "숙소 복귀"

    def _opening_status(self, cursor, usage_time, rest_date):
        rest = str(rest_date or "").strip()
        text = str(usage_time or "")
        match = re.search(r"(\d{1,2}):(\d{2})\s*(?:~|-|–)\s*(\d{1,2}):(\d{2})", text)
        if not match:
            return "영업시간 확인 필요"
        opens = int(match.group(1)) * 60 + int(match.group(2))
        closes = int(match.group(3)) * 60 + int(match.group(4))
        if closes <= opens:
            closes += 24 * 60
        if cursor < opens:
            return f"{self._clock(opens)} 영업 시작"
        if cursor >= closes:
            return "영업 종료 가능성"
        return "영업 중 예상" if not rest else "영업 중 예상 · 휴무일 확인"

    def _time_period(self, cursor, category):
        if self._category_group(category) == "food" and 11 <= cursor // 60 < 15:
            return "점심"
        if cursor < 12 * 60:
            return "오전"
        if cursor < 18 * 60:
            return "오후"
        return "저녁"

    def _time_period_icon(self, cursor, category):
        if self._category_group(category) in ["food", "market"] and 11 <= cursor // 60 < 15:
            return "fa-bowl-food"
        if self._category_group(category) == "cafe":
            return "fa-mug-hot"
        if cursor < 12 * 60:
            return "fa-sun"
        if cursor < 18 * 60:
            return "fa-cloud-sun"
        return "fa-moon"

    def _place_tags(self, place, category, state):
        tags = [category]
        style = self._traveler_style(state)
        if style == "연인":
            tags.append("데이트")
        elif style in ["가족", "아이 동반", "부모님"]:
            tags.append("가족추천")
        elif style == "혼자":
            tags.extend(["혼자여행", "접근성 우선"])
        text = " ".join([str(place.get("name") or ""), str(place.get("address") or ""), str(place.get("overview_summary") or "")])
        if any(token in text for token in ["바다", "해변", "해안"]):
            tags.append("오션뷰")
        if category in ["사진 명소", "전망대", "야경"]:
            tags.append("사진명소")
        return self._unique(tags)[:4]

    def _place_cost(self, place, category):
        try:
            value = int(place.get("estimated_cost") or 0)
            if value > 0:
                return value
        except Exception:
            pass
        return {
            "음식점": 18000, "맛집": 20000, "카페": 9000, "디저트": 8000,
            "시장": 15000, "체험": 25000, "레포츠": 35000, "문화시설": 10000,
            "전망대": 12000,
        }.get(str(category or ""), 0)

    def _budget_won(self, value):
        text = str(value or "").replace(" ", "")
        match = re.search(r"(\d+(?:\.\d+)?)(만원|원)", text)
        if not match:
            return 0
        amount = float(match.group(1))
        return int(amount * 10000 if match.group(2) == "만원" else amount)

    def _won(self, value):
        return f"약 {max(0, int(value or 0)):,}원"

    def _duration_label(self, minutes):
        minutes = max(0, int(minutes or 0))
        hours, remain = divmod(minutes, 60)
        if hours and remain:
            return f"약 {hours}시간 {remain}분"
        if hours:
            return f"약 {hours}시간"
        return f"약 {remain}분"

    def _category_group(self, category):
        return self.CATEGORY_GROUP.get(str(category or ""), str(category or "other"))

    def _normalized_name(self, value):
        return re.sub(r"[^가-힣A-Za-z0-9]", "", str(value or "")).lower()

    def _is_used(self, row, used):
        place_id = str(row.get("place_id") or "")
        name_key = "name:" + self._normalized_name(row.get("name"))
        return bool((place_id and place_id in used) or (name_key != "name:" and name_key in used))

    def _mark_used(self, used, row):
        place_id = str(row.get("place_id") or "")
        name = self._normalized_name(row.get("name"))
        if place_id:
            used.add(place_id)
        if name:
            used.add("name:" + name)

    def _dedupe_adjacent_categories(self, categories):
        rows = []
        for category in categories:
            if rows and self._category_group(rows[-1]) == self._category_group(category):
                continue
            rows.append(category)
        return rows

    def _place_quality_value(self, row):
        try:
            rating = float(row.get("rating") or 0)
        except Exception:
            rating = 0
        try:
            reviews = min(10000, int(row.get("review_count") or 0))
        except Exception:
            reviews = 0
        return rating * 1000 + math.log10(reviews + 1) * 100 + (50 if row.get("thumbnail") else 0)

    def _fallback_minutes_from_coord(self, anchor, destination, mode):
        if isinstance(anchor, tuple):
            origin = {"lat": anchor[0], "lng": anchor[1]}
        else:
            origin = anchor or {}
        return self._fallback_minutes(origin, destination, mode)

    def _admin_area(self, address):
        tokens = str(address or "").split()
        for token in tokens:
            if token.endswith(("구", "군", "시", "읍", "면", "동")):
                return token
        return tokens[1] if len(tokens) > 1 else (tokens[0] if tokens else "")

    def _hour(self, value):
        return self._minutes(value, 0) // 60

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
        if category in ["음식점", "맛집"]:
            return category
        if category == "카페":
            return "카페"
        if category == "디저트":
            return "디저트 베이커리"
        if category == "시장":
            return "전통시장 로컬 먹거리"
        if category == "전망대":
            return "전망대"
        if category == "사진 명소":
            return "사진 명소"
        if category == "체험":
            return "체험"
        return relevant[0] if relevant else ""

    def _mood_tags(self, category, preferences):
        if self._category_group(category) in ["food", "cafe"]:
            return []
        return [item for item in preferences if item not in ["맛집", "카페"]]

    def _parent_region(self, region):
        tokens = str(region or "").split()
        return tokens[0] if len(tokens) > 1 else region

    def _activity(self, category):
        return {
            "음식점": "식사",
            "맛집": "로컬 맛집 식사",
            "카페": "카페 휴식",
            "디저트": "디저트 휴식",
            "자연": "자연 산책",
            "전망대": "전망 감상",
            "시장": "시장 먹거리와 쇼핑",
            "문화시설": "문화 관람",
            "체험": "로컬 체험",
            "사진 명소": "사진 촬영",
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
