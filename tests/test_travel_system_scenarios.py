import datetime
import json
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace

from tests import test_travel_flexible_planning as helpers
from tests.test_ai_harness import IntegrationModelLoader, ModelLoader, SequenceProvider


class SystemPlanningScenarios(unittest.TestCase):
    def setUp(self):
        self.helper = helpers.FlexibleTravelPlanningTest()
        self.helper.setUp()
        self.helper.machine.today_provider = lambda: datetime.date(2026, 10, 28)
        self.engine = self.helper.engine

    def assert_window(self, draft):
        self.assertTrue(draft["days"])
        for day in draft["days"]:
            self.assertTrue(day["places"])
            finish = self.engine._minutes(day["end_time"], 0)
            for row in day["places"]:
                self.assertIsNotNone(self.engine._coord(row))
                self.assertTrue(row["place_id"])
                self.assertLessEqual(self.engine._minutes(row["time"], 0) + row["duration_minutes"], finish)

    def test_A_busan_station_transit_date_followup_and_generation(self):
        agent = self.helper.agent()
        _, first = agent.send("부산역에서 출발해서 대중교통으로 10시부터 18시까지 데이트 코스 만들어줘")
        self.assertEqual("부산역", first["travel_state"]["start_location"])
        self.assertEqual("대중교통", first["travel_state"]["transport"])
        self.assertEqual("10:00", first["travel_state"]["arrival_time"])
        _, ready = agent.send("내일", state_raw=json.dumps(first["travel_state"]))
        self.assertTrue(ready["can_generate"])
        _, result = agent.send("코스 만들어줘", state_raw=json.dumps(ready["travel_state"]))
        self.assertEqual("draft_ready", result["stage"])
        self.assertGreaterEqual(len(result["itinerary_draft"]["days"][0]["places"]), 3)
        self.assertLessEqual(len(result["itinerary_draft"]["days"][0]["places"]), 5)
        self.assert_window(result["itinerary_draft"])

    def test_B_three_hours_collects_real_start_and_infers_end_from_duration(self):
        agent = self.helper.agent()
        state = {}
        for prompt in ["서울에서 3시간 정도 가볍게 데이트하고 싶어", "내일", "서울역", "대중교통", "오전 10시"]:
            _, payload = agent.send(prompt, state_raw=json.dumps(state))
            state = payload["travel_state"]
        self.assertEqual(180, state["available_minutes"])
        self.assertEqual("10:00", state["arrival_time"])
        self.assertEqual("13:00", state["departure_time"])
        self.assertTrue(payload["can_generate"])
        _, result = agent.send("코스 만들어줘", state_raw=json.dumps(state))
        self.assertEqual("draft_ready", result["stage"])
        self.assertLessEqual(len(result["itinerary_draft"]["days"][0]["places"]), 2)
        self.assert_window(result["itinerary_draft"])

    def test_duration_does_not_authorize_hallucinated_clock_times(self):
        agent = self.helper.agent([{
            "changed_slots": {"arrival_time": "10:00", "departure_time": "13:00", "days": 1},
            "user_intent": "provide_information", "assistant_message": "조건을 정리했어요.",
        }])
        _, reply = agent.send("서울에서 3시간 정도 가볍게 데이트하고 싶어")
        self.assertEqual("", reply["travel_state"]["arrival_time"])
        self.assertEqual("", reply["travel_state"]["departure_time"])
        self.assertIn("time_window", reply["missing_slots"])
        self.assertFalse(reply["can_generate"])

    def test_C_two_days_sea_and_food_preserve_preferences(self):
        agent = self.helper.agent()
        _, first = agent.send("부산에서 1박 2일 여행할 건데 바다랑 맛집 위주로 추천해줘")
        state = first["travel_state"]
        self.assertEqual(2, state["days"])
        self.assertIn("바다", state["preferences"])
        self.assertIn("맛집", state["preferences"])
        _, ready = agent.send("내일부터 부산역에서 대중교통으로 출발할게", state_raw=json.dumps(state))
        self.assertEqual("부산역", ready["travel_state"]["start_location"])
        _, result = agent.send("코스 만들어줘", state_raw=json.dumps(ready["travel_state"]))
        self.assertEqual("draft_ready", result["stage"])
        self.assertEqual(2, len(result["itinerary_draft"]["days"]))
        self.assert_window(result["itinerary_draft"])

    def test_day_count_cannot_become_an_invented_duration_or_visit_limit(self):
        agent = self.helper.agent([{
            "changed_slots": {"days": 2, "available_minutes": 288, "max_places": 2},
            "user_intent": "provide_information", "assistant_message": "조건을 정리했어요.",
        }])
        _, reply = agent.send("부산에서 1박 2일 여행할 건데 바다랑 맛집 위주로 추천해줘")
        self.assertIsNone(reply["travel_state"]["available_minutes"])
        self.assertIsNone(reply["travel_state"]["max_places"])
        self.assertEqual(2, reply["travel_state"]["days"])

    def test_D_leave_exactly_two_across_existing_multiday_course_without_new_search(self):
        state = self.helper.state(days=2, end_date="2026-10-30")
        generated = self.engine.generate(state)
        state["itinerary_draft"] = generated["draft"]
        state["conversation_stage"] = "draft_ready"
        agent = self.helper.agent()
        search_count = len(self.helper.loader.ai_tools.search_calls)
        _, reply = agent.send("너무 빡빡하니까 장소 두 개만 남겨줘", state_raw=json.dumps(state))
        self.assertEqual("revise_itinerary", reply["action"])
        self.assertEqual(2, sum(len(day["places"]) for day in reply["itinerary_draft"]["days"]))
        self.assertEqual(search_count, len(self.helper.loader.ai_tools.search_calls))
        self.assert_window(reply["itinerary_draft"])

    def test_E_primary_search_exception_uses_other_provider_without_leaking_secrets(self):
        tools = ModelLoader().model("ai_tools")
        tools._query_places = lambda **kwargs: []
        tools._tour_api_exact_place_search = Mock(side_effect=RuntimeError("secret-key-user-location"))
        tools._naver_exact_place_search = Mock(return_value=[
            {"place_id": "station", "name": "부산역", "lat": 35.115, "lng": 129.041},
            {"place_id": "invalid", "name": "bad", "lat": float("nan"), "lng": 129},
        ])
        result = tools.execute_place_search({"region": "부산", "keyword": "부산역", "category": "", "exact_name": True})
        self.assertEqual("ok", result["status"])
        self.assertEqual(["station"], [row["place_id"] for row in result["results"]])
        self.assertEqual("RuntimeError", result["search_diagnostics"][0]["error_type"])
        self.assertNotIn("secret-key", json.dumps(result))
        tools._naver_exact_place_search.assert_called_once()

    def test_search_budget_does_not_disable_recovery_in_later_independent_requests(self):
        tools = ModelLoader().model("ai_tools")
        tools._query_places = lambda **kwargs: []
        tools._tour_api_exact_place_search = lambda *args, **kwargs: []
        row = {"place_id": "station", "name": "부산역", "lat": 35.115, "lng": 129.041}
        tools._naver_exact_place_search = Mock(side_effect=[[], [], [], [], [], [], [row]])
        for _ in range(6):
            tools.execute_place_search({"region": "부산", "keyword": "부산역", "exact_name": True})
        result = tools.execute_place_search({"region": "부산", "keyword": "부산역", "exact_name": True})
        self.assertEqual("ok", result["status"])

    def test_F_some_routes_fail_but_estimates_are_explicit_and_course_survives(self):
        original = self.helper.loader.ai_tools.execute_directions_lookup
        count = [0]
        def directions(args):
            count[0] += 1
            if count[0] % 3 == 0:
                raise TimeoutError("private-provider-error")
            return original(args)
        with patch.object(self.helper.loader.ai_tools, "execute_directions_lookup", side_effect=directions):
            result = self.engine.generate(self.helper.state())
        self.assertTrue(result["ok"])
        self.assert_window(result["draft"])
        with patch.object(self.helper.loader.ai_tools, "execute_directions_lookup", side_effect=TimeoutError("private-provider-error")):
            fallback = self.engine._route_score_move(
                {"place_id": "new1", "lat": 35.11, "lng": 129.04},
                {"place_id": "new2", "lat": 35.111, "lng": 129.041}, "transit",
            )
        self.assertFalse(fallback["actual"])
        public_move = self.engine._move_payload(fallback, "transit")
        self.assertTrue(public_move["estimated"])
        self.assertIn("예상", public_move["duration_label"])

    def test_ordinal_replace_preserves_other_day_and_other_place_ids(self):
        state = self.helper.state(days=2)
        generated = self.engine.generate(state)
        state["itinerary_draft"] = generated["draft"]
        before = json.loads(json.dumps(generated["draft"]["days"]))
        result = self.engine.revise(state, "첫날 두 번째 장소만 다른 곳으로 바꿔줘", "replace_place")
        self.assertTrue(result["ok"])
        after = result["draft"]["days"]
        self.assertEqual(before[1], after[1])
        self.assertNotEqual(before[0]["places"][1]["place_id"], after[0]["places"][1]["place_id"])
        self.assertEqual(before[0]["places"][0]["place_id"], after[0]["places"][0]["place_id"])

    def test_cafe_add_start_change_walk_and_sea_final(self):
        state = self.helper.state(arrival_time="10:00", departure_time="21:30")
        generated = self.engine.generate(state)
        state["itinerary_draft"] = generated["draft"]
        added = self.engine.revise(state, "카페 하나 더 추가해줘", "add_place")
        self.assertTrue(added["ok"])
        old_ids = {p["place_id"] for p in generated["draft"]["days"][0]["places"]}
        new = [p for p in added["draft"]["days"][0]["places"] if p["place_id"] not in old_ids]
        self.assertTrue(new)
        state["start_location"] = "김해공항"
        changed = self.engine.revise(state, "김해공항에서 출발하는 걸로 변경해줘", "revise_course")
        self.assertTrue(changed["ok"])
        self.assertEqual("김해공항", changed["draft"]["start_location"]["name"])
        agent = self.helper.agent()
        state["conversation_stage"] = "draft_ready"
        _, low = agent.send("걷는 시간이 너무 길어", state_raw=json.dumps(state))
        self.assertEqual("revise_itinerary", low["action"])
        sea = self.engine.revise(state, "마지막은 바다 보면서 끝내고 싶어", "revise_course")
        self.assertTrue(sea["ok"])
        self.assertEqual("자연", sea["draft"]["days"][0]["places"][-1]["category"])

    def test_sea_ending_edit_does_not_rebuild_the_other_day(self):
        state = self.helper.state(days=2, preferences=["바다", "맛집", "카페"])
        original = self.engine.generate(state)["draft"]
        state["itinerary_draft"] = original
        state["preferences"] = ["바다", "맛집"]
        result = self.engine.revise(state, "마지막은 바다 보면서 끝내고 싶어", "revise_course")
        self.assertTrue(result["ok"])
        self.assertEqual(original["days"][0], result["draft"]["days"][0])

    def test_known_stations_and_ambiguous_duplicate_names(self):
        for name in ["부산역", "서울역", "강남역"]:
            suffix = " (2호선)" if name == "강남역" else " (경의중앙선)" if name == "서울역" else " (고속철도)"
            row = {"place_id": name, "name": name + suffix, "lat": 37.5, "lng": 127.0}
            self.assertEqual(row, self.engine._exact_named_candidate(name, [row]))
        self.assertIsNone(self.engine._coord({"lat": float("nan"), "lng": 127.0}))

    def test_ambiguous_anchor_requires_choice_then_uses_verified_selected_id(self):
        rows = [
            {"place_id": "first", "name": "서울역", "lat": 37.55, "lng": 126.97, "address": "서울 중구"},
            {"place_id": "second", "name": "서울역", "lat": 37.60, "lng": 127.0, "address": "서울 다른 구"},
        ]
        self.engine._search = lambda *args, **kwargs: (rows, [], [])
        state = self.helper.state(region="서울", start_location="서울역")
        anchor, _, _ = self.engine._resolve_start_anchor(state, set())
        self.assertIsNone(anchor)
        self.assertEqual(2, len(self.engine._start_candidates))
        state["start_location_id"] = "second"
        anchor, _, _ = self.engine._resolve_start_anchor(state, set())
        self.assertEqual("second", anchor["place_id"])
        self.assertEqual(37.60, anchor["lat"])

    def test_explicit_count_conflict_keeps_mandatory_places_and_returns_choice(self):
        places = [
            {"place_id": str(i), "name": str(i), "route_locked_reason": "must_visit"}
            for i in range(3)
        ]
        result = self.engine._enhanced_revision(
            {"max_places": 2}, [{"places": places}], [0], "장소 두 개만 남겨줘", "",
        )
        self.assertTrue(result.get("conflict"))

    def test_ai_proposal_rejects_unknown_ids_coordinates_and_preserves_provider_facts(self):
        loader = IntegrationModelLoader()
        Advisor = ModelLoader().model("agents/travel_plan_advisor")
        types = loader.model("ai_harness/types")
        candidates = [{"place_id": "one", "name": "박물관", "lat": 35.1, "lng": 129.0}]
        context = {"selected_ids": ["one"]}
        for changes, valid in [
            ({"visit_ids": ["one"]}, True),
            ({"visit_ids": ["invented"]}, False),
            ({"visit_ids": ["one", "one"]}, False),
            ({"visit_ids": ["one"], "coordinates": [0, 0]}, False),
        ]:
            payload = {"visit_ids": ["one"], "alternative_ids": [], "pace": "보통", "recovery_action": "keep"}
            payload.update(changes)
            provider = SequenceProvider(types, [types.ModelResponse(text=json.dumps(payload), tool_calls=[], model="fixture")])
            advisor = Advisor(loader, provider=provider)
            result = advisor.propose({}, candidates, context)
            self.assertEqual(valid, result is not None)
        provider = Mock()
        provider.generate.side_effect = TimeoutError()
        self.assertIsNone(Advisor(loader, provider=provider).propose({}, candidates, context))

    def test_ai_recovery_uses_only_verified_alternative_rows(self):
        self.engine.plan_advisor = SimpleNamespace(last_status="validated", propose=lambda *args: {
            "visit_ids": ["a"], "alternative_ids": ["b"], "pace": "보통", "recovery_action": "replace",
        })
        a = {"place_id": "a", "name": "A", "category": "문화시설", "lat": 35.1, "lng": 129.0, "planned_duration_minutes": 60}
        b = {"place_id": "b", "name": "B", "category": "문화시설", "lat": 35.11, "lng": 129.01}
        proposed = self.engine._candidate_plan({}, {"categories": ["문화시설"], "day_window": {"start": "10:00"}}, [a], {"문화시설": [b]}, 0, "recovery", {"places": []})
        self.assertEqual("b", proposed[0]["place_id"])
        self.assertEqual(35.11, proposed[0]["lat"])

    def test_alternate_route_response_parsers_validate_provider_time_units(self):
        tools = ModelLoader().model("ai_tools")
        tools._project_env_value = lambda *keys: "fixture-key"
        origin = {"latitude": 35.1, "longitude": 129.0}
        destination = {"latitude": 35.11, "longitude": 129.01}
        for mode, payload in [
            ("driving", {"routes": [{"result_code": 0, "summary": {"duration": 240, "distance": 1200}}]}),
            ("walking", {"features": [{"properties": {"summary": {"duration": 240, "distance": 400}}}]}),
        ]:
            response = Mock()
            response.__enter__ = Mock(return_value=response)
            response.__exit__ = Mock(return_value=False)
            response.read.return_value = json.dumps(payload).encode()
            with patch("urllib.request.urlopen", return_value=response):
                result = tools._alternate_directions(origin, destination, mode)
            self.assertEqual("ok", result["status"])
            self.assertEqual(4, result["duration_minutes"])
            self.assertEqual(mode, result["mode"])

    def test_alternate_driving_provider_is_used_before_estimate(self):
        tools = ModelLoader().model("ai_tools")
        tools._get_place = lambda key: {"id": key, "latitude": 35.1, "longitude": 129.0}
        tools._naver_directions = lambda *args: None
        tools._alternate_directions = Mock(return_value={"status": "ok", "source": "verified_alternative", "duration_minutes": 7, "distance_meters": 1000})
        result = tools.execute_directions_lookup({"origin_place_id": "one", "destination_place_id": "two", "mode": "driving"})
        self.assertEqual("verified_alternative", result["source"])
        self.assertEqual(7, result["duration_minutes"])
        tools._alternate_directions.assert_called_once()


if __name__ == "__main__":
    unittest.main()
