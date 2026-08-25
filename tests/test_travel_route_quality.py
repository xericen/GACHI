import unittest
from unittest.mock import patch

from tests.test_ai_harness import FixtureAiTools, IntegrationModelLoader, ModelLoader


class OutOfRegionTools(FixtureAiTools):
    def execute_place_search(self, arguments):
        data = super().execute_place_search(arguments)
        for row in data.get("results") or []:
            row.update({"lat": 37.48, "lng": 126.70, "address": "인천광역시 육지"})
        return data


class UnreachableTools(FixtureAiTools):
    def execute_place_search(self, arguments):
        data = super().execute_place_search(arguments)
        for index, row in enumerate(data.get("results") or [], start=1):
            row.update({"lat": 37.43 + index * 0.025, "lng": 126.76 + index * 0.025})
        return data


class DestinationAwareDirectionsTools(FixtureAiTools):
    def execute_directions_lookup(self, arguments):
        self.direction_calls.append(dict(arguments or {}))
        destination = str(arguments.get("destination_place_id") or "")
        minutes = 12 if destination == "reachable-3" else 55
        return {
            "status": "ok", "source": "fixture", "duration_minutes": minutes,
            "distance_meters": minutes * 1000,
        }


class PairAwareDirectionsTools(FixtureAiTools):
    def execute_directions_lookup(self, arguments):
        self.direction_calls.append(dict(arguments or {}))
        origin = str(arguments.get("origin_place_id") or "")
        destination = str(arguments.get("destination_place_id") or "")
        minutes = {
            ("anchor", "near-dead-end"): 10,
            ("near-dead-end", "next"): 60,
            ("anchor", "paired-route"): 20,
            ("paired-route", "next"): 15,
        }.get((origin, destination), 20)
        return {
            "status": "ok", "source": "fixture", "duration_minutes": minutes,
            "distance_meters": minutes * 1000,
        }


