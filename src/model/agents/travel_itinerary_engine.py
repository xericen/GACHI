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
    ROUTE_REPAIR_MAX_ATTEMPTS = 6
    # Straight-line/region pre-ranking happens before paid route lookup. Two
    # finalists use an adaptive next-slot shortlist and stop at the first
    # reachable option, avoiding the previous all-pairs fan-out.
    ROUTE_PREFILTER_LIMIT = 8
    ROUTE_SCORE_CANDIDATE_LIMIT = 2
    ROUTE_TRANSIT_FALLBACK_LIMIT = 8
    ROUTE_PAIR_SEED_LIMIT = 3
    ROUTE_LOOKAHEAD_LIMIT = 2
    ROUTE_REPLACEMENT_LIMIT = 4
    MIN_SIGNIFICANT_BACKTRACK_METERS = 350
    SEVERE_BACKTRACK_DEGREES = 125
    REGION_BOUNDS = {
        "제주": (33.05, 33.65, 126.05, 126.98),
        "제주도": (33.05, 33.65, 126.05, 126.98),
        "제주특별자치도": (33.05, 33.65, 126.05, 126.98),
        "서울": (37.413, 37.715, 126.734, 127.269),
        "서울특별시": (37.413, 37.715, 126.734, 127.269),
        "백령도": (37.90, 38.02, 124.56, 124.78),
    }
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
    # Preferred limits drive candidate ordering.  A verified route may use the
    # bounded hard limit when the whole day still stays inside MAX_DAY_*.
    MAX_LEG_MINUTES = {"walking": 15, "transit": 30, "driving": 40}
    MAX_LEG_HARD_MINUTES = {"walking": 20, "transit": 45, "driving": 60}
    MAX_DAY_DISTANCE_METERS = {"walking": 10000, "transit": 35000, "driving": 60000}
    MAX_DAY_MOVE_MINUTES = {"walking": 90, "transit": 210, "driving": 180}
    REQUIRED_SCHEDULE_SLOTS = [
        "breakfast", "morning_attraction", "lunch", "afternoon_cafe",
        "afternoon_activity", "dinner", "evening_activity",
    ]
    CANDIDATE_PIPELINE_STAGES = [
        "raw_candidates", "region_validation_passed",
        "coordinate_validation_passed", "category_validation_passed",
        "mandatory_condition_passed", "route_candidates",
        "transport_checked", "transport_reachable", "final_selected",
    ]
    CATEGORY_GROUP = {
        "음식점": "food", "맛집": "food", "시장": "market", "카페": "cafe", "디저트": "cafe",
        "관광지": "sight", "자연": "nature", "전망대": "view", "사진 명소": "photo",
        "문화시설": "culture", "체험": "experience", "레포츠": "experience", "야경": "night",
        "쇼핑": "shopping",
    }

    def __init__(self, tools):
        self.tools = tools
        self._route_score_cache = {}
        self._tool_metrics = {}
        self._candidate_stats = {}
        self._candidate_pipeline = {}
        self._candidate_pipeline_keys = {}
        self._candidate_pipeline_category_keys = {}
        self._active_candidate_slot = None

    def generate(self, state):
        started = time.monotonic()
        self._route_request_scope = f"itinerary-{time.time_ns()}-{id(self)}"
        self._route_score_cache = {}
        self._candidate_stats = {
            "raw_candidate_count": 0,
            "eligible_candidate_count": 0,
            "region_mismatch_count": 0,
            "route_reachable_candidate_count": 0,
            "candidate_evaluations": 0,
            "route_evaluations": 0,
        }
        self._tool_metrics = {
            "tool_calls": 0,
            "place_search_calls": 0,
            "directions_lookup_calls": 0,
            "external_api_calls": 0,
            "successful_external_calls": 0,
            "failed_external_calls": 0,
            "retried_external_calls": 0,
            "billing_external_calls": 0,
            "provider_skipped_route_calls": 0,
            "external_provider_requests": {},
            "external_provider_failures": {},
            "total_route_requests": 0,
            "route_cache_hits": 0,
            "route_cache_misses": 0,
            "tool_elapsed_ms": 0,
            "route_optimization_ms": 0,
        }
        days = max(1, min(int(state.get("days") or 1), 14))
        excluded = set(state.get("collected_place_ids") or [])
        day_plans = [self._day_plan(state, index, days) for index in range(days)]
        self._init_candidate_pipeline(state, day_plans)
        categories = [category for plan in day_plans for category in plan.get("categories") or []]
        pools = {}
        tool_logs = []
        warnings = []
        relaxations = []
        shortage_categories = []
        must_visit_results = []
        mandatory_failures = []
        missing_days = []
        missing_slot_details = []
        assembly_failed = False

        anchor_excludes = set(excluded)
        start_anchor, start_logs, start_attempts = self._resolve_start_anchor(state, anchor_excludes)
        tool_logs.extend(start_logs)
        relaxations.extend(start_attempts)
        if start_anchor is not None:
            self._mark_used(excluded, start_anchor)
        elif state.get("start_location"):
            warnings.append(
                f"시작 위치 '{state.get('start_location')}'의 좌표를 찾지 못해 첫 이동 구간을 계산하지 못함"
            )

        accommodation_anchor = None
        if days > 1:
            accommodation_anchor, accommodation_logs, accommodation_attempts = self._resolve_accommodation_anchor(
                state, anchor_excludes,
            )
            tool_logs.extend(accommodation_logs)
            relaxations.extend(accommodation_attempts)
            if accommodation_anchor is None and state.get("accommodation_area"):
                warnings.append(
                    f"숙소 위치 '{state.get('accommodation_area')}'의 좌표를 찾지 못해 일자 사이 숙소 이동을 계산하지 못함"
                )

        for keyword in state.get("must_visit_places") or []:
            results, logs, attempts = self._search(
                state, "관광지", 10, excluded,
                keyword_override=keyword, exact_name=True,
            )
            tool_logs.extend(logs)
            relaxations.extend(attempts)
            candidate = self._exact_named_candidate(keyword, results, excluded)
            # A strict attraction category can contain ranked but unrelated
            # rows while the exact landmark is classified as culture/park.
            # Retry the exact name without a category before declaring it
            # unreachable; never lock the first fuzzy result.
            if candidate is None:
                broad_results, broad_logs, broad_attempts = self._search(
                    state, "", 20, excluded,
                    keyword_override=keyword, exact_name=True,
                )
                tool_logs.extend(broad_logs)
                relaxations.extend(broad_attempts)
                candidate = self._exact_named_candidate(
                    keyword, list(results or []) + list(broad_results or []), excluded,
                )
            if candidate:
                must_visit_results.append(dict(
                    candidate,
                    requested_category="관광지",
                    requested_location=keyword,
                ))
                self._record_candidate_rows(
                    "mandatory_condition_passed", [candidate], "관광지",
                )
                self._mark_used(excluded, candidate)
            else:
                warnings.append(f"필수 방문 장소 '{keyword}' 검색 결과 부족")
                mandatory_failures.append(keyword)
                self._candidate_pipeline["mandatory_conditions"]["unresolved"].append(keyword)

        if mandatory_failures:
            self._tool_metrics["route_optimization_ms"] = 0
            return {
                "ok": False,
                "failure_stage": "place_search",
                "message": "요청한 필수 방문 장소를 정확히 확인하지 못했어요. 장소명을 확인하거나 다른 장소를 선택해 주세요.",
                "failure_reason": {
                    "code": "mandatory_stop_unreachable",
                    "failure_reason": "mandatory_stop_unreachable",
                    "requested_region": str(state.get("region") or "").strip(),
                    "region": str(state.get("region") or "").strip(),
                    "days": days,
                    "transport": str(state.get("transport") or "대중교통").strip(),
                    "required_places": sum(len(plan.get("slots") or []) for plan in day_plans),
                    "candidate_count": int(self._candidate_stats.get("raw_candidate_count") or 0),
                    "eligible_candidate_count": 0,
                    "route_reachable_candidate_count": 0,
                    "missing_categories": [],
                    "missing_days": [],
                    "missing_slots": [],
                    "mandatory_stops": mandatory_failures,
                },
                "warnings": self._unique(warnings),
                "tool_logs": tool_logs,
                "metadata": {
                    "relaxations": relaxations,
                    "elapsed_ms": self._ms(started),
                    "api_metrics": self._tool_metrics_payload(),
                    "candidate_pipeline": self._candidate_pipeline_payload(
                        days, [], [], [], [], returned=False,
                    ),
                },
            }

        fallback_categories = {
            fallback
            for category in categories
            for fallback in self._similar_categories(category)
        }
        category_order = lambda value: (
            self.CATEGORY_ORDER.index(value)
            if value in self.CATEGORY_ORDER else len(self.CATEGORY_ORDER)
        )
        required_search_categories = sorted(set(categories), key=category_order)
        search_categories = required_search_categories + sorted(
            fallback_categories - set(categories), key=category_order,
        )
        for category in search_categories:
            needed = min(
                24,
                max(
                    categories.count(category) * 3,
                    days + 5,
                    self.ROUTE_SCORE_CANDIDATE_LIMIT + 3,
                ),
            )
            search_state = (
                state
                if category in categories
                else dict(state, preferences=[])
            )
            results, logs, attempts = self._search_many(
                search_state, category, needed, excluded,
            )
            pools[category] = results
            tool_logs.extend(logs)
            relaxations.extend(attempts)
            if not results:
                warnings.append(f"{category} 검색 결과 부족")
                shortage_categories.append(category)

        route_started = time.monotonic()
        itinerary_days = []
        route_optimizations = []
        used = set(excluded)
        previous_day_last = None
        previous_day_penultimate = None
        for day_index in range(days):
            plan = dict(day_plans[day_index])
            day_start_anchor = previous_day_last
            day_previous_route_anchor = previous_day_penultimate
            if day_index == 0 and start_anchor is not None:
                day_start_anchor = start_anchor
                day_previous_route_anchor = None
                plan["start_anchor"] = start_anchor
            elif day_index > 0 and accommodation_anchor is not None:
                day_start_anchor = accommodation_anchor
                day_previous_route_anchor = None
                plan["start_anchor"] = accommodation_anchor
            selected = []
            seed_slot = next(
                (slot for slot in plan["slots"] if slot["key"] == "morning_attraction"),
                plan["slots"][0] if plan["slots"] else None,
            )
            self._active_candidate_slot = {
                "day": day_index + 1,
                "slot": seed_slot.get("key") if seed_slot else "",
                "category": seed_slot.get("category") if seed_slot else "",
            }
            cluster_seed = self._pick_cluster_anchor(
                pools.get(seed_slot["category"], []) if seed_slot else [],
                pools, plan, used, state, start_anchor=day_start_anchor,
            )
            cluster_pair_first = None
            cluster_pair_validated = False
            if seed_slot is not None and plan["slots"]:
                first_slot = plan["slots"][0]
                seed_categories = self._unique(
                    [seed_slot["category"]] + self._similar_categories(seed_slot["category"]),
                )
                for seed_category in seed_categories:
                    seed_rows = [
                        dict(row, requested_category=seed_slot["category"])
                        for row in pools.get(seed_category, [])
                    ]
                    pair_used = set(used)
                    for _ in range(min(self.ROUTE_PAIR_SEED_LIMIT, len(seed_rows))):
                        pair_seed = self._pick_cluster_anchor(
                            seed_rows, pools, plan, pair_used, state,
                            start_anchor=day_start_anchor,
                        )
                        if pair_seed is None:
                            break
                        self._active_candidate_slot = {
                            "day": day_index + 1,
                            "slot": first_slot.get("key") or "",
                            "category": first_slot.get("category") or "",
                        }
                        pair_first_rows = sorted(
                            pools.get(first_slot["category"], []),
                            key=lambda row: self._fallback_minutes(
                                pair_seed, row,
                                self.MODE_MAP.get(state.get("transport"), "transit"),
                            ),
                        )[:self.ROUTE_PAIR_SEED_LIMIT]
                        pair_first = self._pick_easy_route_candidate(
                            pair_first_rows, used, pair_seed,
                            day_start_anchor, [pair_seed], state,
                        )
                        if pair_first is not None:
                            cluster_seed = pair_seed
                            cluster_pair_first = pair_first
                            cluster_pair_validated = True
                            break
                        self._mark_used(pair_used, pair_seed)
                    if cluster_pair_validated:
                        break
            self._active_candidate_slot = None
            required_place = must_visit_results[day_index] if day_index < len(must_visit_results) else None
            for slot_index, slot in enumerate(plan["slots"]):
                category = slot["category"]
                self._active_candidate_slot = {
                    "day": day_index + 1,
                    "slot": slot.get("key") or "",
                    "category": category,
                }
                self._record_slot_pool(day_index + 1, slot, pools.get(category, []), used)
                candidate = None
                if slot_index == 0 and cluster_pair_first is not None:
                    candidate = cluster_pair_first
                if required_place is not None and slot["key"] in ["morning_attraction", "afternoon_activity"]:
                    candidate = dict(required_place, route_locked_reason="must_visit")
                    required_place = None
                if (
                    candidate is None
                    and cluster_seed is not None
                    and seed_slot is not None
                    and slot["key"] == seed_slot["key"]
                    and not self._is_used(cluster_seed, used)
                    and (
                        cluster_pair_validated
                        or (not selected and day_start_anchor is None)
                    )
                ):
                    candidate = cluster_seed
                if candidate is None:
                    # The first stop is paired with the day's cluster seed.  The
                    # previous day endpoint remains a direction/backtrack hint,
                    # not a hard overnight transit-reachability constraint.
                    current_anchor = (
                        cluster_seed
                        if slot_index == 0 and cluster_seed is not None
                        else selected[-1] if selected else day_start_anchor
                    )
                    previous_route_anchor = (
                        selected[-2] if len(selected) >= 2
                        else day_previous_route_anchor if not selected
                        else day_start_anchor
                    )
                    next_slot = plan["slots"][slot_index + 1] if slot_index + 1 < len(plan["slots"]) else None
                    next_rows = self._category_pool_with_alternatives(
                        pools, next_slot.get("category") if next_slot else "",
                    )
                    if next_slot is None and day_index < days - 1 and accommodation_anchor is not None:
                        next_rows = [accommodation_anchor]
                    if slot_index == 0 and cluster_seed is not None:
                        next_rows = [cluster_seed] + list(next_rows)
                    candidate = (
                        self._pick_easy_route_candidate(
                            pools.get(category, []), used, current_anchor,
                            previous_route_anchor, next_rows, state,
                        )
                        if current_anchor is not None
                        else self._pick_cluster_anchor(pools.get(category, []), pools, plan, used, state)
                    )
                if candidate is None:
                    current_anchor = (
                        cluster_seed
                        if slot_index == 0 and cluster_seed is not None
                        else selected[-1] if selected else day_start_anchor
                    )
                    candidate = self._pick_from_similar(
                        pools, category, used, current_anchor, state,
                    )
                current_anchor = (
                    cluster_seed
                    if slot_index == 0 and cluster_seed is not None
                    else selected[-1] if selected else day_start_anchor
                )
                current_coord = self._coord(current_anchor)
                if candidate is None and current_coord is not None:
                    nearby, nearby_logs, nearby_attempts = self._search_nearby(
                        state, category, used, current_anchor,
                        candidate_pools=pools,
                    )
                    tool_logs.extend(nearby_logs)
                    relaxations.extend(nearby_attempts)
                    if nearby is not None:
                        candidate = nearby
                        pools.setdefault(category, []).append(nearby)
                if candidate is None and selected:
                    candidate = self._recover_dead_end_pair(
                        state, category, pools, selected, used,
                        day_previous_route_anchor, day_start_anchor,
                    )
                if candidate is None:
                    shortage_categories.append(category)
                    self._record_slot_result(day_index + 1, slot, None, "candidate_missing")
                    missing_slot_details.append({
                        "day": day_index + 1,
                        "slot": slot.get("key") or "",
                        "category": category,
                    })
                    continue
                self._record_candidate_rows("mandatory_condition_passed", [candidate], category)
                self._record_slot_result(day_index + 1, slot, candidate, "preselected")
                selected.append(self._decorate_slot(candidate, slot, category))
                self._mark_used(used, candidate)

            self._active_candidate_slot = None
            if len(selected) < len(plan["slots"]):
                warnings.append(f"{day_index + 1}일차 장소 검색 결과 부족")
                missing_days.append(day_index + 1)
                continue
            day, route_logs, route_warnings = self._assemble_day(
                state, day_index, days, selected, pools=pools, used=used, plan=plan,
            )
            self._candidate_stats["route_reachable_candidate_count"] = int(
                self._candidate_stats.get("route_reachable_candidate_count") or 0
            ) + len(day.get("places") or [])
            tool_logs.extend(route_logs)
            warnings.extend(route_warnings)
            day, selected, repair_logs, repair_warnings, optimization = self._repair_simple_route(
                state, day_index, days, day, selected, pools, used, plan,
            )
            tool_logs.extend(repair_logs)
            warnings.extend(repair_warnings)
            if accommodation_anchor is None:
                day, selected, boundary_logs, boundary_warnings, optimization = self._repair_day_boundary(
                    state,
                    day_index,
                    days,
                    day,
                    selected,
                    pools,
                    used,
                    plan,
                    previous_day_penultimate,
                    previous_day_last,
                    optimization,
                )
                tool_logs.extend(boundary_logs)
                warnings.extend(boundary_warnings)
            if (
                accommodation_anchor is None
                and previous_day_last
                and itinerary_days
                and int(optimization.get("remaining_day_connection_minutes") or 0)
                > self._hard_leg_minutes(self.MODE_MAP.get(state.get("transport"), "transit"))
            ):
                (
                    repaired_previous_day,
                    repaired_previous_penultimate,
                    repaired_previous_last,
                    previous_logs,
                    previous_warnings,
                ) = self._repair_previous_day_boundary(
                    state, day_index, days, itinerary_days[-1], day,
                    pools, used,
                )
                tool_logs.extend(previous_logs)
                warnings.extend(previous_warnings)
                if repaired_previous_day is not None:
                    itinerary_days[-1] = repaired_previous_day
                    previous_day_penultimate = repaired_previous_penultimate
                    previous_day_last = repaired_previous_last
                    repaired_first = (day.get("places") or [None])[0]
                    repaired_move = self._route_score_move(
                        previous_day_last, repaired_first,
                        self.MODE_MAP.get(state.get("transport"), "transit"),
                    )
                    optimization["remaining_day_connection_minutes"] = int(
                        repaired_move.get("duration_minutes") or 0
                    )
            self._record_assembled_day(day_index + 1, day)
            route_optimizations.append(optimization)
            missing_slots = self._missing_schedule_slots(day)
            if missing_slots:
                warnings.append(f"{day_index + 1}일차 필수 일정 누락: {', '.join(missing_slots)}")
                missing_days.append(day_index + 1)
                assembly_failed = True
                for slot_key in missing_slots:
                    slot_plan = next(
                        (row for row in plan.get("slots") or [] if row.get("key") == slot_key),
                        {},
                    )
                    missing_slot_details.append({
                        "day": day_index + 1,
                        "slot": slot_key,
                        "category": slot_plan.get("category") or "",
                    })
                continue
            if accommodation_anchor is not None and day_index > 0:
                day["previous_day_connection"] = copy.deepcopy(day.get("start_connection") or {})
            elif previous_day_last and day.get("places"):
                first_place = self._place_from_draft(day["places"][0])
                connection, connection_log = self._lookup_move(
                    previous_day_last, first_place,
                    self.MODE_MAP.get(state.get("transport"), "transit"),
                    len(tool_logs),
                )
                tool_logs.append(connection_log)
                if connection.get("duration_minutes") is None:
                    connection = dict(
                        connection or {},
                        duration_minutes=self._fallback_minutes(previous_day_last, first_place, self.MODE_MAP.get(state.get("transport"), "transit")),
                        distance_meters=self._distance_meters(previous_day_last, first_place),
                        source="haversine_fallback",
                    )
                day["previous_day_connection"] = self._move_payload(
                    connection, self.MODE_MAP.get(state.get("transport"), "transit"),
                )
            if accommodation_anchor is not None:
                day["accommodation"] = self._accommodation_payload(accommodation_anchor)
            if accommodation_anchor is not None and day_index < days - 1 and day.get("places"):
                last_place = self._place_from_draft(day["places"][-1])
                return_move, return_log = self._lookup_move(
                    last_place, accommodation_anchor,
                    self.MODE_MAP.get(state.get("transport"), "transit"),
                    len(tool_logs),
                )
                tool_logs.append(return_log)
                if return_move.get("duration_minutes") is None:
                    return_move = dict(
                        return_move or {},
                        duration_minutes=self._fallback_minutes(
                            last_place, accommodation_anchor,
                            self.MODE_MAP.get(state.get("transport"), "transit"),
                        ),
                        distance_meters=self._distance_meters(last_place, accommodation_anchor),
                        source="haversine_fallback",
                    )
                day["accommodation_return_connection"] = self._move_payload(
                    return_move, self.MODE_MAP.get(state.get("transport"), "transit"),
                )
                day["return_plan"]["move"] = copy.deepcopy(day["accommodation_return_connection"])
                day["total_move_minutes"] = int(day.get("total_move_minutes") or 0) + int(
                    return_move.get("duration_minutes") or 0
                )
                day["total_distance_meters"] = int(day.get("total_distance_meters") or 0) + int(
                    return_move.get("distance_meters") or 0
                )
                day["expected_move_time"] = self._duration_label(day["total_move_minutes"])
            itinerary_days.append(day)
            if day.get("places"):
                previous_day_penultimate = (
                    self._place_from_draft(day["places"][-2])
                    if len(day["places"]) >= 2 else previous_day_last
                )
                previous_day_last = self._place_from_draft(day["places"][-1])

        if len(itinerary_days) != days:
            self._tool_metrics["route_optimization_ms"] = self._ms(route_started)
            shortage_categories = self._unique(
                list(shortage_categories)
                + [
                    detail.get("category")
                    for detail in missing_slot_details
                    if detail.get("category")
                ]
            )
            eligible_count = self._pool_candidate_count(pools, must_visit_results)
            reachable_count = max(
                int(self._candidate_stats.get("route_reachable_candidate_count") or 0),
                sum(len(day.get("places") or []) for day in itinerary_days),
            )
            self._candidate_stats["route_reachable_candidate_count"] = reachable_count
            failure_code = "insufficient_route_candidates"
            failure_detail = "route_assembly_failed" if assembly_failed or (eligible_count and not shortage_categories) else "candidate_shortage"
            if mandatory_failures:
                failure_code = "mandatory_stop_unreachable"
                failure_detail = "mandatory_stop_unreachable"
            elif eligible_count == 0 and int(self._candidate_stats.get("region_mismatch_count") or 0) > 0:
                failure_code = "region_candidate_mismatch"
                failure_detail = "only_out_of_region_candidates"
            return {
                "ok": False,
                "failure_stage": "route_assembly" if assembly_failed else "place_search",
                "message": self._place_search_failure_message(
                    state, shortage_categories, day_plans,
                ),
                "failure_reason": {
                    "code": failure_code,
                    "failure_reason": failure_detail,
                    "requested_region": str(state.get("region") or "").strip(),
                    "region": str(state.get("region") or "").strip(),
                    "days": days,
                    "transport": str(state.get("transport") or "대중교통").strip(),
                    "required_places_per_day": max(
                        [len(plan.get("slots") or []) for plan in day_plans] or [0]
                    ),
                    "required_places_by_day": [
                        len(plan.get("slots") or []) for plan in day_plans
                    ],
                    "required_places": sum(
                        len(plan.get("slots") or []) for plan in day_plans
                    ),
                    "candidate_count": int(self._candidate_stats.get("raw_candidate_count") or 0),
                    "eligible_candidate_count": eligible_count,
                    "route_reachable_candidate_count": reachable_count,
                    "shortage_categories": shortage_categories,
                    "missing_categories": shortage_categories,
                    "missing_days": self._unique(missing_days),
                    "missing_slots": missing_slot_details,
                    "mandatory_stops": mandatory_failures,
                    "region_mismatch_count": int(self._candidate_stats.get("region_mismatch_count") or 0),
                },
                "warnings": self._unique(warnings or ["장소 검색 결과 부족"]),
                "tool_logs": tool_logs,
                "metadata": {
                    "relaxations": relaxations,
                    "elapsed_ms": self._ms(started),
                    "api_metrics": self._tool_metrics_payload(),
                    "candidate_pipeline": self._candidate_pipeline_payload(
                        days, itinerary_days, shortage_categories,
                        missing_days, missing_slot_details, returned=False,
                    ),
                },
            }

        self._tool_metrics["route_optimization_ms"] = self._ms(route_started)
        self._candidate_stats["route_reachable_candidate_count"] = sum(
            len(day.get("places") or []) for day in itinerary_days
        )
        quality = self._validate_quality(state, itinerary_days)
        draft = {
            "title": f"{state.get('region') or '여행'} {days}일 코스",
            "region": state.get("region") or "",
            "start_location": self._start_location_payload(start_anchor),
            "accommodation": self._accommodation_payload(accommodation_anchor),
            "days": itinerary_days,
            "transport": state.get("transport") or "대중교통",
            "schedule_pace": state.get("schedule_pace") or "보통",
            "walking_tolerance": state.get("walking_tolerance") or "",
            "rest_preference": state.get("rest_preference") or "",
            "traveler_style": self._traveler_style(state),
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "quality": quality,
            "metadata": {
                "source": "deterministic_places_engine",
                "relaxations": relaxations,
                "elapsed_ms": self._ms(started),
                "api_metrics": self._tool_metrics_payload(),
                "candidate_pipeline": self._candidate_pipeline_payload(
                    days, itinerary_days, shortage_categories,
                    missing_days, missing_slot_details, returned=True,
                ),
                "route_policy": {
                    "prompt": self.EASY_ROUTE_POLICY_PROMPT,
                    "strategy": "cluster_lookahead_no_backtrack",
                    "max_leg_minutes": self.MAX_LEG_MINUTES,
                    "max_day_distance_meters": self.MAX_DAY_DISTANCE_METERS,
                },
                "route_optimization": route_optimizations,
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
        elif intent == "revise_course" and any(token in prompt for token in ["너무 많", "장소 수", "장소 줄"]):
            for index in day_indexes:
                places = list(days[index].get("places") or [])
                if len(places) > 3:
                    days[index]["places"] = places[:-1]
                    changed = True
        elif intent == "revise_course" and target_day is not None and any(
            token in prompt for token in ["다시 만들어", "새로 만들어", "다시 짜"]
        ):
            # Re-run time and route assembly for only the requested day.
            changed = True
            enhanced["patch_type"] = "rebuild_day"
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
            if index == 0 and isinstance(draft.get("start_location"), dict):
                plan["start_anchor"] = copy.deepcopy(draft["start_location"])
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

    def _search(self, state, category, limit, excludes, keyword_override="", exact_name=False):
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
                "exact_name": bool(exact_name),
            }
            data = self._execute_place_search(args)
            logs.append(self._tool_log("place_search", args, data, len(logs)))
            attempts.append({
                "category": category,
                "region": search_region,
                "status": data.get("status", "error"),
                "relaxation": data.get("relaxation", ""),
            })
            raw_rows = [
                row for row in data.get("results", []) or []
                if str(row.get("place_id") or "").strip()
                and str(row.get("place_id") or "") not in excludes
            ]
            rows = self._filter_region_candidates(region, raw_rows, category)
            if rows:
                return rows, logs, attempts
        return [], logs, attempts

    def _resolve_start_anchor(self, state, excludes):
        return self._resolve_named_anchor(
            state, excludes, "start_location", "start_location",
        )

    def _resolve_accommodation_anchor(self, state, excludes):
        return self._resolve_named_anchor(
            state, excludes, "accommodation_area", "accommodation",
        )

    def _resolve_named_anchor(self, state, excludes, state_key, reason):
        requested = str(state.get(state_key) or "").strip()
        if not requested:
            return None, [], []
        rows, logs, attempts = self._search(
            state, "", 5, excludes, keyword_override=requested,
        )
        if not rows:
            return None, logs, attempts
        query = re.sub(r"\s+", "", requested).lower()

        def rank(row):
            name = re.sub(r"\s+", "", str(row.get("name") or "")).lower()
            address = re.sub(r"\s+", "", str(row.get("address") or "")).lower()
            return (
                0 if query and query in name else 1,
                0 if query and query in address else 1,
                -self._place_quality_value(row),
                str(row.get("place_id") or row.get("name") or ""),
            )

        anchor = dict(min(rows, key=rank))
        anchor["requested_category"] = reason
        anchor["route_locked_reason"] = reason
        anchor["requested_location"] = requested
        return anchor, logs, attempts

    def _start_location_payload(self, anchor):
        if not isinstance(anchor, dict):
            return {}
        return {
            "place_id": str(anchor.get("place_id") or ""),
            "name": str(anchor.get("requested_location") or anchor.get("name") or ""),
            "resolved_name": str(anchor.get("name") or ""),
            "address": str(anchor.get("address") or ""),
            "lat": anchor.get("lat"),
            "lng": anchor.get("lng"),
            "admin_area": str(anchor.get("admin_area") or ""),
        }

    def _accommodation_payload(self, anchor):
        payload = self._start_location_payload(anchor)
        if payload:
            payload["type"] = "accommodation"
        return payload

    def _place_search_failure_message(self, state, shortage_categories, day_plans=None):
        region = str(state.get("region") or "해당 지역").strip()
        transport = str(state.get("transport") or "대중교통").strip()
        days = max(1, min(int(state.get("days") or 1), 14))
        categories = self._unique(shortage_categories)
        category_text = "·".join(categories[:4]) if categories else "일부 일정"
        plans = list(day_plans or [
            self._day_plan(state, index, days) for index in range(days)
        ])
        required_places = sum(len(plan.get("slots") or []) for plan in plans)
        return (
            f"{region} {days}일 일정의 {required_places}개 방문 구간을 실제 장소와 "
            f"{transport} 동선으로 검증했지만, {category_text} 구간을 끝까지 "
            "연결하지 못했어요. 이동시간과 운영시간을 다시 확인해 코스를 재구성해 주세요."
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
        total_distance = 0
        total_move = 0
        total_cost = 0
        total_stay = 0
        omitted_schedule_slots = []
        used = used if isinstance(used, set) else {
            str(place.get("place_id") or "") for place in selected if str(place.get("place_id") or "")
        }
        plan = plan or self._day_plan(state, day_index, total_days)
        previous = plan.get("start_anchor") if isinstance(plan, dict) else None

        for index, place in enumerate(selected):
            place = dict(place or {})
            category = str(place.get("requested_category") or place.get("category") or "관광지")
            self._active_candidate_slot = {
                "day": day_index + 1,
                "slot": str(place.get("itinerary_slot") or ""),
                "category": category,
            }
            locked_reason = str(place.get("route_locked_reason") or "")
            if (
                not locked_reason
                and places
                and self._category_group(places[-1].get("category")) == self._category_group(category)
                and self._scheduled_gap_minutes(places[-1], place) < 120
            ):
                warnings.append(f"{place.get('name') or category}: 같은 유형 연속 배치를 제외")
                self._record_slot_outcome_for_place(place, "consecutive_category_rejected")
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
                if move.get("source") == "haversine_fallback":
                    warnings.append("이동 경로 계산 실패로 직선거리 예상값 사용")
                route_unreachable = self._transit_route_unreachable(move, mode)
                if route_unreachable or int(duration or 0) > self._hard_leg_minutes(mode):
                    if locked_reason:
                        warnings.append(
                            f"{place.get('name') or category}: {locked_reason} 조건을 우선해 "
                            f"{duration}분 이동 구간을 유지"
                        )
                    else:
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
                            reason = "대중교통 경로 없음" if route_unreachable else f"{duration}분 이동"
                            warnings.append(f"{place.get('name') or category}: {reason}으로 일정에서 제외")
                            outcome = "transport_unreachable" if route_unreachable else "leg_time_exceeded"
                            self._record_slot_outcome_for_place(place, outcome)
                            continue
                if move.get("status") != "ok":
                    warnings.append("일부 이동시간은 예상값")
                leg_distance = int(move.get("distance_meters") or self._distance_meters(previous, place))
                if (
                    total_distance + leg_distance > self.MAX_DAY_DISTANCE_METERS[mode]
                    or total_move + int(duration or 0) > self.MAX_DAY_MOVE_MINUTES[mode]
                ):
                    if locked_reason:
                        warnings.append(
                            f"{place.get('name') or category}: {locked_reason} 조건을 우선해 하루 이동 한도 초과를 허용"
                        )
                    else:
                        warnings.append(f"{place.get('name') or category}: 하루 이동 한도를 넘어 일정에서 제외")
                        self._record_slot_outcome_for_place(place, "daily_route_limit_exceeded")
                        omitted_schedule_slots.append({
                            "slot": str(place.get("itinerary_slot") or ""),
                            "reason": "daily_route_limit_exceeded",
                        })
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
            if cursor + visit_minutes > end_minutes and len(places) >= 2 and not locked_reason:
                warnings.append(f"{day_index + 1}일차 이용 가능 시간 안에 들어오지 않아 마지막 장소 제외")
                self._record_slot_outcome_for_place(place, "time_window_exceeded")
                omitted_schedule_slots.append({
                    "slot": str(place.get("itinerary_slot") or ""),
                    "reason": "time_window_exceeded",
                })
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
                "route_time_fixed": bool(place.get("target_time")),
                "route_locked_reason": locked_reason,
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

        self._active_candidate_slot = None
        planned_schedule_slots = [
            str(slot.get("key") or "") for slot in plan.get("slots") or []
            if str(slot.get("key") or "")
        ]
        omitted_slot_keys = {
            str(item.get("slot") or "") for item in omitted_schedule_slots
            if str(item.get("slot") or "")
        }
        expected_schedule_slots = [
            slot for slot in planned_schedule_slots if slot not in omitted_slot_keys
        ]
        day = {
            "day": day_index + 1,
            "label": f"{day_index + 1}일차",
            "date": self._day_date(state.get("start_date"), day_index),
            "start_time": start or "10:00",
            "end_time": self._clock(min(cursor, end_minutes)),
            "places": places,
            "planned_schedule_slots": planned_schedule_slots,
            "expected_schedule_slots": expected_schedule_slots,
            "omitted_schedule_slots": omitted_schedule_slots,
            "available_minutes": max(0, end_minutes - self._minutes(start or "09:00", 540)),
            "planned_place_count": len(planned_schedule_slots),
            "final_place_count": len(places),
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
        if isinstance(plan.get("start_anchor"), dict):
            day["start_location"] = self._start_location_payload(plan.get("start_anchor"))
            day["start_connection"] = (
                copy.deepcopy(places[0].get("move_from_previous") or {})
                if places else {}
            )
        day["description"] = self._day_description(state, day)
        day["quality_score"] = self._day_quality_score(day)
        return day, logs, warnings

    def _repair_simple_route(self, state, day_index, total_days, day, selected, pools, used, plan):
        """Bounded deterministic reselection for backtracking, jumps and detours."""
        selected = [dict(place or {}) for place in selected]
        mode = self.MODE_MAP.get(state.get("transport"), "transit")
        current_day = day
        current_objective = self._day_route_objective(current_day, mode)
        current_count = current_objective[1]
        current_jumps = current_objective[2]
        current_detour = current_objective[3]
        optimization = {
            "day": day_index + 1,
            "attempted": False,
            "attempts": 0,
            "before_backtracks": current_count,
            "remaining_backtracks": current_count,
            "before_cross_region_jumps": current_jumps,
            "remaining_cross_region_jumps": current_jumps,
            "before_detour_ratio": current_detour,
            "remaining_detour_ratio": current_detour,
            "improved": False,
            "status": "not_needed" if current_objective[0] == 0 else "constrained",
            "reasons": [],
        }
        if current_objective[0] == 0:
            return current_day, selected, [], [], optimization

        optimization["attempted"] = True
        logs = []
        warnings = []
        rejected_ids_by_index = {}
        rejected_indexes = set()
        corridor_attempted = set()
        for _ in range(self.ROUTE_REPAIR_MAX_ATTEMPTS):
            target_index = self._repair_target_index(
                selected, rejected_indexes, current_day, mode,
            )
            if target_index is None:
                optimization["reasons"].append("locked_or_no_replaceable_backtrack_slot")
                break

            original = selected[target_index]
            original_id = str(original.get("place_id") or "")
            rejected_ids = rejected_ids_by_index.setdefault(target_index, set())
            category = str(original.get("requested_category") or original.get("category") or "관광지")
            selected_ids = {
                str(place.get("place_id") or "") for index, place in enumerate(selected)
                if index != target_index and str(place.get("place_id") or "")
            }
            candidate_pool = [
                row for row in self._category_pool_with_alternatives(pools, category)
                if str(row.get("place_id") or "") not in selected_ids
                and str(row.get("place_id") or "") not in rejected_ids
                and str(row.get("place_id") or "") != original_id
            ]
            trial_used = set(used or [])
            if original_id:
                trial_used.discard(original_id)
            next_rows = [selected[target_index + 1]] if target_index + 1 < len(selected) else []
            for next_row in next_rows:
                next_id = str(next_row.get("place_id") or "")
                if next_id:
                    trial_used.discard(next_id)
            if target_index not in corridor_attempted and target_index > 0:
                corridor_attempted.add(target_index)
                nearby, nearby_logs, _ = self._search_nearby(
                    state, category, trial_used, self._coord(selected[target_index - 1]),
                )
                logs.extend(nearby_logs)
                if nearby is not None and all(
                    str(row.get("place_id") or "") != str(nearby.get("place_id") or "")
                    for row in candidate_pool
                ):
                    candidate_pool.append(nearby)
                    pools.setdefault(category, []).append(nearby)
            replacement = self._pick_easy_route_candidate(
                candidate_pool,
                trial_used,
                selected[target_index - 1] if target_index > 0 else None,
                selected[target_index - 2] if target_index > 1 else None,
                next_rows,
                state,
            )
            optimization["attempts"] += 1
            if replacement is None:
                rejected_indexes.add(target_index)
                optimization["reasons"].append(f"no_feasible_alternative:{target_index}")
                continue

            replacement_id = str(replacement.get("place_id") or "")
            trial_selected = list(selected)
            trial_selected[target_index] = self._copy_slot_metadata(replacement, original)
            trial_day, trial_logs, trial_warnings = self._assemble_day(
                state,
                day_index,
                total_days,
                trial_selected,
                pools=pools,
                used=set(trial_used),
                plan=plan,
            )
            logs.extend(trial_logs)
            trial_count = self._route_backtrack_count(trial_day.get("places") or [])
            trial_objective = self._day_route_objective(trial_day, mode)
            route_improved = trial_objective < current_objective
            if (
                len(trial_day.get("places") or []) < len(current_day.get("places") or [])
                or self._missing_schedule_slots(trial_day)
                or not route_improved
            ):
                if replacement_id:
                    rejected_ids.add(replacement_id)
                optimization["reasons"].append(f"alternative_not_improved:{target_index}")
                if not [
                    row for row in candidate_pool
                    if str(row.get("place_id") or "") not in rejected_ids
                ]:
                    rejected_indexes.add(target_index)
                continue

            if original_id:
                used.discard(original_id)
            self._mark_used(used, replacement)
            selected = trial_selected
            current_day = trial_day
            current_objective = trial_objective
            current_count = trial_count
            current_jumps = trial_objective[2]
            current_detour = trial_objective[3]
            warnings.extend(trial_warnings)
            optimization["improved"] = True
            optimization["status"] = "optimized" if current_objective[0] == 0 else "improved"
            rejected_ids_by_index = {}
            rejected_indexes = set()
            if current_objective[0] == 0:
                break

        optimization["remaining_backtracks"] = current_count
        optimization["remaining_cross_region_jumps"] = current_jumps
        optimization["remaining_detour_ratio"] = current_detour
        if current_objective[0]:
            warnings.append(
                f"{day_index + 1}일차 동선은 필수 방문·시간·후보 제약으로 "
                f"역방향 {current_count}개·권역 점프 {current_jumps}개·"
                f"우회 비율 {current_detour:.2f}를 남김"
            )
            if not optimization["reasons"]:
                optimization["reasons"].append("repair_attempt_limit_reached")
        return current_day, selected, logs, warnings, optimization

    def _repair_day_boundary(
        self,
        state,
        day_index,
        total_days,
        day,
        selected,
        pools,
        used,
        plan,
        previous_penultimate,
        previous_last,
        optimization,
    ):
        before = self._boundary_backtrack_count(
            previous_penultimate, previous_last, day.get("places") or [],
        )
        mode = self.MODE_MAP.get(state.get("transport"), "transit")
        current_first = (day.get("places") or [None])[0]
        current_boundary_move = (
            self._route_score_move(previous_last, current_first, mode)
            if current_first else {}
        )
        current_boundary_minutes = int(
            current_boundary_move.get("duration_minutes")
            or self._fallback_minutes(previous_last, current_first, mode)
        ) if current_first else 0
        optimization["before_cross_day_backtracks"] = before
        optimization["remaining_cross_day_backtracks"] = before
        optimization["before_day_connection_minutes"] = current_boundary_minutes
        optimization["remaining_day_connection_minutes"] = current_boundary_minutes
        if (
            (not before and current_boundary_minutes <= self._hard_leg_minutes(mode))
            or not selected or not previous_last
        ):
            return day, selected, [], [], optimization

        optimization["attempted"] = True
        logs = []
        warnings = []
        current_day = day
        current_selected = [dict(place or {}) for place in selected]
        current_day_objective = self._day_route_objective(day, mode)
        current_objective = (
            before + current_day_objective[0],
            before,
            current_day_objective[0],
            current_boundary_minutes,
            current_day_objective[3],
            current_day_objective[4],
        )
        original = current_selected[0]
        if str(original.get("route_locked_reason") or ""):
            optimization["reasons"].append("cross_day_first_slot_locked")
            return current_day, current_selected, logs, warnings, optimization

        category = str(original.get("requested_category") or original.get("category") or "관광지")
        original_id = str(original.get("place_id") or "")
        selected_ids = {
            str(place.get("place_id") or "") for place in current_selected[1:]
            if str(place.get("place_id") or "")
        }
        rejected_ids = set()
        nearby_attempted = False
        for _ in range(self.ROUTE_REPAIR_MAX_ATTEMPTS):
            candidate_pool = [
                row for row in self._category_pool_with_alternatives(pools, category)
                if str(row.get("place_id") or "") not in selected_ids
                and str(row.get("place_id") or "") not in rejected_ids
                and str(row.get("place_id") or "") != original_id
            ]
            trial_used = set(used or [])
            if original_id:
                trial_used.discard(original_id)
            next_rows = current_selected[1:2]
            for next_row in next_rows:
                next_id = str(next_row.get("place_id") or "")
                if next_id:
                    trial_used.discard(next_id)
            replacement = self._pick_easy_route_candidate(
                candidate_pool,
                trial_used,
                previous_last,
                previous_penultimate,
                next_rows,
                state,
            )
            optimization["attempts"] += 1
            if replacement is None and not nearby_attempted:
                nearby_attempted = True
                replacement, nearby_logs, _ = self._search_nearby(
                    state, category, trial_used, previous_last,
                    previous_penultimate, next_rows, candidate_pools=pools,
                )
                logs.extend(nearby_logs)
            if replacement is None:
                optimization["reasons"].append("no_cross_day_alternative")
                break
            replacement_id = str(replacement.get("place_id") or "")
            trial_selected = list(current_selected)
            trial_selected[0] = self._copy_slot_metadata(replacement, original)
            trial_day, trial_logs, trial_warnings = self._assemble_day(
                state,
                day_index,
                total_days,
                trial_selected,
                pools=pools,
                used=set(trial_used),
                plan=plan,
            )
            logs.extend(trial_logs)
            trial_boundary = self._boundary_backtrack_count(
                previous_penultimate, previous_last, trial_day.get("places") or [],
            )
            trial_first = (trial_day.get("places") or [None])[0]
            trial_move = self._route_score_move(previous_last, trial_first, mode)
            trial_boundary_minutes = int(
                trial_move.get("duration_minutes")
                or self._fallback_minutes(previous_last, trial_first, mode)
            )
            trial_day_objective = self._day_route_objective(trial_day, mode)
            trial_objective = (
                trial_boundary + trial_day_objective[0],
                trial_boundary,
                trial_day_objective[0],
                trial_boundary_minutes,
                trial_day_objective[3],
                trial_day_objective[4],
            )
            if (
                len(trial_day.get("places") or []) < len(current_day.get("places") or [])
                or self._missing_schedule_slots(trial_day)
                or trial_objective >= current_objective
            ):
                if replacement_id:
                    rejected_ids.add(replacement_id)
                optimization["reasons"].append("cross_day_alternative_not_improved")
                continue
            if original_id:
                used.discard(original_id)
            self._mark_used(used, replacement)
            current_day = trial_day
            current_selected = trial_selected
            current_objective = trial_objective
            current_boundary_minutes = trial_boundary_minutes
            before = trial_boundary
            warnings.extend(trial_warnings)
            optimization["improved"] = True
            optimization["status"] = (
                "optimized"
                if current_objective[0] == 0
                and current_boundary_minutes <= self._hard_leg_minutes(mode)
                else "improved"
            )
            break

        optimization["remaining_cross_day_backtracks"] = before
        optimization["remaining_day_connection_minutes"] = current_boundary_minutes
        if before or current_boundary_minutes > self._hard_leg_minutes(mode):
            warnings.append(
                f"{day_index + 1}일차 시작 동선은 전날 연결 및 후보 제약으로 "
                f"역방향 {before}개·연결 {current_boundary_minutes}분을 남김"
            )
        return current_day, current_selected, logs, warnings, optimization

    def _boundary_backtrack_count(self, previous_penultimate, previous_last, places):
        if not previous_last or not places:
            return 0
        count = 0
        if previous_penultimate:
            count += self._route_backtrack_count(
                [previous_penultimate, previous_last, places[0]],
            )
        if len(places) >= 2:
            count += self._route_backtrack_count(
                [previous_last, places[0], places[1]],
            )
        return count

    def _repair_previous_day_boundary(
        self, state, day_index, total_days, previous_day, current_day,
        pools, used,
    ):
        """Repair an over-limit day boundary by replacing the prior day's last stop."""
        previous_places = list((previous_day or {}).get("places") or [])
        current_first = ((current_day or {}).get("places") or [None])[0]
        if len(previous_places) < 2 or not current_first:
            return None, None, None, [], []
        original = self._place_from_draft(previous_places[-1])
        if str(original.get("route_locked_reason") or ""):
            return None, None, None, [], []
        category = str(
            original.get("requested_category") or original.get("category") or "관광지"
        )
        anchor = self._place_from_draft(previous_places[-2])
        previous_anchor = (
            self._place_from_draft(previous_places[-3])
            if len(previous_places) >= 3 else None
        )
        mode = self.MODE_MAP.get(state.get("transport"), "transit")
        original_id = str(original.get("place_id") or "")
        original_name = self._normalized_name(original.get("name"))
        trial_used = set(used or [])
        if original_id:
            trial_used.discard(original_id)
        if original_name:
            trial_used.discard("name:" + original_name)
        current_id = str(current_first.get("place_id") or "")
        current_name = self._normalized_name(current_first.get("name"))
        if current_id:
            trial_used.discard(current_id)
        if current_name:
            trial_used.discard("name:" + current_name)

        replacement = self._pick_easy_route_candidate(
            self._category_pool_with_alternatives(pools, category),
            trial_used, anchor, previous_anchor, [current_first], state,
        )
        logs = []
        warnings = []
        if replacement is None:
            replacement, nearby_logs, _ = self._search_nearby(
                state, category, trial_used, anchor,
                previous_anchor, [current_first], candidate_pools=pools,
            )
            logs.extend(nearby_logs)
        if replacement is None:
            return None, None, None, logs, warnings

        raw_places = [self._place_from_draft(place) for place in previous_places]
        raw_places[-1] = self._copy_slot_metadata(replacement, original)
        previous_plan = self._day_plan(
            state, day_index - 1, total_days,
            preferred_theme=previous_day.get("theme") or "",
        )
        rebuilt, rebuild_logs, rebuild_warnings = self._assemble_day(
            state, day_index - 1, total_days, raw_places,
            pools=pools, used=set(trial_used), plan=previous_plan,
        )
        if previous_day.get("previous_day_connection"):
            rebuilt["previous_day_connection"] = copy.deepcopy(
                previous_day["previous_day_connection"]
            )
        logs.extend(rebuild_logs)
        warnings.extend(rebuild_warnings)
        if (
            len(rebuilt.get("places") or []) < len(previous_places)
            or self._missing_schedule_slots(rebuilt)
        ):
            return None, None, None, logs, warnings
        rebuilt_last = self._place_from_draft(rebuilt["places"][-1])
        boundary_move = self._route_score_move(rebuilt_last, current_first, mode)
        if (
            self._transit_route_unreachable(boundary_move, mode)
            or int(boundary_move.get("duration_minutes") or 0) > self._hard_leg_minutes(mode)
        ):
            return None, None, None, logs, warnings

        if original_id:
            used.discard(original_id)
        if original_name:
            used.discard("name:" + original_name)
        self._mark_used(used, rebuilt_last)
        rebuilt_penultimate = self._place_from_draft(rebuilt["places"][-2])
        warnings.append(
            f"{day_index}일차 마지막 장소를 다음 날 45분 이내 연결 후보로 자동 교체"
        )
        return rebuilt, rebuilt_penultimate, rebuilt_last, logs, warnings

    def _repair_target_index(self, selected, rejected_indexes=None, day=None, mode="transit"):
        rejected_indexes = set(rejected_indexes or [])
        for index in self._route_backtrack_candidate_indexes(selected):
            for target_index in [index, index - 1]:
                if target_index <= 0 or target_index in rejected_indexes:
                    continue
                if not str(selected[target_index].get("route_locked_reason") or ""):
                    return target_index
        for target_index in self._route_cross_region_candidate_indexes(
            (day or {}).get("places") or selected, mode,
        ):
            if target_index <= 0 or target_index in rejected_indexes:
                continue
            if target_index >= len(selected):
                continue
            if not str(selected[target_index].get("route_locked_reason") or ""):
                return target_index
        for target_index in self._route_detour_candidate_indexes(
            (day or {}).get("places") or selected,
        ):
            if target_index <= 0 or target_index in rejected_indexes:
                continue
            if target_index >= len(selected):
                continue
            if not str(selected[target_index].get("route_locked_reason") or ""):
                return target_index
        return None

    def _day_route_objective(self, day, mode="transit"):
        places = list((day or {}).get("places") or [])
        backtracks = self._route_backtrack_count(places)
        cross_region_jumps = len(self._route_cross_region_candidate_indexes(places, mode))
        detour_ratio = self._route_detour_ratio(places)
        distance = int((day or {}).get("total_distance_meters") or 0)
        problem_count = backtracks + cross_region_jumps + (1 if detour_ratio > 3.0 else 0)
        return (problem_count, backtracks, cross_region_jumps, detour_ratio, distance)

    def _route_cross_region_candidate_indexes(self, places, mode="transit"):
        limits = {"walking": 5000, "transit": 12000, "driving": 25000}
        jump_limit = limits.get(mode, limits["transit"])
        indexes = []
        for index, (one, two) in enumerate(zip(places or [], (places or [])[1:]), start=1):
            if not self._place_area(one) or self._place_area(one) == self._place_area(two):
                continue
            distance = int(
                (two.get("move_from_previous") or {}).get("distance_meters")
                or self._distance_meters(one, two)
            )
            constrained = bool(
                one.get("route_locked_reason") or two.get("route_locked_reason")
                or one.get("route_time_fixed") or two.get("route_time_fixed")
            )
            if distance > jump_limit and not constrained:
                indexes.append(index)
        return indexes

    def _route_detour_ratio(self, places):
        places = list(places or [])
        if len(places) < 2:
            return 1.0
        route_distance = sum(
            int((two.get("move_from_previous") or {}).get("distance_meters") or self._distance_meters(one, two))
            for one, two in zip(places, places[1:])
        )
        baseline = max(
            self._distance_meters(one, two)
            for index, one in enumerate(places)
            for two in places[index + 1:]
        )
        return round(route_distance / max(1, baseline), 2)

    def _route_detour_candidate_indexes(self, places):
        candidates = []
        for index in range(1, len(places or []) - 1):
            if str((places[index] or {}).get("route_locked_reason") or ""):
                continue
            incoming = self._distance_meters(places[index - 1], places[index])
            outgoing = self._distance_meters(places[index], places[index + 1])
            shortcut = self._distance_meters(places[index - 1], places[index + 1])
            saving = incoming + outgoing - shortcut
            if saving >= self.MIN_SIGNIFICANT_BACKTRACK_METERS:
                candidates.append((saving, index))
        candidates.sort(key=lambda value: (-value[0], value[1]))
        return [index for _, index in candidates]

    def _route_backtrack_candidate_indexes(self, places):
        indexes = []
        for index in range(2, len(places)):
            if self._is_significant_backtrack(
                places[index - 2], places[index - 1], places[index],
            ):
                indexes.append(index)
        ordered = []
        for index in indexes:
            if index not in ordered:
                ordered.append(index)
        return ordered

    def _is_significant_backtrack(self, previous, current, candidate):
        previous_coord = self._coord(previous)
        current_coord = self._coord(current)
        candidate_coord = self._coord(candidate)
        if not previous_coord or not current_coord or not candidate_coord:
            return False
        incoming = (
            current_coord[0] - previous_coord[0],
            current_coord[1] - previous_coord[1],
        )
        outgoing = (
            candidate_coord[0] - current_coord[0],
            candidate_coord[1] - current_coord[1],
        )
        incoming_size = math.hypot(*incoming)
        outgoing_size = math.hypot(*outgoing)
        if incoming_size <= 0 or outgoing_size <= 0:
            return False
        cosine = (
            incoming[0] * outgoing[0] + incoming[1] * outgoing[1]
        ) / (incoming_size * outgoing_size)
        angle = math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
        incoming_meters = self._distance_meters(previous, current)
        outgoing_meters = self._distance_meters(current, candidate)
        return_distance = self._distance_meters(previous, candidate)
        return bool(
            angle >= self.SEVERE_BACKTRACK_DEGREES
            and min(incoming_meters, outgoing_meters) >= self.MIN_SIGNIFICANT_BACKTRACK_METERS
            and return_distance <= incoming_meters * 0.9
        )

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
        schedule_pace = str(state.get("schedule_pace") or "보통")
        walking_tolerance = str(state.get("walking_tolerance") or "")
        rest_preference = str(state.get("rest_preference") or "")
        duration_scale = {
            "여유롭게": 1.15,
            "보통": 1.0,
            "알차게": 0.85,
        }.get(schedule_pace, 1.0)
        if schedule_pace == "여유롭게" or rest_preference == "자주 쉬기":
            slots = [slot for slot in slots if slot["key"] != "evening_activity"]
        if walking_tolerance == "10분 이내":
            slots = [slot for slot in slots if slot["key"] != "afternoon_activity"]
        slots = [
            dict(slot, duration_minutes=max(40, int(round(slot["duration_minutes"] * duration_scale / 5.0) * 5)))
            for slot in slots
        ]
        slots = [slot for slot in slots if slot["category"] not in excluded]
        start_minutes = self._minutes(
            state.get("arrival_time") if day_index == 0 else "09:00", 540,
        )
        end_minutes = self._minutes(
            state.get("departure_time") if day_index == total_days - 1 else "21:30",
            1290,
        )
        partial_arrival = day_index == 0 and start_minutes > 600
        partial_departure = day_index == total_days - 1 and end_minutes < 1290
        if partial_arrival or partial_departure:
            slots = [
                slot for slot in slots
                if (
                    not partial_arrival
                    or self._minutes(slot.get("target_time"), start_minutes)
                    + int(slot.get("duration_minutes") or 0) > start_minutes
                )
                and (
                    not partial_departure
                    or self._minutes(slot.get("target_time"), end_minutes)
                    + int(slot.get("duration_minutes") or 0) <= end_minutes
                )
            ]
        categories = [slot["category"] for slot in slots]
        return {
            "theme": str(preferred_theme or theme),
            "categories": categories,
            "slots": slots,
            "day_window": {
                "start": self._clock(start_minutes),
                "end": self._clock(end_minutes),
                "partial": bool(partial_arrival or partial_departure),
            },
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
            route_locked_reason=str(candidate.get("route_locked_reason") or ""),
        )

    def _copy_slot_metadata(self, candidate, original):
        result = dict(candidate or {})
        for key in [
            "requested_category", "itinerary_slot", "itinerary_label",
            "target_time", "planned_duration_minutes", "route_locked_reason",
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
        anchor_area = self._place_area(anchor)
        candidates.sort(key=lambda row: (
            0 if anchor_area and self._place_area(row) == anchor_area else 1,
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
        self._candidate_stats["candidate_evaluations"] = int(
            self._candidate_stats.get("candidate_evaluations") or 0
        ) + len(candidates)
        if not candidates:
            return None
        if anchor is None:
            return max(candidates, key=self._place_quality_value)
        mode = self.MODE_MAP.get(state.get("transport"), "transit")
        target_minutes = self._candidate_target_minutes(mode)
        hard_minutes = self._hard_leg_minutes(mode)
        anchor_coord = self._coord(anchor)
        candidates = [
            row for row in candidates
            if self._fallback_minutes_from_coord(anchor_coord, row, mode) <= hard_minutes
        ]
        if not candidates:
            return None
        future = [
            row for row in next_rows or []
            if not self._is_used(row, used) and self._coord(row)
        ]
        anchor_area = self._place_area(anchor)

        def approximate_cost(row):
            current = self._fallback_minutes_from_coord(anchor_coord, row, mode)
            onward = min(
                (
                    self._fallback_minutes(row, next_row, mode)
                    + self._route_backtrack_penalty(
                        anchor_coord,
                        self._coord(row),
                        self._coord(next_row),
                        self._coord_distance(self._coord(row), self._coord(next_row)),
                    ) * 100000
                    for next_row in future
                ),
                default=0,
            )
            distance = self._coord_distance(anchor_coord, self._coord(row))
            reversal = self._route_backtrack_penalty(
                self._coord(previous_anchor), anchor_coord, self._coord(row), distance,
            )
            area_cost = 0 if not anchor_area or self._place_area(row) == anchor_area else 8
            return current + onward * self.ROUTE_LOOKAHEAD_WEIGHT + reversal * 100000 + area_cost

        candidates.sort(key=lambda row: (
            approximate_cost(row),
            0 if not anchor_area or self._place_area(row) == anchor_area else 1,
            -self._candidate_preference_score(row, state),
            -self._place_quality_value(row),
            str(row.get("place_id") or row.get("name") or ""),
        ))
        prefiltered_candidates = candidates[:self.ROUTE_PREFILTER_LIMIT]
        candidates = prefiltered_candidates[:self.ROUTE_SCORE_CANDIDATE_LIMIT]
        self._record_candidate_rows(
            "route_candidates", candidates, self._active_slot_category(),
        )
        self._record_slot_candidates("route_candidates", candidates)

        def score(row):
            coord = self._coord(row)
            move = self._prefer_short_walk(
                anchor, row, self._route_score_move(anchor, row, mode), mode,
            )
            current_minutes = int(move.get("duration_minutes") or self._fallback_minutes_from_coord(anchor_coord, row, mode))
            feasible_rank = self._route_feasibility_rank(move, mode, current_minutes)
            future_shortlist = sorted(
                [
                    next_row for next_row in future
                    if self._candidate_identity(next_row) != self._candidate_identity(row)
                ],
                key=lambda next_row: self._fallback_minutes(row, next_row, mode),
            )[:self.ROUTE_LOOKAHEAD_LIMIT]
            lookahead_options = []
            for next_row in future_shortlist:
                next_move = self._route_score_move(row, next_row, mode)
                next_minutes = int(next_move.get("duration_minutes") or self._fallback_minutes(row, next_row, mode))
                next_rank = self._route_feasibility_rank(next_move, mode, next_minutes)
                lookahead_reversal = self._route_backtrack_penalty(
                    anchor_coord,
                    self._coord(row),
                    self._coord(next_row),
                    self._coord_distance(self._coord(row), self._coord(next_row)),
                )
                lookahead_options.append((
                    next_rank,
                    next_minutes + lookahead_reversal * 100000,
                ))
                if next_rank <= 1:
                    break
            lookahead_rank, lookahead_minutes = min(
                lookahead_options,
                default=(3, hard_minutes) if future else (0, 0),
            )
            current_distance = self._coord_distance(anchor_coord, coord)
            backtrack_penalty = self._route_backtrack_penalty(
                self._coord(previous_anchor), anchor_coord, coord, current_distance,
            )
            area_penalty = 0 if not anchor_area or self._place_area(row) == anchor_area else 1
            route_cost = (
                current_minutes
                + lookahead_minutes * self.ROUTE_LOOKAHEAD_WEIGHT
                + lookahead_rank * self.MAX_LEG_MINUTES[mode]
                + backtrack_penalty * 100000
                + area_penalty * 8
            )
            return (
                feasible_rank,
                lookahead_rank,
                route_cost,
                area_penalty,
                -self._candidate_preference_score(row, state),
                -self._place_quality_value(row),
                str(row.get("place_id") or row.get("name") or ""),
            )

        scored = [(score(row), row) for row in candidates]
        def route_and_lookahead_feasible(value):
            return value[0][0] <= 1 and (not future or value[0][1] <= 1)

        if mode == "transit" and not any(route_and_lookahead_feasible(value) for value in scored):
            for row in prefiltered_candidates[
                self.ROUTE_SCORE_CANDIDATE_LIMIT:self.ROUTE_TRANSIT_FALLBACK_LIMIT
            ]:
                self._record_candidate_rows(
                    "route_candidates", [row], self._active_slot_category(),
                )
                self._record_slot_candidates("route_candidates", [row])
                value = score(row)
                scored.append((value, row))
                if route_and_lookahead_feasible((value, row)):
                    break
        feasible = [
            value for value in scored
            if value[0][0] <= 1 and (not future or value[0][1] <= 1)
        ]
        if mode == "transit" and not feasible:
            return None
        return min(feasible or scored, key=lambda value: value[0])[1]

    def _route_score_move(self, origin, destination, mode):
        self._tool_metrics["total_route_requests"] = int(
            self._tool_metrics.get("total_route_requests") or 0
        ) + 1
        self._candidate_stats["route_evaluations"] = int(
            self._candidate_stats.get("route_evaluations") or 0
        ) + 1
        origin_id = str(origin.get("place_id") or "") if isinstance(origin, dict) else ""
        destination_id = str(destination.get("place_id") or "") if isinstance(destination, dict) else ""
        origin_coord = self._coord(origin)
        destination_coord = self._coord(destination)
        cache_key = self._route_cache_key(mode, origin_id, destination_id, origin_coord, destination_coord)
        if cache_key in self._route_score_cache:
            self._tool_metrics["route_cache_hits"] = int(
                self._tool_metrics.get("route_cache_hits") or 0
            ) + 1
            cached = dict(self._route_score_cache[cache_key])
            self._record_transport_candidate(origin, destination, cached, mode)
            return cached
        self._tool_metrics["route_cache_misses"] = int(
            self._tool_metrics.get("route_cache_misses") or 0
        ) + 1
        move = {}
        if origin_id and destination_id:
            try:
                move = self._execute_directions_lookup({
                    "origin_place_id": origin_id,
                    "destination_place_id": destination_id,
                    "mode": mode,
                    "request_scope": getattr(self, "_route_request_scope", f"engine-{id(self)}"),
                }) or {}
            except Exception:
                move = {}
        duration = move.get("duration_minutes")
        actual = move.get("status") == "ok" and duration is not None
        if duration is None:
            duration = self._fallback_minutes(origin, destination, mode)
        result = {
            "duration_minutes": int(duration or 0),
            "distance_meters": int(move.get("distance_meters") or self._distance_meters(origin, destination)),
            "actual": bool(actual),
            "status": "ok" if actual else move.get("status") or "estimated",
            "source": move.get("source") or "haversine_fallback",
            "cache": move.get("cache") or "miss",
            "external_requests": int(move.get("external_requests") or 0),
            "external_successful_calls": int(move.get("external_successful_calls") or 0),
            "external_failed_calls": int(move.get("external_failed_calls") or 0),
            "external_retried_calls": int(move.get("external_retried_calls") or 0),
            "billing_external_requests": int(move.get("billing_external_requests") or 0),
            "external_provider": str(move.get("external_provider") or ""),
            "external_provider_skip_reason": str(move.get("external_provider_skip_reason") or ""),
            "external_provider_failure_code": str(move.get("external_provider_failure_code") or ""),
        }
        self._route_score_cache[cache_key] = dict(result)
        self._record_transport_candidate(origin, destination, result, mode)
        return result

    def _route_cache_key(self, mode, origin_id, destination_id, origin_coord, destination_coord):
        def endpoint(place_id, coord):
            if coord:
                return (round(float(coord[0]), 5), round(float(coord[1]), 5))
            return str(place_id or "")

        return (
            str(mode or "transit"),
            endpoint(origin_id, origin_coord),
            endpoint(destination_id, destination_coord),
        )

    def _candidate_preference_score(self, row, state):
        preferences = list(state.get("preferences") or [])
        if not preferences:
            return 0
        text = " ".join([
            str(row.get("category") or ""),
            str(row.get("name") or ""),
            str(row.get("description") or ""),
            " ".join(str(tag) for tag in row.get("tags") or []),
        ])
        aliases = {
            "바다": ["바다", "해변", "오션뷰", "자연"],
            "자연": ["자연", "공원", "산책"],
            "맛집": ["맛집", "음식점", "시장", "식사"],
            "카페": ["카페", "디저트"],
            "문화": ["문화", "박물관", "미술관"],
            "야경": ["야경", "전망대"],
        }
        return sum(
            1 for preference in preferences
            if any(token in text for token in aliases.get(preference, [preference]))
        )

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

    def _search_nearby(
        self, state, category, used, anchor,
        previous_anchor=None, next_rows=None, candidate_pools=None,
    ):
        mode = self.MODE_MAP.get(state.get("transport"), "transit")
        target_minutes = self._hard_leg_minutes(mode)
        anchor_coord = self._coord(anchor)
        if anchor_coord is None:
            return None, [], []
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
                "near_lat": anchor_coord[0],
                "near_lng": anchor_coord[1],
                "radius_meters": self._nearby_radius_meters(mode),
                "force_external": True,
            }
            data = self._execute_place_search(args)
            logs.append(self._tool_log("place_search", args, data, len(logs)))
            region_rows = self._filter_region_candidates(
                state.get("region") or "", data.get("results") or [], search_category,
            )
            rows = [
                row for row in region_rows
                if not self._is_used(row, used)
                and self._fallback_minutes_from_coord(anchor_coord, row, mode) <= target_minutes
            ]
            if isinstance(candidate_pools, dict):
                target_pool = candidate_pools.setdefault(category, [])
                known = {
                    self._candidate_identity(row) for row in target_pool
                    if self._candidate_identity(row)
                }
                for row in rows:
                    identity = self._candidate_identity(row)
                    if not identity or identity in known:
                        continue
                    known.add(identity)
                    target_pool.append(dict(row, requested_category=category))
            self._record_candidate_rows("route_candidates", rows, category)
            self._record_slot_candidates("route_candidates", rows)
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
                self._fallback_minutes_from_coord(anchor_coord, row, mode),
                -self._place_quality_value(row),
            ))
            if rows:
                if isinstance(anchor, dict):
                    chosen = self._pick_easy_route_candidate(
                        rows, used, anchor, previous_anchor, next_rows or [], state,
                    )
                    if chosen is None:
                        continue
                    return dict(chosen, requested_category=category), logs, attempts
                return dict(rows[0], requested_category=category), logs, attempts
        return None, logs, attempts

    def _candidate_target_minutes(self, mode):
        return int(self.MAX_LEG_MINUTES.get(mode, self.MAX_LEG_MINUTES["transit"]))

    def _hard_leg_minutes(self, mode):
        return int(
            self.MAX_LEG_HARD_MINUTES.get(
                mode, self.MAX_LEG_HARD_MINUTES["transit"],
            )
        )

    def _route_feasibility_rank(self, move, mode, duration=None):
        duration = int(duration if duration is not None else (move or {}).get("duration_minutes") or 0)
        if self._transit_route_unreachable(move, mode):
            return 3
        if duration > self._hard_leg_minutes(mode):
            return 2
        if duration <= self._candidate_target_minutes(mode) and (move or {}).get("actual"):
            return 0
        return 1

    def _nearby_radius_meters(self, mode):
        speed_kmh = {"walking": 4.5, "transit": 25, "driving": 35}.get(mode, 25)
        return int(speed_kmh * 1000 * self._hard_leg_minutes(mode) / 60)

    def _pick_cluster_anchor(self, rows, pools, plan, used, state, start_anchor=None):
        candidates = [row for row in rows if not self._is_used(row, used)]
        self._record_candidate_rows(
            "route_candidates", candidates, self._active_slot_category(),
        )
        self._record_slot_candidates("route_candidates", candidates)
        if not candidates:
            return None
        mode = self.MODE_MAP.get(state.get("transport"), "transit")
        target_minutes = self._candidate_target_minutes(mode)
        next_categories = list(plan.get("categories") or [])[1:]
        scored = []
        for candidate in candidates:
            area = self._place_area(candidate)
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
                    nearby_count += sum(1 for row in nearby if area and self._place_area(row) == area)
                    cluster_spread += min(self._distance_meters(candidate, row) for row in nearby)
            start_cost = self._fallback_minutes(start_anchor, candidate, mode) if start_anchor else 0
            scored.append((coverage, nearby_count, start_cost, cluster_spread, self._candidate_preference_score(candidate, state), self._place_quality_value(candidate), candidate))
        scored.sort(key=lambda item: (-item[0], -item[1], item[2], item[3], -item[4], -item[5], str(item[6].get("place_id") or "")))
        return scored[0][6]

    def _pick_from_similar(
        self, pools, category, used, anchor, state=None,
        previous_anchor=None, next_rows=None,
    ):
        for candidate_category in self._similar_categories(category):
            available = [
                row for row in pools.get(candidate_category, [])
                if not self._is_used(row, used)
            ]
            self._record_candidate_rows("route_candidates", available, category)
            self._record_slot_candidates("route_candidates", available)
            place = (
                self._pick_easy_route_candidate(
                    pools.get(candidate_category, []), used, anchor,
                    previous_anchor, next_rows or [], state or {},
                )
                if anchor is not None
                else self._pick_best(pools.get(candidate_category, []), used, anchor, state or {})
            )
            if place is not None:
                return dict(place, requested_category=category)
        return None

    def _recover_dead_end_pair(
        self, state, category, pools, selected, used,
        previous_day_penultimate=None, previous_day_last=None,
    ):
        """Replace the previous unlocked stop when it leaves the next slot unreachable."""
        if not selected:
            return None
        original = selected[-1]
        if str(original.get("route_locked_reason") or ""):
            return None
        original_category = str(
            original.get("requested_category") or original.get("category") or "관광지"
        )
        previous_rows = self._category_pool_with_alternatives(
            pools, original_category,
        )
        next_rows = self._category_pool_with_alternatives(pools, category)
        if not previous_rows or not next_rows:
            return None

        anchor = selected[-2] if len(selected) >= 2 else previous_day_last
        previous_anchor = (
            selected[-3] if len(selected) >= 3
            else previous_day_penultimate if len(selected) == 1
            else previous_day_last
        )
        if anchor is None:
            return None
        trial_used = set(used or [])
        original_id = str(original.get("place_id") or "")
        original_name = self._normalized_name(original.get("name"))
        if original_id:
            trial_used.discard(original_id)
        if original_name:
            trial_used.discard("name:" + original_name)
        replacement = self._pick_easy_route_candidate(
            previous_rows, trial_used, anchor, previous_anchor, next_rows, state,
        )
        if replacement is None:
            return None
        replacement_slot = self._copy_slot_metadata(replacement, original)
        self._mark_used(trial_used, replacement_slot)
        next_place = self._pick_easy_route_candidate(
            next_rows, trial_used, replacement_slot, anchor, [], state,
        )
        if next_place is None:
            return None

        if original_id:
            used.discard(original_id)
        if original_name:
            used.discard("name:" + original_name)
        self._mark_used(used, replacement_slot)
        selected[-1] = replacement_slot
        return dict(next_place, requested_category=category)

    def _category_pool_with_alternatives(self, pools, category):
        if not category:
            return []
        rows = []
        seen = set()
        for candidate_category in self._unique(
            [category] + self._similar_categories(category),
        ):
            for row in pools.get(candidate_category, []) or []:
                identity = self._candidate_identity(row)
                if not identity or identity in seen:
                    continue
                seen.add(identity)
                rows.append(row)
        return rows

    def _similar_categories(self, category):
        alternatives = {
            "카페": ["디저트"],
            "디저트": ["카페"],
            "야경": ["전망대", "사진 명소", "자연"],
            "전망대": ["야경", "사진 명소", "자연", "관광지"],
            "사진 명소": ["전망대", "자연", "관광지"],
            "자연": ["관광지", "사진 명소"],
            "문화시설": ["체험", "관광지"],
            "체험": ["문화시설", "관광지"],
            "시장": ["쇼핑", "관광지"],
            "맛집": ["음식점", "시장"],
            "음식점": ["맛집", "시장"],
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
            "route_time_fixed": bool(place.get("route_time_fixed") or place.get("target_time")),
            "route_locked_reason": place.get("route_locked_reason", ""),
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
        move = self._route_score_move(origin, destination, mode)
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
        previous_area = self._place_area(previous)
        candidates.sort(key=lambda row: (
            0 if previous_area and self._place_area(row) == previous_area else 1,
            self._distance_meters(previous, row),
            -self._place_quality_value(row),
        ))
        logs = []
        replacement_limit = (
            self.ROUTE_TRANSIT_FALLBACK_LIMIT
            if mode == "transit" else self.ROUTE_REPLACEMENT_LIMIT
        )
        for candidate in candidates[:replacement_limit]:
            candidate = dict(candidate, requested_category=str(candidate.get("requested_category") or candidate.get("category") or category))
            move, log = self._lookup_move(previous, candidate, mode, iteration + len(logs))
            logs.append(log)
            duration = move.get("duration_minutes")
            if duration is None:
                duration = self._fallback_minutes(previous, candidate, mode)
                move = dict(move or {}, duration_minutes=duration, distance_meters=self._distance_meters(previous, candidate), source="haversine_fallback")
            move = self._prefer_short_walk(previous, candidate, move, mode)
            duration = move.get("duration_minutes")
            if (
                not self._transit_route_unreachable(move, mode)
                and int(duration or 0) <= self._hard_leg_minutes(mode)
            ):
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
                data = self._execute_place_search(args)
                logs.append(self._tool_log("place_search", args, data, iteration + len(logs)))
                nearby_rows = sorted(
                    self._filter_region_candidates(
                        state.get("region") or "", data.get("results") or [], search_category,
                    ),
                    key=lambda row: self._fallback_minutes(previous, row, mode),
                )
                nearby_rows = [
                    row for row in nearby_rows
                    if self._fallback_minutes(previous, row, mode)
                    <= self._hard_leg_minutes(mode)
                ]
                for row in nearby_rows[:replacement_limit]:
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
                    if (
                        not self._transit_route_unreachable(move, mode)
                        and int(duration or 0) <= self._hard_leg_minutes(mode)
                    ):
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

    def _transit_route_unreachable(self, move, mode):
        return bool(
            mode == "transit"
            and int((move or {}).get("external_failed_calls") or 0) > 0
            and not (move or {}).get("actual")
            and str((move or {}).get("source") or "") != "short_walk_connection"
        )

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
        meal_slots = {"breakfast", "lunch", "dinner"}
        meal_days_ok = all(
            not (meal_slots & set(day.get("expected_schedule_slots") or self.REQUIRED_SCHEDULE_SLOTS))
            or meal_slots.intersection({
                str(place.get("schedule_slot") or "") for place in day.get("places") or []
            }) == meal_slots.intersection(
                set(day.get("expected_schedule_slots") or self.REQUIRED_SCHEDULE_SLOTS)
            )
            for day in days
        )
        cafe_days_ok = all(
            "afternoon_cafe" not in set(
                day.get("expected_schedule_slots") or self.REQUIRED_SCHEDULE_SLOTS
            )
            or any(
                str(place.get("schedule_slot") or "") == "afternoon_cafe"
                for place in day.get("places") or []
            )
            for day in days
        )
        mode = self.MODE_MAP.get(state.get("transport"), "transit")
        excessive_days = sum(1 for day in days if int(day.get("total_distance_meters") or 0) > self.MAX_DAY_DISTANCE_METERS[mode])
        route_diagnostics = self._route_quality_diagnostics(state, days)
        route_backtracks = int(route_diagnostics.get("avoidable_backtrack_count") or 0)
        cross_day_backtracks = int(route_diagnostics.get("cross_day_backtrack_count") or 0)
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
                "simple_route_ok": bool(route_diagnostics.get("simple_route_ok")),
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
            "cross_day_backtrack_count": cross_day_backtracks,
            "route_quality_reason": route_diagnostics.get("reasons") or [],
            "route_diagnostics": route_diagnostics,
        }

    def _route_quality_diagnostics(self, state, days):
        mode = self.MODE_MAP.get(state.get("transport"), "transit")
        segments = []
        raw_backtracks = 0
        constrained_backtracks = 0
        avoidable_backtracks = 0
        cross_day_backtracks = 0
        region_changes = 0
        cross_region_jumps = 0
        avoidable_cross_region_jumps = 0
        constrained_cross_region_jumps = 0
        total_distance = 0
        within_day_distance = 0
        total_minutes = 0
        direct_baseline = 0
        day_connections = []
        long_day_connections = 0
        largest = None

        def append_route(route_places, day_number, cross_day=False):
            nonlocal raw_backtracks, constrained_backtracks, avoidable_backtracks
            nonlocal region_changes, cross_region_jumps
            nonlocal avoidable_cross_region_jumps, constrained_cross_region_jumps
            nonlocal total_distance
            nonlocal within_day_distance, total_minutes, largest
            previous_bearing = None
            previous_distance = None
            for index, (one, two) in enumerate(zip(route_places, route_places[1:]), start=1):
                move = two.get("move_from_previous") or {}
                distance = int(move.get("distance_meters") or self._distance_meters(one, two))
                duration = int(move.get("duration_minutes") or self._fallback_minutes(one, two, mode))
                bearing = self._bearing_degrees(one, two)
                direction_change = self._direction_change_degrees(previous_bearing, bearing)
                constrained = bool(
                    one.get("route_locked_reason") or two.get("route_locked_reason")
                    or (
                        one.get("route_time_fixed")
                        and self._category_group(one.get("category")) == "food"
                    )
                    or (
                        two.get("route_time_fixed")
                        and self._category_group(two.get("category")) == "food"
                    )
                )
                backtrack = bool(
                    index >= 2
                    and self._is_significant_backtrack(
                        route_places[index - 2], one, two,
                    )
                )
                # A short local turn on transit is not a meaningful itinerary
                # reversal unless it actually returns to the previous stop's
                # vicinity.  This prevents a 4-minute neighbourhood connector
                # from failing an otherwise compact 3-day route while still
                # rejecting A→B→C→B patterns.
                returns_to_prior = bool(
                    index >= 2
                    and self._distance_meters(route_places[index - 2], two) <= 250
                )
                if (
                    backtrack and mode == "transit" and not constrained and not returns_to_prior
                    and duration <= 5 and distance <= 2000
                ):
                    backtrack = False
                if backtrack:
                    raw_backtracks += 1
                    if constrained:
                        constrained_backtracks += 1
                    else:
                        avoidable_backtracks += 1
                    if largest is None or distance > largest["distance_meters"]:
                        largest = {
                            "day": day_number, "from": one.get("name") or "",
                            "to": two.get("name") or "", "distance_meters": distance,
                            "duration_minutes": duration,
                            "direction_change_degrees": round(direction_change, 1),
                            "constrained": constrained,
                        }
                one_area = self._place_area(one)
                two_area = self._place_area(two)
                area_changed = bool(one_area and two_area and one_area != two_area)
                if area_changed:
                    region_changes += 1
                    jump_limit = 12000 if mode == "transit" else 25000 if mode == "driving" else 5000
                    if distance > jump_limit:
                        cross_region_jumps += 1
                        if constrained:
                            constrained_cross_region_jumps += 1
                        else:
                            avoidable_cross_region_jumps += 1
                segments.append({
                    "day": day_number, "from": one.get("name") or "", "to": two.get("name") or "",
                    "distance_meters": distance, "duration_minutes": duration,
                    "bearing_degrees": round(bearing, 1) if bearing is not None else None,
                    "direction_change_degrees": round(direction_change, 1) if direction_change is not None else None,
                    "backtrack": backtrack, "constrained": constrained,
                    "area_changed": area_changed, "cross_day": cross_day,
                })
                total_distance += distance
                within_day_distance += distance
                total_minutes += duration
                previous_bearing = bearing
                previous_distance = distance

        previous_last = None
        previous_day = None
        for day in days:
            places = list(day.get("places") or [])
            if len(places) >= 2:
                append_route(places, int(day.get("day") or 0))
                direct_baseline += max(
                    self._distance_meters(one, two)
                    for index, one in enumerate(places)
                    for two in places[index + 1:]
                )
            if previous_last and places:
                return_connection = (previous_day or {}).get("accommodation_return_connection") or {}
                start_connection = day.get("start_connection") or day.get("previous_day_connection") or {}
                has_accommodation = bool(return_connection or day.get("accommodation"))
                if has_accommodation:
                    return_distance = int(return_connection.get("distance_meters") or 0)
                    return_minutes = int(return_connection.get("duration_minutes") or 0)
                    start_distance = int(start_connection.get("distance_meters") or 0)
                    start_minutes = int(start_connection.get("duration_minutes") or 0)
                    connection_distance = return_distance + start_distance
                    connection_minutes = return_minutes + start_minutes
                    constraint_reason = "overnight_accommodation"
                else:
                    connection_distance = int(
                        start_connection.get("distance_meters")
                        or self._distance_meters(previous_last, places[0])
                    )
                    connection_minutes = int(
                        start_connection.get("duration_minutes")
                        or self._fallback_minutes(previous_last, places[0], mode)
                    )
                    constraint_reason = "overnight_accommodation_unknown"
                over_limit = max(
                    int(return_connection.get("duration_minutes") or 0),
                    int(start_connection.get("duration_minutes") or connection_minutes),
                ) > self._hard_leg_minutes(mode)
                day_connections.append({
                    "from_day": int(day.get("day") or 1) - 1,
                    "to_day": int(day.get("day") or 1),
                    "distance_meters": connection_distance,
                    "duration_minutes": connection_minutes,
                    "over_limit": over_limit,
                    "constrained": True,
                    "constraint_reason": constraint_reason,
                })
                total_distance += connection_distance
                total_minutes += connection_minutes
                if not has_accommodation and self._boundary_backtrack_count(None, previous_last, places):
                    cross_day_backtracks += 1
            if places:
                previous_last = places[-1]
                previous_day = day

        detour_ratio = round(within_day_distance / max(1, direct_baseline), 2)
        constrained = constrained_backtracks > 0
        large_detour = detour_ratio > 3.0 and not constrained
        reasons = []
        if avoidable_backtracks:
            reasons.append("excessive_backtracking")
        if large_detour:
            reasons.append("large_detour")
        if avoidable_cross_region_jumps:
            reasons.append("cross_region_jump")
        if constrained_backtracks or constrained_cross_region_jumps:
            locked = any(
                place.get("route_locked_reason") for day in days for place in day.get("places") or []
            )
            fixed = any(
                place.get("route_time_fixed")
                and self._category_group(place.get("category")) == "food"
                for day in days for place in day.get("places") or []
            )
            if locked:
                reasons.append("mandatory_stop_constraint")
            if fixed:
                reasons.append("fixed_meal_constraint")
        simple = (
            avoidable_backtracks == 0
            and not large_detour
            and avoidable_cross_region_jumps == 0
        )
        return {
            "simple_route_ok": simple,
            "reasons": self._unique(reasons),
            "total_distance_meters": total_distance,
            "total_move_minutes": total_minutes,
            "segment_count": len(segments),
            "segments": segments,
            "raw_backtrack_count": raw_backtracks,
            "avoidable_backtrack_count": avoidable_backtracks,
            "constrained_backtrack_count": constrained_backtracks,
            "cross_day_backtrack_count": cross_day_backtracks,
            "long_day_connection_count": long_day_connections,
            "largest_backtrack_segment": largest,
            "detour_ratio": detour_ratio,
            "region_change_count": region_changes,
            "cross_region_jump_count": cross_region_jumps,
            "avoidable_cross_region_jump_count": avoidable_cross_region_jumps,
            "constrained_cross_region_jump_count": constrained_cross_region_jumps,
            "day_connection_costs": day_connections,
        }

    def _bearing_degrees(self, origin, destination):
        one = self._coord(origin)
        two = self._coord(destination)
        if not one or not two:
            return None
        lat1 = math.radians(one[0])
        lat2 = math.radians(two[0])
        delta_lng = math.radians(two[1] - one[1])
        y = math.sin(delta_lng) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lng)
        return (math.degrees(math.atan2(y, x)) + 360) % 360

    def _direction_change_degrees(self, previous, current):
        if previous is None or current is None:
            return None
        return abs((current - previous + 180) % 360 - 180)

    def _route_backtrack_count(self, places):
        return len(self._route_backtrack_candidate_indexes(places))

    def _cross_day_backtrack_count(self, days):
        count = 0
        for previous_day, next_day in zip(days, days[1:]):
            previous_places = list(previous_day.get("places") or [])
            next_places = list(next_day.get("places") or [])
            previous_last = previous_places[-1] if previous_places else None
            previous_penultimate = previous_places[-2] if len(previous_places) >= 2 else None
            count += self._boundary_backtrack_count(
                previous_penultimate, previous_last, next_places,
            )
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
        expected = list(
            day.get("expected_schedule_slots") or self.REQUIRED_SCHEDULE_SLOTS
        )
        return [slot for slot in expected if slot not in present]

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

    def _scheduled_gap_minutes(self, previous, current):
        previous_target = self._minutes((previous or {}).get("target_time"), -1)
        current_target = self._minutes((current or {}).get("target_time"), -1)
        if previous_target < 0 or current_target < 0:
            return 0
        return max(0, current_target - previous_target)

    def _normalized_name(self, value):
        return re.sub(r"[^가-힣A-Za-z0-9]", "", str(value or "")).lower()

    def _exact_named_candidate(self, requested, rows, excluded=None):
        """Return only a result whose name strongly identifies the requested place."""
        query = self._normalized_name(requested)
        if not query:
            return None
        excluded = set(excluded or [])
        ranked = []
        for row in rows or []:
            if str(row.get("place_id") or "") in excluded:
                continue
            name = self._normalized_name(row.get("name"))
            if not name:
                continue
            exact = name == query
            contained = len(query) >= 4 and (query in name or name in query)
            shorter = min(len(query), len(name))
            longer = max(len(query), len(name))
            coverage = shorter / max(1, longer)
            if not exact and not (contained and coverage >= 0.72):
                continue
            ranked.append((0 if exact else 1, -coverage, -self._place_quality_value(row), row))
        return min(ranked, key=lambda item: item[:3])[3] if ranked else None

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
            if token.endswith(("구", "군", "읍", "면", "동")):
                return token
        for token in tokens:
            if token.endswith("시"):
                return token
        return tokens[1] if len(tokens) > 1 else (tokens[0] if tokens else "")

    def _place_area(self, place):
        if not isinstance(place, dict):
            return ""
        return str(place.get("admin_area") or self._admin_area(place.get("address"))).strip()

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

    def _execute_place_search(self, arguments):
        started = time.monotonic()
        data = {}
        try:
            data = self.tools.execute_place_search(arguments) or {}
            self._record_place_search_pipeline(arguments, data)
            if data.get("candidate_diagnostics"):
                data = dict(data)
                data.pop("candidate_diagnostics", None)
            return data
        finally:
            self._record_tool_metric("place_search", data, started)

    def _execute_directions_lookup(self, arguments):
        started = time.monotonic()
        data = {}
        try:
            data = self.tools.execute_directions_lookup(arguments) or {}
            return data
        finally:
            self._record_tool_metric("directions_lookup", data, started)

    def _record_tool_metric(self, name, data, started):
        metrics = self._tool_metrics
        if not isinstance(metrics, dict):
            return
        metrics["tool_calls"] = int(metrics.get("tool_calls") or 0) + 1
        key = f"{name}_calls"
        metrics[key] = int(metrics.get(key) or 0) + 1
        metrics["tool_elapsed_ms"] = int(metrics.get("tool_elapsed_ms") or 0) + self._ms(started)
        inferred_external = (
            name == "place_search" and str(data.get("relaxation") or "") == "google_places"
        ) or (
            name == "directions_lookup"
            and str(data.get("source") or "") in ["google_directions", "naver_directions"]
            and str(data.get("cache") or "") != "hit"
        )
        external_requests = int(data.get("external_requests") or (1 if inferred_external else 0))
        successful = int(data.get("external_successful_calls") or (1 if inferred_external else 0))
        failed = int(data.get("external_failed_calls") or 0)
        retried = int(data.get("external_retried_calls") or 0)
        billing = int(data.get("billing_external_requests") or external_requests)
        metrics["external_api_calls"] = int(metrics.get("external_api_calls") or 0) + external_requests
        metrics["successful_external_calls"] = int(metrics.get("successful_external_calls") or 0) + successful
        metrics["failed_external_calls"] = int(metrics.get("failed_external_calls") or 0) + failed
        metrics["retried_external_calls"] = int(metrics.get("retried_external_calls") or 0) + retried
        metrics["billing_external_calls"] = int(metrics.get("billing_external_calls") or 0) + billing
        provider = str(data.get("external_provider") or "").strip()
        if provider and billing:
            provider_requests = metrics.setdefault("external_provider_requests", {})
            provider_requests[provider] = int(provider_requests.get(provider) or 0) + billing
        failure_code = str(data.get("external_provider_failure_code") or "").strip()
        if provider and failure_code:
            provider_failures = metrics.setdefault("external_provider_failures", {})
            key = f"{provider}:{failure_code}"
            provider_failures[key] = int(provider_failures.get(key) or 0) + 1
        if name == "directions_lookup" and str(data.get("external_provider_skip_reason") or ""):
            metrics["provider_skipped_route_calls"] = int(
                metrics.get("provider_skipped_route_calls") or 0
            ) + 1

    def _tool_metrics_payload(self):
        metrics = dict(self._tool_metrics or {})
        for key in [
            "tool_calls", "place_search_calls", "directions_lookup_calls",
            "external_api_calls", "successful_external_calls", "failed_external_calls",
            "retried_external_calls", "total_route_requests", "route_cache_hits",
            "route_cache_misses", "tool_elapsed_ms", "route_optimization_ms",
            "billing_external_calls", "provider_skipped_route_calls",
        ]:
            metrics[key] = int(metrics.get(key) or 0)
        metrics["route_score_cache_entries"] = len(self._route_score_cache)
        metrics.update({
            key: int(value or 0) for key, value in (self._candidate_stats or {}).items()
        })
        return metrics

    def _init_candidate_pipeline(self, state, day_plans):
        self._candidate_pipeline_keys = {
            stage: set() for stage in self.CANDIDATE_PIPELINE_STAGES
        }
        self._candidate_pipeline_category_keys = {}
        slots = []
        for day_index, plan in enumerate(day_plans):
            for slot in plan.get("slots") or []:
                slots.append({
                    "day": day_index + 1,
                    "slot": str(slot.get("key") or ""),
                    "label": str(slot.get("label") or ""),
                    "category": str(slot.get("category") or ""),
                    "pool_candidates": 0,
                    "available_after_dedup": 0,
                    "route_candidates": 0,
                    "transport_checked": 0,
                    "transport_reachable": 0,
                    "preselected_place": "",
                    "assembled_place": "",
                    "outcome": "pending",
                })
        self._candidate_pipeline = {
            "requested_region": str(state.get("region") or ""),
            "transport": str(state.get("transport") or "대중교통"),
            "days": len(day_plans),
            "places_per_day": max(
                [len(plan.get("slots") or []) for plan in day_plans] or [0]
            ),
            "places_by_day": [
                len(plan.get("slots") or []) for plan in day_plans
            ],
            "planned_places_by_day": [
                len(plan.get("slots") or []) for plan in day_plans
            ],
            "required_places": sum(
                len(plan.get("slots") or []) for plan in day_plans
            ),
            "planned_required_places": sum(
                len(plan.get("slots") or []) for plan in day_plans
            ),
            "stage_order": [
                "raw_candidates", "coordinate_validation_passed",
                "category_validation_passed", "region_validation_passed",
                "mandatory_condition_passed", "route_candidates",
                "transport_reachable", "final_selected",
            ],
            "stage_definitions": {
                "raw_candidates": "검색 제공자가 반환하기 전 관측한 원본 후보",
                "coordinate_validation_passed": "위도·경도가 유효한 후보",
                "category_validation_passed": "검색 카테고리 타입 검증을 통과한 후보",
                "region_validation_passed": "요청 지역 좌표·주소 경계를 통과한 후보",
                "mandatory_condition_passed": "슬롯 필수조건을 통과해 사전 선택된 후보",
                "route_candidates": "거리·권역 사전 정렬 후 동선 평가 대상이 된 후보",
                "transport_checked": "실제 또는 캐시된 교통 경로를 검사한 후보",
                "transport_reachable": "교통수단별 한도 안에서 이동 가능한 후보",
                "final_selected": "일자 조립 단계에서 실제 배치된 고유 후보",
            },
            "count_semantics": (
                "단계 count는 요청 안에서 관측된 고유 후보 수이며 observations는 "
                "재검색·카테고리 중복을 포함한 관측 건수입니다."
            ),
            "stage_observations": {stage: 0 for stage in self.CANDIDATE_PIPELINE_STAGES},
            "by_category_observations": {},
            "slots": slots,
            "mandatory_conditions": {
                "requested": len(state.get("must_visit_places") or []),
                "resolved": 0,
                "unresolved": [],
            },
        }

    def _candidate_identity(self, row):
        if not isinstance(row, dict):
            return ""
        identity = str(row.get("place_id") or row.get("provider_place_id") or "").strip()
        if identity:
            return identity
        coord = self._coord(row)
        if coord:
            return f"{row.get('name') or ''}:{coord[0]:.5f}:{coord[1]:.5f}"
        return str(row.get("name") or "").strip()

    def _record_candidate_keys(self, stage, keys, category="", observations=None):
        if stage not in self._candidate_pipeline_keys:
            return
        clean_keys = {str(key) for key in keys or [] if str(key)}
        self._candidate_pipeline_keys[stage].update(clean_keys)
        observed = len(clean_keys) if observations is None else max(0, int(observations or 0))
        stage_observations = self._candidate_pipeline.get("stage_observations") or {}
        stage_observations[stage] = int(stage_observations.get(stage) or 0) + observed
        category = str(category or "").strip()
        if not category:
            return
        category_keys = self._candidate_pipeline_category_keys.setdefault(category, {})
        category_keys.setdefault(stage, set()).update(clean_keys)
        category_observations = self._candidate_pipeline.setdefault(
            "by_category_observations", {}
        ).setdefault(category, {})
        category_observations[stage] = int(category_observations.get(stage) or 0) + observed

    def _record_candidate_rows(self, stage, rows, category=""):
        rows = list(rows or [])
        keys = [self._candidate_identity(row) for row in rows]
        self._record_candidate_keys(stage, keys, category, observations=len(rows))

    def _record_place_search_pipeline(self, arguments, data):
        category = str((arguments or {}).get("category") or "")
        diagnostics = data.get("candidate_diagnostics") or {}
        results = list(data.get("results") or [])
        mappings = [
            ("raw_candidates", "raw_candidate_keys", "raw_candidate_count"),
            (
                "coordinate_validation_passed",
                "coordinate_validation_passed_keys",
                "coordinate_validation_passed_count",
            ),
            (
                "category_validation_passed",
                "category_validation_passed_keys",
                "category_validation_passed_count",
            ),
        ]
        if diagnostics:
            for stage, key_field, count_field in mappings:
                self._record_candidate_keys(
                    stage, diagnostics.get(key_field) or [], category,
                    observations=diagnostics.get(count_field),
                )
        else:
            self._record_candidate_rows("raw_candidates", results, category)
            self._record_candidate_rows(
                "coordinate_validation_passed",
                [row for row in results if self._coord(row)], category,
            )
            self._record_candidate_rows("category_validation_passed", results, category)

    def _active_slot_category(self):
        return str((self._active_candidate_slot or {}).get("category") or "")

    def _slot_pipeline_entry(self, day=None, slot=None):
        active = self._active_candidate_slot or {}
        day = int(day or active.get("day") or 0)
        slot = str(slot or active.get("slot") or "")
        return next((
            row for row in self._candidate_pipeline.get("slots") or []
            if int(row.get("day") or 0) == day and str(row.get("slot") or "") == slot
        ), None)

    def _record_slot_pool(self, day, slot, rows, used):
        entry = self._slot_pipeline_entry(day, slot.get("key"))
        if not entry:
            return
        rows = list(rows or [])
        entry["pool_candidates"] = len({
            self._candidate_identity(row) for row in rows if self._candidate_identity(row)
        })
        entry["available_after_dedup"] = len({
            self._candidate_identity(row) for row in rows
            if self._candidate_identity(row) and not self._is_used(row, used)
        })

    def _record_slot_candidates(self, field, rows):
        entry = self._slot_pipeline_entry()
        if not entry:
            return
        hidden = f"_{field}_keys"
        values = entry.setdefault(hidden, set())
        values.update(
            self._candidate_identity(row) for row in rows or []
            if self._candidate_identity(row)
        )
        entry[field] = len(values)

    def _record_slot_result(self, day, slot, candidate, outcome):
        entry = self._slot_pipeline_entry(day, slot.get("key"))
        if not entry:
            return
        if candidate:
            entry["preselected_place"] = str(candidate.get("name") or "")
        entry["outcome"] = outcome

    def _record_slot_outcome_for_place(self, place, outcome):
        entry = self._slot_pipeline_entry(
            (self._active_candidate_slot or {}).get("day"),
            str((place or {}).get("itinerary_slot") or ""),
        )
        if entry:
            entry["outcome"] = outcome

    def _record_transport_candidate(self, origin, destination, move, mode):
        category = self._active_slot_category() or str(
            (destination or {}).get("requested_category")
            or (destination or {}).get("category") or ""
        )
        self._record_candidate_rows("transport_checked", [destination], category)
        self._record_slot_candidates("transport_checked", [destination])
        evaluated = self._prefer_short_walk(origin, destination, move, mode)
        duration = int(evaluated.get("duration_minutes") or 0)
        reachable = (
            not self._transit_route_unreachable(evaluated, mode)
            and duration <= self._hard_leg_minutes(mode)
        )
        if reachable:
            self._record_candidate_rows("transport_reachable", [destination], category)
            self._record_slot_candidates("transport_reachable", [destination])

    def _record_assembled_day(self, day, assembled):
        for place in assembled.get("places") or []:
            slot = str(place.get("schedule_slot") or "")
            entry = self._slot_pipeline_entry(day, slot)
            if entry:
                entry["assembled_place"] = str(place.get("name") or "")
                entry["outcome"] = "assembled"
            self._record_candidate_rows(
                "final_selected", [place], str(place.get("category") or ""),
            )

    def _candidate_pipeline_payload(
        self, requested_days, itinerary_days, shortage_categories,
        missing_days, missing_slots, returned,
    ):
        stages = {}
        observations = self._candidate_pipeline.get("stage_observations") or {}
        for stage in self.CANDIDATE_PIPELINE_STAGES:
            stages[stage] = {
                "count": len(self._candidate_pipeline_keys.get(stage) or set()),
                "observations": int(observations.get(stage) or 0),
            }
        by_category = {}
        category_observations = self._candidate_pipeline.get("by_category_observations") or {}
        categories = set(category_observations) | set(self._candidate_pipeline_category_keys)
        for category in sorted(categories):
            by_category[category] = {}
            for stage in self.CANDIDATE_PIPELINE_STAGES:
                keys = (
                    self._candidate_pipeline_category_keys.get(category, {}).get(stage)
                    or set()
                )
                seen = int(category_observations.get(category, {}).get(stage) or 0)
                if keys or seen:
                    by_category[category][stage] = {
                        "count": len(keys), "observations": seen,
                    }
        slots = []
        for source in self._candidate_pipeline.get("slots") or []:
            row = {
                key: value for key, value in source.items() if not str(key).startswith("_")
            }
            if row.get("outcome") == "pending":
                row["outcome"] = "not_reached"
            slots.append(row)
        completed_day_selection_count = sum(
            len(day.get("places") or []) for day in itinerary_days or []
        )
        assembled_count = int(
            (self._candidate_pipeline.get("stage_observations") or {}).get("final_selected")
            or 0
        )
        payload = {
            key: value for key, value in self._candidate_pipeline.items()
            if key not in ["stage_observations", "by_category_observations", "slots"]
        }
        mandatory = dict(payload.get("mandatory_conditions") or {})
        mandatory["resolved"] = max(
            0, int(mandatory.get("requested") or 0)
            - len(mandatory.get("unresolved") or []),
        )
        payload.update({
            "stages": stages,
            "by_category": by_category,
            "slots": slots,
            "mandatory_conditions": mandatory,
            "assembled_selection_count": assembled_count,
            "completed_day_selection_count": completed_day_selection_count,
            "returned_final_selection_count": completed_day_selection_count if returned else 0,
            "missing_categories": self._unique(shortage_categories),
            "missing_days": self._unique(missing_days),
            "missing_slots": list(missing_slots or []),
            "complete": bool(returned and len(itinerary_days or []) == requested_days),
        })
        final_places_by_day = [
            len(day.get("places") or []) for day in itinerary_days or []
        ]
        payload["final_places_by_day"] = final_places_by_day
        if returned:
            payload["places_by_day"] = final_places_by_day
            payload["required_places"] = sum(final_places_by_day)
        return payload

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
            if isinstance(row, (tuple, list)) and len(row) >= 2:
                return float(row[0]), float(row[1])
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

    def _filter_region_candidates(self, requested_region, rows, category=""):
        rows = list(rows or [])
        accepted = [row for row in rows if self._candidate_in_region(requested_region, row)]
        requested_category = str(category or self._active_slot_category() or "")
        self._record_candidate_rows("region_validation_passed", accepted, requested_category)
        self._record_candidate_rows(
            "coordinate_validation_passed_after_region",
            [row for row in accepted if self._coord(row)], requested_category,
        )
        stats = self._candidate_stats
        if isinstance(stats, dict):
            stats["raw_candidate_count"] = int(stats.get("raw_candidate_count") or 0) + len(rows)
            stats["eligible_candidate_count"] = int(stats.get("eligible_candidate_count") or 0) + len(accepted)
            stats["region_mismatch_count"] = int(stats.get("region_mismatch_count") or 0) + len(rows) - len(accepted)
        return accepted

    def _candidate_in_region(self, requested_region, row):
        region = str(requested_region or "").strip()
        bounds = self.REGION_BOUNDS.get(region)
        coord = self._coord(row)
        if bounds and coord:
            min_lat, max_lat, min_lng, max_lng = bounds
            return min_lat <= coord[0] <= max_lat and min_lng <= coord[1] <= max_lng
        if not bounds:
            return True
        text = " ".join([
            str(row.get("address") or ""), str(row.get("area") or ""),
            str(row.get("admin_area") or ""), str(row.get("name") or ""),
        ])
        aliases = {
            "제주": ["제주", "서귀포"], "제주도": ["제주", "서귀포"],
            "제주특별자치도": ["제주", "서귀포"],
            "서울": ["서울"], "서울특별시": ["서울"],
            "백령도": ["백령도", "백령면"],
        }
        return any(token in text for token in aliases.get(region, [region]))

    def _pool_candidate_count(self, pools, must_visit_results=None):
        ids = {
            str(row.get("place_id") or "")
            for rows in (pools or {}).values()
            for row in rows or []
            if str(row.get("place_id") or "")
        }
        ids.update(
            str(row.get("place_id") or "") for row in must_visit_results or []
            if str(row.get("place_id") or "")
        )
        return len(ids)

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
