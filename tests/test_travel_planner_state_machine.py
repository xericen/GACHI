import json
import datetime
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

    def test_relative_dates_are_resolved_before_model_call(self):
        machine = self.StateMachine(today_provider=lambda: datetime.date(2026, 7, 21))
        cases = [
            ("오늘만 다녀올래", "2026-07-21", "2026-07-21", 1),
            ("내일부터 갈래", "2026-07-22", "2026-07-22", 1),
            ("이번 주말에 갈래", "2026-07-25", "2026-07-26", 2),
            ("모레 출발", "2026-07-23", "2026-07-23", 1),
            ("다음 주에 갈래", "2026-07-27", "2026-08-02", 7),
            ("금요일에 갈래", "2026-07-24", "2026-07-24", 1),
            ("토요일에 갈래", "2026-07-25", "2026-07-25", 1),
            ("다음 달에 갈래", "2026-08-01", "2026-08-01", 1),
            ("이번 휴가에 갈래", "2026-07-21", "2026-07-21", 1),
        ]
        for prompt, start, end, days in cases:
            changed = machine.extract(prompt, {})["changed_slots"]
            self.assertEqual((start, end, days), (changed["start_date"], changed["end_date"], changed["days"]), prompt)

    def test_stay_expressions_normalize_days_and_end_date(self):
        machine = self.StateMachine(today_provider=lambda: datetime.date(2026, 7, 21))
        cases = [("1박2일", 2), ("2박 3일", 3), ("3박4일", 4)]
        for phrase, days in cases:
            changed = machine.extract(f"내일부터 {phrase} 갈래", {})["changed_slots"]
            self.assertEqual(days, changed["days"])
            self.assertEqual((datetime.date(2026, 7, 22) + datetime.timedelta(days=days - 1)).isoformat(), changed["end_date"])

    def test_companion_transport_and_mood_aliases_are_normalized(self):
        companion_cases = {
            "강릉 데이트": "연인", "애인이랑": "연인", "남친이랑": "연인",
            "여친과": "연인", "남자친구와": "연인", "여자친구와": "연인",
            "친구들이랑": "친구", "가족끼리": "가족",
        }
        for prompt, expected in companion_cases.items():
            self.assertEqual([expected], self.state_machine.extract(prompt, {})["changed_slots"]["companions"])

        self.assertEqual("대중교통", self.state_machine.extract("차 없이 걸어다닐래", {})["changed_slots"]["transport"])
        self.assertEqual("자동차", self.state_machine.extract("렌트할 거야", {})["changed_slots"]["transport"])
        moods = self.state_machine.extract("바다에서 감성 있게 힐링하고 사진 많이 찍으며 먹방도 할래", {})["changed_slots"]["preferences"]
        self.assertEqual(["바다", "감성카페", "자연", "사진 명소", "맛집"], moods)

    def test_pending_generation_continues_after_meaningful_day_answer(self):
        types = self.loader.model("ai_harness/types")
        Agent = self.loader.model("agents/travel_planner")
        agent = Agent(self.loader)
        responses = [
            types.ModelResponse(text='{"user_intent":"provide_information"}', tool_calls=[], model="fixture-model"),
            types.ModelResponse(text='{"user_intent":"provide_information"}', tool_calls=[], model="fixture-model"),
        ]
        agent.harness.config.model_provider = SequenceProvider(types, responses)
        first_prompt = "강릉 데이트 코스 만들어줘"
        status, first = agent.send(first_prompt, "[]")
        history = json.dumps([
            {"role": "user", "text": first_prompt},
            {"role": "assistant", "text": first["message"]},
        ], ensure_ascii=False)
        next_status, second = agent.send("오늘", history)

        self.assertEqual(200, status)
        self.assertEqual(["days"], first["missing_slots"])
        self.assertIn("며칠", first["message"])
        self.assertEqual(200, next_status)
        self.assertEqual("draft_ready", second["stage"])
        self.assertEqual("generate_itinerary", second["action"])
        self.assertEqual(1, second["travel_state"]["days"])
        self.assertEqual("연인", second["travel_state"]["companions"][0])

    def test_complete_colloquial_request_generates_without_question(self):
        extracted = self.state_machine.extract(
            "오늘 강릉 데이트 코스 만들어줘. 차 없이 사진 많이 찍고 감성 있게 다닐래",
            {},
        )
        state = self.state_machine.apply_generation_defaults(
            self.state_machine.merge({}, extracted["changed_slots"])
        )

        self.assertEqual("generate_course", extracted["user_intent"])
        self.assertEqual([], self.state_machine.missing_slots(state))
        self.assertEqual(1, state["days"])
        self.assertEqual(["연인"], state["companions"])
        self.assertEqual("대중교통", state["transport"])
        self.assertIn("감성카페", state["preferences"])
        self.assertIn("사진 명소", state["preferences"])

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

    def test_each_day_has_theme_explanation_and_quality_summary(self):
        result = self.engine.generate(self.state(region="강릉", days=3, companions=["연인"], preferences=["바다", "맛집", "카페", "야경"]))

        self.assertTrue(result["ok"])
        self.assertEqual("연인", result["draft"]["traveler_style"])
        self.assertEqual(3, len(result["draft"]["days"]))
        self.assertGreaterEqual(result["draft"]["quality"]["score"], 80)
        for day in result["draft"]["days"]:
            self.assertTrue(day["theme"])
            self.assertGreaterEqual(len(day["description"]), 3)
            self.assertIn("expected_cost_label", day)
            self.assertIn("condition_fulfillment_rate", result["draft"]["quality"])

    def test_rich_place_metadata_and_time_periods_are_included(self):
        result = self.engine.generate(self.state(days=1, companions=["가족"]))
        place = result["draft"]["days"][0]["places"][0]

        for key in ["time_period", "time_period_icon", "rating", "review_count", "opening_status", "tags", "duration_label", "estimated_cost"]:
            self.assertIn(key, place)
        self.assertTrue(place["time_period"])

    def test_excessive_direction_leg_is_replaced_or_removed(self):
        self.tools.direction_sequence = [90, 10, 10, 10, 10]
        result = self.engine.generate(self.state(days=1))

        self.assertTrue(result["ok"])
        day = result["draft"]["days"][0]
        self.assertLessEqual(day["total_move_minutes"], self.engine.MAX_DAY_MOVE_MINUTES["transit"])
        self.assertTrue(all(
            int(place.get("move_from_previous", {}).get("duration_minutes") or 0) <= self.engine.MAX_LEG_MINUTES["transit"]
            for place in day["places"]
        ))

    def test_categories_do_not_repeat_consecutively(self):
        result = self.engine.generate(self.state(days=3))

        for day in result["draft"]["days"]:
            groups = [self.engine._category_group(place["category"]) for place in day["places"]]
            self.assertTrue(all(one != two for one, two in zip(groups, groups[1:])))

    def test_enhanced_revision_prompts_patch_existing_draft(self):
        prompts = [
            ("점심을 한식 말고 양식으로", "meal_cuisine"),
            ("사진 찍기 좋은 곳 추가", "add_photo_spot"),
            ("야경을 꼭 넣어줘", "add_night"),
            ("비 오는 날 코스로 바꿔줘", "rainy_indoor"),
            ("걷는 거 적게 바꿔줘", "low_walking"),
        ]
        for prompt, patch_type in prompts:
            generated = self.engine.generate(self.state(days=2))
            state = self.state(days=2, itinerary_draft=generated["draft"], collected_place_ids=self.place_ids(generated["draft"]))
            revised = self.engine.revise(state, prompt, "revise_course")
            self.assertTrue(revised["ok"], prompt)
            self.assertEqual(patch_type, revised["draft"]["metadata"]["revision"])

    def test_budget_patch_recalculates_quality_cost(self):
        generated = self.engine.generate(self.state(days=2))
        state = self.state(
            days=2,
            budget="10만원",
            itinerary_draft=generated["draft"],
            collected_place_ids=self.place_ids(generated["draft"]),
        )
        revised = self.engine.revise(state, "예산 10만원 이하로 바꿔줘", "revise_course")

        self.assertTrue(revised["ok"])
        self.assertEqual("budget_limit", revised["draft"]["metadata"]["revision"])
        self.assertIn("budget_ok", revised["draft"]["quality"]["checks"])

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