class TravelRouteQualityTest(unittest.TestCase):
    def setUp(self):
        loader = IntegrationModelLoader()
        self.Engine = loader.model("agents/travel_itinerary_engine")
        self.State = loader.model("agents/travel_planner_state")

    def state(self, region="서울", days=1, transport="대중교통"):
        machine = self.State()
        return machine.apply_generation_defaults(machine.normalize({
            "region": region,
            "destination": region,
            "days": days,
            "transport": transport,
            "preferences": ["문화", "맛집", "카페"],
        }))

    def test_region_boundaries_reject_cross_region_candidates(self):
        engine = self.Engine(FixtureAiTools())
        self.assertFalse(engine._candidate_in_region("제주", {
            "lat": 37.5, "lng": 127.0, "address": "서울특별시",
        }))
        self.assertFalse(engine._candidate_in_region("백령도", {
            "lat": 37.48, "lng": 126.70, "address": "인천광역시 육지",
        }))
        self.assertFalse(engine._candidate_in_region("서울", {
            "lat": 33.49, "lng": 126.52, "address": "제주특별자치도",
        }))
        self.assertTrue(engine._candidate_in_region("백령도", {
            "lat": 37.96, "lng": 124.66, "address": "인천광역시 옹진군 백령면",
        }))

    def test_only_out_of_region_candidates_returns_region_mismatch(self):
        result = self.Engine(OutOfRegionTools()).generate(self.state("백령도"))

        self.assertFalse(result["ok"])
        reason = result["failure_reason"]
        self.assertEqual("region_candidate_mismatch", reason["code"])
        self.assertGreater(reason["region_mismatch_count"], 0)
        self.assertEqual(0, reason["eligible_candidate_count"])

    def test_unreachable_mandatory_stop_has_specific_failure_code(self):
        state = self.state("백령도")
        state["must_visit_places"] = ["백령도 필수 장소"]
        result = self.Engine(OutOfRegionTools()).generate(state)

        self.assertFalse(result["ok"])
        self.assertEqual("mandatory_stop_unreachable", result["failure_reason"]["code"])
        self.assertEqual(["백령도 필수 장소"], result["failure_reason"]["mandatory_stops"])

    def test_mandatory_stop_requires_strong_name_match(self):
        engine = self.Engine(FixtureAiTools())
        rows = [
            {"place_id": "wrong", "name": "허준근린공원", "rating": 5.0},
            {"place_id": "exact", "name": "충무공 이순신 동상", "rating": 4.5},
        ]

        selected = engine._exact_named_candidate("충무공이순신동상", rows)

        self.assertEqual("exact", selected["place_id"])
        self.assertIsNone(engine._exact_named_candidate(
            "충무공 이순신 동상", rows[:1],
        ))

    def test_unreachable_candidates_remain_structured_failure(self):
        tools = UnreachableTools()
        tools.direction_minutes = 999
        engine = self.Engine(tools)
        engine._prefer_short_walk = lambda origin, destination, move, requested_mode: move
        result = engine.generate(self.state("서울"))

        self.assertFalse(result["ok"])
        reason = result["failure_reason"]
        self.assertEqual("insufficient_route_candidates", reason["code"])
        self.assertTrue(reason["missing_categories"])
        self.assertTrue(reason["missing_slots"])
        for key in [
            "requested_region", "days", "transport", "candidate_count",
            "eligible_candidate_count", "route_reachable_candidate_count",
            "missing_categories", "missing_days", "missing_slots", "failure_reason",
        ]:
            self.assertIn(key, reason)

        pipeline = result["metadata"]["candidate_pipeline"]
        self.assertEqual(7, pipeline["required_places"])
        self.assertGreater(pipeline["stages"]["raw_candidates"]["count"], 0)
        self.assertGreater(
            pipeline["stages"]["region_validation_passed"]["count"], 0,
        )
        self.assertEqual(7, len(pipeline["slots"]))
        self.assertTrue(pipeline["missing_slots"])

    def test_candidate_pipeline_records_each_requested_stage(self):
        result = self.Engine(FixtureAiTools()).generate(self.state("서울"))

        self.assertTrue(result["ok"])
        pipeline = result["metadata"]["candidate_pipeline"]
        for stage in [
            "raw_candidates", "region_validation_passed",
            "coordinate_validation_passed", "transport_reachable",
            "category_validation_passed", "mandatory_condition_passed",
            "route_candidates", "final_selected",
        ]:
            self.assertIn(stage, pipeline["stages"])
            self.assertIn("count", pipeline["stages"][stage])
            self.assertIn("observations", pipeline["stages"][stage])
        self.assertEqual(7, pipeline["returned_final_selection_count"])
        self.assertFalse(pipeline["missing_categories"])
        self.assertFalse(pipeline["missing_days"])
        self.assertTrue(all(row["outcome"] == "assembled" for row in pipeline["slots"]))

    def test_partial_arrival_and_departure_use_only_feasible_daily_slots(self):
        state = self.state("제주", days=3, transport="대중교통")
        state.update({"arrival_time": "17:00", "departure_time": "11:00"})

        result = self.Engine(FixtureAiTools()).generate(state)

        self.assertTrue(result["ok"])
        days = result["draft"]["days"]
        self.assertEqual([2, 7, 1], [len(day["places"]) for day in days])
        self.assertEqual(
            [["dinner", "evening_activity"], self.Engine.REQUIRED_SCHEDULE_SLOTS, ["breakfast"]],
            [day["expected_schedule_slots"] for day in days],
        )
        pipeline = result["metadata"]["candidate_pipeline"]
        self.assertEqual([2, 7, 1], pipeline["places_by_day"])
        self.assertEqual(10, pipeline["required_places"])
        self.assertEqual(10, pipeline["returned_final_selection_count"])
        self.assertTrue(result["draft"]["quality"]["checks"]["schedule_complete"])
        self.assertTrue(result["draft"]["quality"]["checks"]["daily_meals_ok"])

    def test_full_day_default_keeps_seven_slots(self):
        result = self.Engine(FixtureAiTools()).generate(self.state("제주", days=3))

        self.assertTrue(result["ok"])
        self.assertEqual([7, 7, 7], [
            len(day["expected_schedule_slots"]) for day in result["draft"]["days"]
        ])

    def test_visit_count_changes_with_available_trip_time(self):
        cases = [
            ("17:00", "11:00", [2, 7, 1]),
            ("15:00", "13:00", [3, 7, 2]),
            ("12:00", "18:00", [5, 7, 5]),
            ("10:00", "21:30", [7, 7, 7]),
        ]

        for arrival, departure, expected in cases:
            with self.subTest(arrival=arrival, departure=departure):
                state = self.state("제주", days=3)
                state.update({"arrival_time": arrival, "departure_time": departure})
                engine = self.Engine(FixtureAiTools())
                plans = [engine._day_plan(state, index, 3) for index in range(3)]
                self.assertEqual(expected, [len(plan["slots"]) for plan in plans])

    def test_actual_travel_time_can_reduce_optional_visit_count(self):
        tools = FixtureAiTools()
        tools.direction_minutes = 45
        engine = self.Engine(tools)
        engine._prefer_short_walk = lambda origin, destination, move, requested_mode: move
        state = self.state("제주", days=1)
        state.update({"arrival_time": "11:30", "departure_time": "18:00"})

        result = engine.generate(state)

        self.assertTrue(result["ok"])
        day = result["draft"]["days"][0]
        self.assertEqual(4, day["planned_place_count"])
        self.assertEqual(3, day["final_place_count"])
        self.assertEqual(
            [{"slot": "afternoon_activity", "reason": "time_window_exceeded"}],
            day["omitted_schedule_slots"],
        )
        pipeline = result["metadata"]["candidate_pipeline"]
        self.assertEqual([4], pipeline["planned_places_by_day"])
        self.assertEqual([3], pipeline["final_places_by_day"])
        self.assertEqual(3, pipeline["required_places"])

    def test_route_cache_reuses_same_transport_and_normalized_coordinates(self):
        tools = FixtureAiTools()
        engine = self.Engine(tools)
        origin = {"place_id": "a", "lat": 37.500001, "lng": 127.000001}
        destination = {"place_id": "b", "lat": 37.510001, "lng": 127.010001}

        first = engine._route_score_move(origin, destination, "transit")
        second = engine._route_score_move(origin, destination, "transit")

        self.assertEqual(first["duration_minutes"], second["duration_minutes"])
        self.assertEqual(1, len(tools.direction_calls))
        self.assertEqual(2, engine._tool_metrics["total_route_requests"])
        self.assertEqual(1, engine._tool_metrics["route_cache_hits"])
        self.assertEqual(1, engine._tool_metrics["route_cache_misses"])

    def test_transit_candidate_search_expands_until_reachable_candidate(self):
        tools = DestinationAwareDirectionsTools()
        engine = self.Engine(tools)
        engine._tool_metrics = {
            "total_route_requests": 0, "route_cache_hits": 0,
            "route_cache_misses": 0,
        }
        engine._candidate_stats = {"candidate_evaluations": 0, "route_evaluations": 0}
        anchor = {"place_id": "anchor", "lat": 37.50, "lng": 127.00}
        candidates = [
            {
                "place_id": f"reachable-{index}", "name": f"후보 {index}",
                "lat": 37.50, "lng": 127.00 + 0.03 * index, "category": "맛집",
            }
            for index in range(1, 5)
        ]

        picked = engine._pick_easy_route_candidate(
            candidates, set(), anchor, None, [], self.state("서울"),
        )

        self.assertEqual("reachable-3", picked["place_id"])
        self.assertEqual(3, len(tools.direction_calls))

    def test_transit_candidate_uses_verified_soft_limit_but_rejects_hard_limit(self):
        tools = DestinationAwareDirectionsTools()
        engine = self.Engine(tools)
        engine._tool_metrics = {
            "total_route_requests": 0, "route_cache_hits": 0,
            "route_cache_misses": 0,
        }
        engine._candidate_stats = {"candidate_evaluations": 0, "route_evaluations": 0}
        anchor = {"place_id": "anchor", "lat": 37.50, "lng": 127.00}
        state = self.state("서울")

        tools.execute_directions_lookup = lambda arguments: {
            "status": "ok", "source": "fixture", "duration_minutes": 40,
            "distance_meters": 5000,
        }
        accepted = engine._pick_easy_route_candidate([
            {"place_id": "soft", "lat": 37.51, "lng": 127.01},
        ], set(), anchor, None, [], state)
        self.assertEqual("soft", accepted["place_id"])

        engine._route_score_cache = {}
        tools.execute_directions_lookup = lambda arguments: {
            "status": "ok", "source": "fixture", "duration_minutes": 50,
            "distance_meters": 5000,
        }
        rejected = engine._pick_easy_route_candidate([
            {"place_id": "hard", "lat": 37.51, "lng": 127.01},
        ], set(), anchor, None, [], state)
        self.assertIsNone(rejected)

    def test_transit_candidate_requires_reachable_next_slot_pair(self):
        tools = PairAwareDirectionsTools()
        engine = self.Engine(tools)
        engine._tool_metrics = {
            "total_route_requests": 0, "route_cache_hits": 0,
            "route_cache_misses": 0,
        }
        engine._candidate_stats = {"candidate_evaluations": 0, "route_evaluations": 0}
        anchor = {"place_id": "anchor", "lat": 37.50, "lng": 127.00}
        candidates = [
            {"place_id": "near-dead-end", "lat": 37.501, "lng": 127.001},
            {"place_id": "paired-route", "lat": 37.502, "lng": 127.002},
        ]
        next_rows = [{"place_id": "next", "lat": 37.503, "lng": 127.003}]

        picked = engine._pick_easy_route_candidate(
            candidates, set(), anchor, None, next_rows, self.state("서울"),
        )

        self.assertEqual("paired-route", picked["place_id"])

    def test_lookahead_does_not_pair_candidate_with_itself(self):
        tools = PairAwareDirectionsTools()

        def directions(arguments):
            tools.direction_calls.append(dict(arguments or {}))
            pair = (
                str(arguments.get("origin_place_id") or ""),
                str(arguments.get("destination_place_id") or ""),
            )
            minutes = {
                ("anchor", "overlap"): 5,
                ("overlap", "overlap"): 1,
                ("overlap", "next"): 60,
                ("anchor", "paired"): 10,
                ("paired", "next"): 15,
            }.get(pair, 60)
            return {
                "status": "ok", "source": "fixture",
                "duration_minutes": minutes, "distance_meters": minutes * 1000,
            }

        tools.execute_directions_lookup = directions
        engine = self.Engine(tools)
        engine._tool_metrics = {
            "total_route_requests": 0, "route_cache_hits": 0,
            "route_cache_misses": 0,
        }
        engine._candidate_stats = {"candidate_evaluations": 0, "route_evaluations": 0}
        anchor = {"place_id": "anchor", "lat": 37.50, "lng": 127.00}
        overlap = {"place_id": "overlap", "lat": 37.501, "lng": 127.001}
        paired = {"place_id": "paired", "lat": 37.502, "lng": 127.002}
        next_row = {"place_id": "next", "lat": 37.503, "lng": 127.003}

        picked = engine._pick_easy_route_candidate(
            [overlap, paired], set(), anchor, None,
            [overlap, next_row], self.state("서울"),
        )

        self.assertEqual("paired", picked["place_id"])
        self.assertNotIn(("overlap", "overlap"), {
            (
                str(call.get("origin_place_id") or ""),
                str(call.get("destination_place_id") or ""),
            )
            for call in tools.direction_calls
        })

    def test_dead_end_pair_replaces_previous_stop_before_dropping_next_slot(self):
        tools = PairAwareDirectionsTools()

        def directions(arguments):
            tools.direction_calls.append(dict(arguments or {}))
            pair = (
                str(arguments.get("origin_place_id") or ""),
                str(arguments.get("destination_place_id") or ""),
            )
            minutes = {
                ("anchor", "original"): 10,
                ("original", "next"): 60,
                ("anchor", "replacement"): 15,
                ("replacement", "next"): 15,
            }.get(pair, 60)
            return {
                "status": "ok", "source": "fixture",
                "duration_minutes": minutes, "distance_meters": minutes * 1000,
            }

        tools.execute_directions_lookup = directions
        engine = self.Engine(tools)
        engine._tool_metrics = {
            "total_route_requests": 0, "route_cache_hits": 0,
            "route_cache_misses": 0,
        }
        engine._candidate_stats = {"candidate_evaluations": 0, "route_evaluations": 0}
        anchor = {"place_id": "anchor", "lat": 37.50, "lng": 127.00}
        original = {
            "place_id": "original", "category": "맛집",
            "requested_category": "맛집", "lat": 37.501, "lng": 127.001,
        }
        replacement = {
            "place_id": "replacement", "category": "맛집",
            "lat": 37.502, "lng": 127.002,
        }
        next_row = {
            "place_id": "next", "category": "전망대",
            "lat": 37.503, "lng": 127.003,
        }
        selected = [anchor, original]
        used = {"anchor", "original"}

        recovered = engine._recover_dead_end_pair(
            self.state("서울"), "전망대",
            {"맛집": [original, replacement], "전망대": [next_row]},
            selected, used,
        )

        self.assertEqual("next", recovered["place_id"])
        self.assertEqual("replacement", selected[-1]["place_id"])
        self.assertNotIn("original", used)
        self.assertIn("replacement", used)

    def test_internal_market_candidate_does_not_require_external_place_types(self):
        tools = ModelLoader().model("ai_tools")
        tools._query_places = lambda **kwargs: [{
            "place_id": "internal-market",
            "name": "제주 동문시장",
            "category": "시장",
        }]

        result = tools.execute_place_search({"region": "제주", "category": "시장"})

        self.assertEqual("ok", result["status"])
        self.assertEqual("internal-market", result["results"][0]["place_id"])

    def test_backtracking_route_is_rejected_with_diagnostics(self):
        engine = self.Engine(FixtureAiTools())
        places = [
            {"name": "A", "lat": 37.5, "lng": 127.00},
            {"name": "B", "lat": 37.5, "lng": 127.01},
            {"name": "C", "lat": 37.5, "lng": 127.02},
            {"name": "B2", "lat": 37.5, "lng": 127.01},
            {"name": "D", "lat": 37.5, "lng": 127.03},
        ]
        diagnostics = engine._route_quality_diagnostics(
            self.state(), [{"day": 1, "places": places}],
        )

        self.assertFalse(diagnostics["simple_route_ok"])
        self.assertGreater(diagnostics["avoidable_backtrack_count"], 0)
        self.assertIn("excessive_backtracking", diagnostics["reasons"])
        self.assertIsNotNone(diagnostics["largest_backtrack_segment"])

    def test_sharp_local_turn_without_material_return_is_not_backtracking(self):
        engine = self.Engine(FixtureAiTools())
        places = [
            {"name": "A", "lat": 37.5, "lng": 127.00},
            {"name": "B", "lat": 37.5, "lng": 127.05},
            {"name": "C", "lat": 37.5002, "lng": 127.046},
        ]

        self.assertEqual(0, engine._route_backtrack_count(places))

    def test_short_transit_neighbourhood_turn_is_not_route_quality_failure(self):
        engine = self.Engine(FixtureAiTools())
        places = [
            {"name": "A", "lat": 37.50, "lng": 127.00},
            {"name": "B", "lat": 37.51, "lng": 127.01,
             "move_from_previous": {"distance_meters": 1600, "duration_minutes": 4}},
            {"name": "C", "lat": 37.505, "lng": 126.995,
             "move_from_previous": {"distance_meters": 1700, "duration_minutes": 4}},
        ]

        diagnostics = engine._route_quality_diagnostics(
            self.state(transport="대중교통"), [{"day": 1, "places": places}],
        )

        self.assertEqual(0, diagnostics["avoidable_backtrack_count"])
        self.assertTrue(diagnostics["simple_route_ok"])

    def test_large_detour_without_reverse_turn_is_rejected(self):
        engine = self.Engine(FixtureAiTools())
        ring = [
            (37.50, 127.05), (37.535355, 127.035355),
            (37.55, 127.00), (37.535355, 126.964645),
            (37.50, 126.95), (37.464645, 126.964645),
            (37.45, 127.00), (37.464645, 127.035355),
            (37.50, 127.05),
        ]
        places = [
            {"name": f"P{index}", "lat": lat, "lng": lng}
            for index, (lat, lng) in enumerate(ring + ring[1:])
        ]
        diagnostics = engine._route_quality_diagnostics(
            self.state(), [{"day": 1, "places": places}],
        )

        self.assertFalse(diagnostics["simple_route_ok"])
        self.assertGreater(diagnostics["detour_ratio"], 3.0)
        self.assertIn("large_detour", diagnostics["reasons"])

    def test_detour_repair_targets_the_largest_removable_stop(self):
        engine = self.Engine(FixtureAiTools())
        ring = [
            (37.50, 127.05), (37.535355, 127.035355),
            (37.55, 127.00), (37.535355, 126.964645),
            (37.50, 126.95), (37.464645, 126.964645),
            (37.45, 127.00), (37.464645, 127.035355),
            (37.50, 127.05),
        ]
        selected = [
            {"place_id": f"p{index}", "lat": lat, "lng": lng}
            for index, (lat, lng) in enumerate(ring + ring[1:])
        ]
        day = {
            "places": selected,
            "total_distance_meters": 5000,
        }

        self.assertGreater(engine._day_route_objective(day)[0], 0)
        self.assertEqual(0, engine._route_backtrack_count(selected))
        detour_targets = engine._route_detour_candidate_indexes(selected)
        self.assertTrue(detour_targets)
        self.assertEqual(
            detour_targets[0], engine._repair_target_index(selected, day=day),
        )

    def test_cross_region_jump_is_a_repair_target(self):
        engine = self.Engine(FixtureAiTools())
        selected = [
            {"place_id": "a", "name": "A", "address": "서울 강남구", "lat": 37.50, "lng": 127.00},
            {"place_id": "jump", "name": "B", "address": "서울 마포구", "lat": 37.60, "lng": 126.80,
             "move_from_previous": {"distance_meters": 25000}},
            {"place_id": "c", "name": "C", "address": "서울 마포구", "lat": 37.61, "lng": 126.81,
             "move_from_previous": {"distance_meters": 1200}},
        ]
        day = {"places": selected, "total_distance_meters": 26200}

        self.assertEqual([1], engine._route_cross_region_candidate_indexes(selected, "transit"))
        self.assertEqual(1, engine._repair_target_index(selected, day=day, mode="transit"))
        self.assertGreater(engine._day_route_objective(day, "transit")[0], 0)

    def test_route_repair_retries_same_slot_after_non_improving_candidate(self):
        engine = self.Engine(FixtureAiTools())
        selected = [
            {"place_id": "a", "category": "관광지"},
            {"place_id": "original", "category": "관광지"},
            {"place_id": "c", "category": "관광지"},
        ]
        pools = {"관광지": [
            {"place_id": "bad", "category": "관광지"},
            {"place_id": "good", "category": "관광지"},
        ]}
        picked = iter(pools["관광지"])
        engine._repair_target_index = lambda *args, **kwargs: 1
        engine._pick_easy_route_candidate = lambda *args, **kwargs: next(picked)
        engine._search_nearby = lambda *args, **kwargs: (None, [], [])
        engine._missing_schedule_slots = lambda day: []
        engine._day_route_objective = lambda day, *_args: {
            "current": (1, 1, 0, 5.41, 16000),
            "bad": (1, 1, 0, 5.60, 17000),
            "good": (0, 0, 0, 2.40, 12000),
        }[day["kind"]]

        def assemble(_state, _day_index, _total_days, trial, **kwargs):
            kind = str(trial[1].get("place_id") or "")
            return {
                "kind": kind,
                "places": trial,
                "total_distance_meters": 12000 if kind == "good" else 17000,
            }, [], []

        engine._assemble_day = assemble
        repaired, repaired_selected, _, _, optimization = engine._repair_simple_route(
            self.state(), 0, 1,
            {"kind": "current", "places": selected, "total_distance_meters": 16000},
            selected, pools, {"a", "original", "c"}, {"slots": []},
        )

        self.assertEqual("good", repaired["kind"])
        self.assertEqual("good", repaired_selected[1]["place_id"])
        self.assertEqual(2, optimization["attempts"])
        self.assertTrue(optimization["improved"])
        self.assertEqual("optimized", optimization["status"])

    def test_mandatory_and_fixed_meal_detour_is_reported_but_allowed(self):
        engine = self.Engine(FixtureAiTools())
        places = [
            {"name": "A", "category": "관광지", "lat": 37.5, "lng": 127.00},
            {
                "name": "필수", "category": "관광지", "lat": 37.5, "lng": 127.02,
                "route_locked_reason": "must_visit",
            },
            {
                "name": "고정 점심", "category": "맛집", "lat": 37.5, "lng": 127.01,
                "route_time_fixed": True,
            },
            {"name": "D", "category": "관광지", "lat": 37.5, "lng": 127.03},
        ]
        diagnostics = engine._route_quality_diagnostics(
            self.state(), [{"day": 1, "places": places}],
        )

        self.assertTrue(diagnostics["simple_route_ok"])
        self.assertGreater(diagnostics["constrained_backtrack_count"], 0)
        self.assertIn("mandatory_stop_constraint", diagnostics["reasons"])
        self.assertIn("fixed_meal_constraint", diagnostics["reasons"])

    def test_locked_cross_region_jump_is_reported_but_not_failed(self):
        engine = self.Engine(FixtureAiTools())
        places = [
            {"name": "A", "address": "서울 강남구", "lat": 37.50, "lng": 127.00},
            {"name": "필수", "address": "서울 마포구", "lat": 37.60, "lng": 126.80,
             "route_locked_reason": "must_visit",
             "move_from_previous": {"distance_meters": 25000, "duration_minutes": 40}},
        ]

        diagnostics = engine._route_quality_diagnostics(
            self.state(), [{"day": 1, "places": places}],
        )

        self.assertTrue(diagnostics["simple_route_ok"])
        self.assertEqual(1, diagnostics["constrained_cross_region_jump_count"])
        self.assertEqual(0, diagnostics["avoidable_cross_region_jump_count"])
        self.assertIn("mandatory_stop_constraint", diagnostics["reasons"])

    def test_transit_provider_billing_counts_actual_http_once_then_cache_hit(self):
        tools = ModelLoader().model("ai_tools")
        tools._direction_cache = {}
        tools._get_place = lambda place_id: {
            "latitude": 37.50 if place_id == "a" else 37.51,
            "longitude": 127.00 if place_id == "a" else 127.01,
        }
        tools._project_env_value = lambda *names: "test-key" if "ODSAY_API_KEY" in names else ""

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b'{"result":{"path":[{"info":{"totalTime":18,"totalDistance":4200.5}}]}}'

        with patch("urllib.request.urlopen", return_value=Response()) as urlopen:
            first = tools.execute_directions_lookup({
                "origin_place_id": "a", "destination_place_id": "b", "mode": "transit",
            })
            second = tools.execute_directions_lookup({
                "origin_place_id": "a", "destination_place_id": "b", "mode": "transit",
            })

        self.assertEqual("odsay_transit", first["source"])
        self.assertEqual(4200, first["distance_meters"])
        self.assertEqual(1, first["billing_external_requests"])
        self.assertEqual(0, second["billing_external_requests"])
        self.assertEqual("hit", second["cache"])
        self.assertEqual(1, urlopen.call_count)

    def test_transit_provider_budget_is_isolated_per_itinerary_request(self):
        tools = ModelLoader().model("ai_tools")
        tools._direction_cache = {}
        tools._transit_external_requests_by_scope = {"finished-request": 24}
        tools._get_place = lambda place_id: {
            "latitude": 37.50 if place_id == "a" else 37.51,
            "longitude": 127.00 if place_id == "a" else 127.01,
        }
        tools._project_env_value = lambda *names: "test-key" if "ODSAY_API_KEY" in names else ""

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b'{"result":{"path":[{"info":{"totalTime":11,"totalDistance":2100.0}}]}}'

        with patch("urllib.request.urlopen", return_value=Response()) as urlopen:
            skipped = tools.execute_directions_lookup({
                "origin_place_id": "a", "destination_place_id": "b", "mode": "transit",
                "request_scope": "finished-request",
            })
            fresh = tools.execute_directions_lookup({
                "origin_place_id": "a", "destination_place_id": "b", "mode": "transit",
                "request_scope": "new-request",
            })

        self.assertEqual(0, skipped["billing_external_requests"])
        self.assertEqual("request_budget_exhausted", skipped["external_provider_skip_reason"])
        self.assertEqual(1, fresh["billing_external_requests"])
        self.assertEqual("odsay_transit", fresh["source"])
        self.assertEqual(1, urlopen.call_count)

    def test_cross_day_distance_is_not_counted_as_within_day_detour(self):
        engine = self.Engine(FixtureAiTools())
        days = [
            {
                "day": 1,
                "places": [
                    {"name": "A", "lat": 37.50, "lng": 127.00},
                    {"name": "B", "lat": 37.50, "lng": 127.01,
                     "move_from_previous": {"distance_meters": 900}},
                ],
            },
            {
                "day": 2,
                "previous_day_connection": {
                    "distance_meters": 20000, "duration_minutes": 40,
                },
                "places": [
                    {"name": "C", "lat": 37.60, "lng": 127.10},
                    {"name": "D", "lat": 37.60, "lng": 127.11,
                     "move_from_previous": {"distance_meters": 900}},
                ],
            },
        ]

        diagnostics = engine._route_quality_diagnostics(self.state(), days)

        self.assertLess(diagnostics["detour_ratio"], 2.0)
        self.assertEqual(0, diagnostics["long_day_connection_count"])
        self.assertTrue(diagnostics["simple_route_ok"])

    def test_over_limit_day_connection_is_reported_but_not_used_as_route_failure(self):
        engine = self.Engine(FixtureAiTools())
        days = [
            {
                "day": 1,
                "places": [
                    {"name": "A", "lat": 37.50, "lng": 127.00},
                    {"name": "B", "lat": 37.50, "lng": 127.01},
                ],
            },
            {
                "day": 2,
                "previous_day_connection": {
                    "distance_meters": 20000, "duration_minutes": 70,
                },
                "places": [
                    {"name": "C", "lat": 37.60, "lng": 127.10},
                    {"name": "D", "lat": 37.60, "lng": 127.11},
                ],
            },
        ]

        diagnostics = engine._route_quality_diagnostics(self.state(), days)

        self.assertTrue(diagnostics["simple_route_ok"])
        self.assertEqual(0, diagnostics["long_day_connection_count"])
        self.assertTrue(diagnostics["day_connection_costs"][0]["over_limit"])
        self.assertEqual(
            "overnight_accommodation_unknown",
            diagnostics["day_connection_costs"][0]["constraint_reason"],
        )


if __name__ == "__main__":
    unittest.main()
