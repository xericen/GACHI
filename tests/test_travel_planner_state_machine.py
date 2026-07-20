import json
import unittest

from tests.test_ai_harness import IntegrationModelLoader, SequenceProvider


class TravelPlannerStateMachineTest(unittest.TestCase):
    def setUp(self):
        self.loader = IntegrationModelLoader()
        self.StateMachine = self.loader.model("agents/travel_planner_state")
        self.Engine = self.loader.model("agents/travel_itinerary_engine")
        self.state_machine = self.StateMachine()
        self.tools = self.loader.ai_tools
        self.engine = self.Engine(self.tools)

    def state(self, **changes):
        value = self.state_machine.normalize({
            "region": "부산",
            "days": 2,
            "transport": "대중교통",
            "preferences": ["바다", "맛집", "카페"],
        })
        value.update(changes)
        return self.state_machine.apply_generation_defaults(value)

    def test_all_conditions_in_one_sentence_generate_immediately(self):
        extracted = self.state_machine.extract(
            "부산 1박 2일 친구와 대중교통으로 바다 맛집 카페 코스 만들어줘",
            {},
        )
        state = self.state_machine.merge({}, extracted["changed_slots"])
        result = self.engine.generate(self.state_machine.apply_generation_defaults(state))

        self.assertEqual("generate_course", extracted["user_intent"])
        self.assertEqual([], self.state_machine.missing_slots(state))
        self.assertTrue(result["ok"])
        self.assertEqual(2, len(result["draft"]["days"]))

    def test_conditions_accumulate_across_messages(self):
        state = self.state_machine.normalize({})
        for prompt in ["부산으로 갈게", "2박 3일이야", "대중교통으로 바다와 맛집 위주"]:
            state = self.state_machine.merge(state, self.state_machine.extract(prompt, state)["changed_slots"])

        self.assertEqual("부산", state["region"])
        self.assertEqual(3, state["days"])
        self.assertEqual("대중교통", state["transport"])
        self.assertEqual(["바다", "맛집"], state["preferences"])

    def test_region_change_updates_only_region_and_invalidates_old_draft(self):
        state = self.state(itinerary_draft={"days": [{"places": []}]}, collected_place_ids=["old"])
        changed = self.state_machine.extract("서울 말고 부산으로 바꿔줘", state)["changed_slots"]
        merged = self.state_machine.merge(dict(state, region="서울"), changed)

        self.assertEqual("부산", merged["region"])
        self.assertEqual(2, merged["days"])
        self.assertEqual({}, merged["itinerary_draft"])
        self.assertEqual([], merged["collected_place_ids"])

    def test_days_change_preserves_other_slots(self):
        state = self.state()
        changed = self.state_machine.extract("3일로 바꿔줘", state)["changed_slots"]
        merged = self.state_machine.merge(state, changed)

        self.assertEqual(3, merged["days"])
        self.assertEqual("부산", merged["region"])
        self.assertEqual(["바다", "맛집", "카페"], merged["preferences"])

    def test_remove_place_patches_only_target_day(self):
        generated = self.engine.generate(self.state())
        state = self.state(itinerary_draft=generated["draft"])
        state["collected_place_ids"] = self.place_ids(generated["draft"])
        before_second = self.place_ids({"days": [generated["draft"]["days"][1]]})
        revised = self.engine.revise(state, "첫째 날 카페는 빼줘", "remove_place")

        self.assertTrue(revised["ok"])
        self.assertFalse(any(place["category"] == "카페" for place in revised["draft"]["days"][0]["places"]))
        self.assertEqual(before_second, self.place_ids({"days": [revised["draft"]["days"][1]]}))

    def test_replace_place_excludes_every_existing_place_id(self):
        generated = self.engine.generate(self.state())
        original_ids = self.place_ids(generated["draft"])
        state = self.state(itinerary_draft=generated["draft"], collected_place_ids=original_ids)
        revised = self.engine.revise(state, "첫째 날 카페를 다른 곳으로 바꿔줘", "replace_place")

        self.assertTrue(revised["ok"])
        revised_ids = self.place_ids(revised["draft"])
        self.assertEqual(len(revised_ids), len(set(revised_ids)))
        self.assertTrue(set(revised_ids) - set(original_ids))

    def test_add_named_place_searches_database_and_patches_target_day(self):
        generated = self.engine.generate(self.state())
        original_ids = self.place_ids(generated["draft"])
        state = self.state(itinerary_draft=generated["draft"], collected_place_ids=original_ids)
        before = len(generated["draft"]["days"][1]["places"])
        revised = self.engine.revise(state, "둘째 날 해운대를 넣어줘", "add_place")

        self.assertTrue(revised["ok"])
        self.assertEqual(before + 1, len(revised["draft"]["days"][1]["places"]))
        self.assertEqual("해운대", self.tools.search_calls[-1]["keyword"])

    def test_must_visit_place_is_resolved_through_place_search(self):
        result = self.engine.generate(self.state(must_visit_places=["해운대"]))

        self.assertTrue(result["ok"])
        self.assertEqual("해운대", self.tools.search_calls[0]["keyword"])
        self.assertTrue(result["draft"]["days"][0]["places"][0]["place_id"])

    def test_cafe_exclusion_is_accumulated_and_not_scheduled(self):
        state = self.state()
        changed = self.state_machine.extract("카페는 빼줘", state)
        merged = self.state_machine.merge(state, changed["changed_slots"])
        generated = self.engine.generate(merged)

        self.assertEqual("provide_information", changed["user_intent"])
        self.assertIn("카페", merged["excluded_preferences"])
        self.assertNotIn("카페", merged["preferences"])
        self.assertFalse(any(
            place["category"] == "카페"
            for day in generated["draft"]["days"] for place in day["places"]
        ))

    def test_empty_place_search_returns_specific_failure_stage(self):
        self.tools.fail_search = True
        result = self.engine.generate(self.state())

        self.assertFalse(result["ok"])
        self.assertEqual("place_search", result["failure_stage"])

    def test_malformed_gemini_json_falls_back_to_server_extraction(self):
        types = self.loader.model("ai_harness/types")
        Agent = self.loader.model("agents/travel_planner")
        agent = Agent(self.loader)
        response = types.ModelResponse(text="{잘못된 JSON", tool_calls=[], model="fixture-model")
        agent.harness.config.model_provider = SequenceProvider(types, [response])

        status, payload = agent.send("부산 1일 대중교통 바다 코스 만들어줘")

        self.assertEqual(200, status)
        self.assertEqual("draft_ready", payload["stage"])
        self.assertEqual("json_parse_recovered", payload["_fallback_reason"])

    def test_directions_failure_uses_distance_fallback(self):
        self.tools.fail_directions = True
        result = self.engine.generate(self.state(days=1))

        self.assertTrue(result["ok"])
        self.assertTrue(any("직선거리" in warning for warning in result["warnings"]))
        places = result["draft"]["days"][0]["places"]
        self.assertIsNotNone(places[1]["move_from_previous"]["duration_minutes"])

    def test_duplicate_place_ids_are_never_scheduled(self):
        result = self.engine.generate(self.state(days=3))
        ids = self.place_ids(result["draft"])

        self.assertTrue(result["ok"])
        self.assertEqual(len(ids), len(set(ids)))

    def test_harness_and_legacy_switch_reports_active_executor(self):
        facade = self.loader.model("ai_chat")
        self.assertEqual("harness", facade.admin_settings()["active_executor"])
        facade.switch.set_enabled(False)
        self.assertEqual("legacy", facade.admin_settings()["active_executor"])

    def place_ids(self, draft):
        return [
            place["place_id"]
            for day in draft.get("days", [])
            for place in day.get("places", [])
        ]


if __name__ == "__main__":
    unittest.main()
