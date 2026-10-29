import json
import unittest
from unittest.mock import patch

from tests.test_ai_harness import IntegrationModelLoader, ModelLoader, SequenceProvider


class FlexibleTravelPlanningTest(unittest.TestCase):
    def setUp(self):
        self.loader = IntegrationModelLoader()
        self.machine = self.loader.model("agents/travel_planner_state")()
        self.engine = self.loader.model("agents/travel_itinerary_engine")(self.loader.ai_tools)

    def state(self, **changes):
        state = {
            "region": "부산", "start_location": "부산역", "days": 1,
            "start_date": "2026-10-29", "end_date": "2026-10-29",
            "transport": "대중교통", "arrival_time": "10:00", "departure_time": "18:00",
            "conversation_stage": "ready_to_generate",
        }
        state.update(changes)
        return self.machine.apply_generation_defaults(state)

    def agent(self, replies=None):
        agent = self.loader.model("agents/travel_planner")(self.loader)
        types = self.loader.model("ai_harness/types")
        agent.harness.config.model_provider = SequenceProvider(types, [
            types.ModelResponse(text=json.dumps(reply), tool_calls=[], model="fixture")
            for reply in (replies or [{}] * 4)
        ])
        agent.route_observability.record = lambda *args, **kwargs: {}
        return agent

    def test_natural_sentence_does_not_mix_region_and_date_into_departure_station(self):
        extracted = self.machine.extract("부산에서 내일 부산역에서 시작해서 대중교통으로 오후 2시부터 6시까지, 카페보다는 전시를 보고 조용히 쉬고 싶어")
        changed = extracted["changed_slots"]
        self.assertEqual("부산역", changed["start_location"])
        self.assertIn("조용한 분위기", changed["preferences"])
        self.assertIn("문화", changed["preferences"])

    def test_short_window_changes_density_and_evening_is_not_empty(self):
        short = self.engine._day_plan(self.state(arrival_time="14:00", departure_time="16:00"), 0, 1)
        long = self.engine._day_plan(self.state(arrival_time="09:00", departure_time="21:30"), 0, 1)
        late = self.engine._day_plan(self.state(arrival_time="20:30", departure_time="22:00"), 0, 1)
        self.assertGreater(len(long["slots"]), len(short["slots"]))
        self.assertTrue(late["slots"])
        for plan in [short, late]:
            for slot in plan["slots"]:
                self.assertGreaterEqual(slot["target_time"], plan["day_window"]["start"])
                self.assertLessEqual(
                    self.engine._minutes(slot["target_time"], 0) + slot["duration_minutes"],
                    self.engine._minutes(plan["day_window"]["end"], 0),
                )

    def test_optional_category_shortage_returns_real_partial_day(self):
        original = self.loader.ai_tools.execute_place_search
        def search(args):
            if args.get("category") in {"맛집", "음식점", "시장", "카페", "디저트"}:
                return {"status": "not_found", "results": []}
            return original(args)
        with patch.object(self.loader.ai_tools, "execute_place_search", side_effect=search):
            result = self.engine.generate(self.state())
        self.assertTrue(result["ok"])
        self.assertTrue(result["partial"])
        self.assertEqual("partial", result["draft"]["completion_status"])
        self.assertTrue(result["draft"]["days"][0]["places"])
        self.assertTrue(result["draft"]["days"][0]["unfilled_schedule_slots"])

    def test_unresolved_must_visit_is_explicit_on_partial_draft(self):
        result = self.engine.generate(self.state(must_visit_places=["없는필수박물관"]))
        self.assertTrue(result["ok"])
        self.assertTrue(result["partial"])
        self.assertIn("없는필수박물관", result["draft"]["unresolved_requirements"])
        self.assertTrue(result["draft"]["days"][0]["places"])

    def test_empty_arrival_day_keeps_the_next_day_and_original_date_on_revision(self):
        state = self.state(days=2, arrival_time="23:30", departure_time="18:00", end_date="2026-10-30")
        result = self.engine.generate(state)
        self.assertTrue(result["ok"])
        self.assertTrue(result["partial"])
        self.assertEqual([1], result["draft"]["unscheduled_days"])
        self.assertEqual(2, result["draft"]["days"][0]["day"])
        self.assertEqual("2026-10-30", result["draft"]["days"][0]["date"])
        state["itinerary_draft"] = result["draft"]
        state["schedule_pace"] = "여유롭게"
        revised = self.engine.revise(state, "여유롭게 조정해줘", "revise_course")
        self.assertTrue(revised["ok"])
        self.assertEqual(2, revised["draft"]["days"][0]["day"])
        self.assertEqual("2026-10-30", revised["draft"]["days"][0]["date"])

    def test_unreachable_event_is_pending_without_hiding_available_visits(self):
        result = self.engine.generate(self.state(
            must_visit_places=["없는공연장"],
            event_selection={"name": "공연", "venue": "없는공연장", "date": "2026-10-29",
                             "time": "17:00", "duration_minutes": 180},
        ))
        self.assertTrue(result["ok"])
        self.assertTrue(result["partial"])
        self.assertIn("공연", result["draft"]["unresolved_requirements"])
        self.assertTrue(result["draft"]["days"][0]["places"])
        self.assertFalse(any(p.get("route_locked_reason") == "event" for p in result["draft"]["days"][0]["places"]))

    def test_whole_search_failure_never_returns_empty_success(self):
        self.loader.ai_tools.fail_search = True
        result = self.engine.generate(self.state())
        self.assertFalse(result["ok"])
        self.assertFalse(result.get("draft", {}).get("days"))

    def test_station_suffix_is_accepted_but_station_shop_is_not(self):
        row = {"place_id": "station", "name": "부산역 경부선 KTX", "lat": 35.11, "lng": 129.04}
        self.assertEqual(row, self.engine._exact_named_candidate("부산역", [row]))
        self.assertIsNone(self.engine._exact_named_candidate("부산역", [dict(row, name="부산역 카페")]))
        tools = ModelLoader().model("ai_tools")
        self.assertTrue(tools._strong_name_match("부산역", "부산역 경부선 KTX"))
        self.assertFalse(tools._strong_name_match("부산역", "부산역 카페"))

    def test_anchor_search_retries_name_without_personal_mood(self):
        queries = []
        def search(args):
            queries.append(args)
            if args["keyword"] == "부산역 KTX":
                return {"status": "ok", "results": [{
                    "place_id": "busan-station", "name": "부산역 경부선",
                    "lat": 35.11, "lng": 129.04, "address": "부산 동구",
                }]}
            return {"status": "not_found", "results": []}
        with patch.object(self.loader.ai_tools, "execute_place_search", side_effect=search):
            row, _, _ = self.engine._resolve_start_anchor(
                self.state(preferences=["조용한 분위기", "카페"]), set(),
            )
        self.assertEqual("busan-station", row["place_id"])
        self.assertGreater(len(queries), 1)
        self.assertTrue(all(not args["mood_tags"] for args in queries))

    def test_multilingual_provider_title_is_the_same_named_anchor(self):
        title = "수원 맛집 매산약방 | Korean Restaurant Maesan Yakbang | 韓國料理 メサンヤクバン"
        tools = ModelLoader().model("ai_tools")
        self.assertTrue(tools._strong_name_match("수원 맛집 매산약방", title))
        row = {"place_id": "maesan", "name": title, "lat": 37.2, "lng": 127.0}
        self.assertEqual(
            "maesan",
            self.engine._exact_named_candidate("수원 맛집 매산약방", [row])["place_id"],
        )

    def test_candidate_choice_collects_only_start_without_resetting_other_conditions(self):
        agent = self.agent()
        with patch.object(agent.itinerary_engine, "generate", return_value={
            "ok": False, "failure_stage": "travel_conditions",
            "missing_slots": ["start_location"],
            "failure_reason": {"code": "start_location_unresolved"},
            "start_candidates": [{"name": "부산역 경부선", "address": "부산 동구"}],
            "message": "출발 장소를 선택해주세요.",
        }):
            _, first = agent.send("코스 만들어줘", state_raw=json.dumps(self.state()))
        self.assertEqual("collecting", first["stage"])
        self.assertIn("부산역 경부선", first["suggested_replies"][0]["label"])
        _, selected = agent.send("1번", state_raw=json.dumps(first["travel_state"]))
        self.assertEqual("부산역 경부선", selected["travel_state"]["start_location"])
        self.assertEqual("대중교통", selected["travel_state"]["transport"])
        self.assertEqual("10:00", selected["travel_state"]["arrival_time"])
        self.assertTrue(selected["can_generate"])
        self.assertEqual([], selected["travel_state"]["start_location_candidates"])

    def test_partial_message_does_not_pretend_requirements_are_complete(self):
        agent = self.agent()
        with patch.object(agent.itinerary_engine, "generate", return_value={
            "ok": True, "draft": {
                "completion_status": "partial", "unresolved_requirements": ["필수 전시관"],
                "unscheduled_days": [2], "days": [{"day": 1, "places": [{"place_id": "one", "name": "공원"}]}],
            },
        }):
            _, payload = agent.send("코스 만들어줘", state_raw=json.dumps(self.state()))
        self.assertEqual("draft_ready", payload["stage"])
        self.assertIn("방문 가능한 장소부터", payload["message"])
        self.assertIn("필수 전시관", payload["message"])
        self.assertIn("2일차", payload["message"])

    def test_first_visit_cannot_overrun_time_or_closing_hours(self):
        for usage in ["09:00~12:00", "09:00~22:00"]:
            selected = [self.engine._decorate_slot(
                {"place_id": "museum", "name": "전시관", "category": "문화시설", "usage_time": usage,
                 "lat": 35.1, "lng": 129.0},
                self.engine._slot("activity", "전시", "문화시설", "15:30", 75), "문화시설",
            )]
            day, _, _ = self.engine._assemble_day(
                self.state(arrival_time="15:00", departure_time="16:00"), 0, 1, selected,
                plan={"slots": [], "theme": "전시"},
            )
            self.assertEqual([], day["places"])

    def test_pace_change_in_natural_chat_updates_existing_draft(self):
        generated = self.engine.generate(self.state())
        self.assertTrue(generated["ok"])
        agent = self.agent([{
            "changed_slots": {"schedule_pace": "여유롭게"},
            "user_intent": "provide_information", "assistant_message": "여유롭게 조정할게요.",
        }])
        old = generated["draft"]
        state = self.state(itinerary_draft=old, conversation_stage="draft_ready")
        _, reply = agent.send("조금 더 여유롭게 둘러보고 싶어", state_raw=json.dumps(state))
        self.assertEqual("revise_itinerary", reply["action"])
        self.assertEqual("draft_ready", reply["stage"])
        self.assertEqual("여유롭게", reply["itinerary_draft"]["schedule_pace"])
        self.assertLessEqual(len(reply["itinerary_draft"]["days"][0]["places"]), len(old["days"][0]["places"]))
        self.assertEqual([], reply["missing_slots"])


if __name__ == "__main__":
    unittest.main()
