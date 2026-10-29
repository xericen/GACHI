import contextlib
import datetime
import io
import json
import unittest
from unittest.mock import Mock

from tests.test_ai_harness import IntegrationModelLoader, SequenceProvider


class TravelGenerationReadinessTest(unittest.TestCase):
    def setUp(self):
        self.loader = IntegrationModelLoader()
        self.machine = self.loader.model("agents/travel_planner_state")(
            today_provider=lambda: datetime.date(2026, 10, 27),
        )

    def agent(self, replies=None):
        types = self.loader.model("ai_harness/types")
        agent = self.loader.model("agents/travel_planner")(self.loader)
        agent.state_machine = self.machine
        agent.route_observability.record = lambda *args, **kwargs: {}
        agent.harness.config.model_provider = SequenceProvider(types, [
            types.ModelResponse(text=json.dumps(reply, ensure_ascii=False), tool_calls=[], model="fixture")
            for reply in (replies or [{}] * 10)
        ])
        agent.itinerary_engine.generate = Mock(wraps=agent.itinerary_engine.generate)
        return agent

    def test_today_is_only_a_date_and_never_starts_search(self):
        agent = self.agent()
        _, payload = agent.send("오늘")
        self.assertEqual("2026-10-27", payload["travel_state"]["start_date"])
        self.assertEqual("", payload["travel_state"]["region"])
        self.assertEqual("", payload["travel_state"]["transport"])
        self.assertEqual("region", payload["travel_state"]["pending_slot"])
        self.assertEqual("collecting", payload["stage"])
        self.assertNotIn("방문 구간", payload["message"])
        self.assertNotIn("휴식", payload["message"])
        agent.itinerary_engine.generate.assert_not_called()
        self.assertEqual([], self.loader.ai_tools.search_calls)

    def test_model_and_restored_date_regions_cannot_pass_readiness(self):
        agent = self.agent([{
            "changed_slots": {"region": "2026-10-27", "destination": "2026-10-27",
                              "start_location": "2026-10-27", "transport": "미정"},
            "user_intent": "generate_course", "assistant_message": "코스를 만들게요.",
        }])
        _, payload = agent.send("오늘 코스 만들어 줘", state_raw=json.dumps({
            "region": "2026-10-27", "destination": "2026-10-27",
            "start_location": "2026-10-27", "transport": "미정",
            "conversation_stage": "ready_to_generate",
        }))
        self.assertEqual("region", payload["travel_state"]["pending_slot"])
        self.assertEqual("", payload["travel_state"]["region"])
        self.assertEqual("collecting", payload["stage"])
        agent.itinerary_engine.generate.assert_not_called()

    def test_today_answer_does_not_overwrite_known_region(self):
        agent = self.agent([{"changed_slots": {"region": "2026-10-27", "destination": "2026-10-27"}}])
        _, payload = agent.send("오늘", state_raw=json.dumps({"region": "서울", "destination": "서울"}))
        self.assertEqual("서울", payload["travel_state"]["region"])

    def test_collects_only_route_essentials_and_then_generates(self):
        agent = self.agent()
        state = {}
        expected = ["region", "start_location", "transport", "time_window", ""]
        for text, pending in zip(
            ["오늘 코스 만들어줘", "부산", "부산역", "대중교통", "오전 10시부터 오후 9시 30분까지"], expected,
        ):
            _, payload = agent.send(text, state_raw=json.dumps(state))
            state = payload["travel_state"]
            self.assertEqual(pending, state["pending_slot"], text)
            agent.itinerary_engine.generate.assert_not_called()
            self.assertNotIn("walking_tolerance", payload["missing_slots"])
            self.assertNotIn("rest_preference", payload["missing_slots"])
        self.assertEqual("ready_to_generate", payload["stage"])
        self.assertEqual("10:00", state["arrival_time"])
        self.assertEqual("21:30", state["departure_time"])
        _, generated = agent.send("코스 만들어 줘", state_raw=json.dumps(state))
        agent.itinerary_engine.generate.assert_called_once()
        self.assertEqual("draft_ready", generated["stage"])
        self.assertTrue(generated["itinerary_draft"]["days"][0]["places"])

    def test_unknown_transport_and_copied_region_anchor_remain_missing(self):
        state = self.machine.apply_generation_defaults({
            "region": "서울", "start_location": "서울", "days": 1, "transport": "미정",
        })
        self.assertEqual("", state["start_location"])
        self.assertEqual("미정", state["transport"])
        self.assertEqual(["start_location", "transport", "time_window"], self.machine.missing_slots(state))

    def test_dates_and_clock_times_never_become_locations(self):
        for value in ["오늘", "오늘만", "2026-10-27", "2026년 10월 27일", "14:00", "1일", "미정"]:
            self.assertFalse(self.machine.valid_location(value), value)
        for value in ["송파구", "서울역", "롯데월드", "오늘카페", "서울숲"]:
            self.assertTrue(self.machine.valid_location(value), value)

    def test_reversed_or_invalid_time_window_cannot_generate(self):
        for start, end in [("18:00", "14:00"), ("25:00", "26:00"), ("14:00", "14:00")]:
            agent = self.agent()
            _, payload = agent.send("이 조건으로 코스 만들어줘", state_raw=json.dumps({
                "region": "부산", "start_location": "부산역", "days": 1, "transport": "대중교통",
                "arrival_time": start, "departure_time": end, "conversation_stage": "ready_to_generate",
            }))
            self.assertIn("time_window", payload["missing_slots"])
            agent.itinerary_engine.generate.assert_not_called()

    def test_window_parse_does_not_confuse_dates_with_clock_times(self):
        state = {"pending_slot": "time_window"}
        changed = self.machine.extract("오후 2시부터 6시까지", state)["changed_slots"]
        self.assertEqual("14:00", changed["arrival_time"])
        self.assertEqual("18:00", changed["departure_time"])
        changed = self.machine.extract("10월 27일", state)["changed_slots"]
        self.assertNotIn("arrival_time", changed)

    def test_engine_itself_rejects_incomplete_state_without_queries(self):
        engine = self.loader.model("agents/travel_itinerary_engine")(self.loader.ai_tools)
        result = engine.generate({"region": "2026-10-27", "days": 1, "transport": "미정"})
        self.assertFalse(result["ok"])
        self.assertEqual("travel_conditions", result["failure_stage"])
        self.assertEqual([], self.loader.ai_tools.search_calls)
        self.assertNotIn("7개", result["message"])

    def test_date_only_message_cannot_invent_a_city(self):
        agent = self.agent([{
            "changed_slots": {"region": "서울", "start_location": "서울역"},
            "user_intent": "generate_course",
        }])
        _, payload = agent.send("오늘 코스 만들어 줘")
        self.assertEqual("", payload["travel_state"]["region"])
        agent.itinerary_engine.generate.assert_not_called()

    def test_unresolved_start_requires_a_real_location(self):
        agent = self.agent()
        _, payload = agent.send("이 조건으로 코스 만들어줘", state_raw=json.dumps({
            "region": "부산", "days": 1, "transport": "대중교통",
            "start_location": "없는 출발지", "arrival_time": "10:00", "departure_time": "18:00",
        }))
        self.assertEqual("collecting", payload["stage"])
        self.assertEqual("start_location", payload["travel_state"]["pending_slot"])
        self.assertEqual("start_location_unresolved", payload["failure_reason"]["code"])
        self.assertFalse(payload["itinerary_draft"])

    def test_tiny_time_window_does_not_return_an_empty_success(self):
        agent = self.agent()
        _, payload = agent.send("이 조건으로 코스 만들어줘", state_raw=json.dumps({
            "region": "부산", "days": 1, "transport": "대중교통", "start_location": "부산역",
            "arrival_time": "14:00", "departure_time": "14:01",
        }))
        self.assertEqual("collecting", payload["stage"])
        self.assertEqual("time_window", payload["travel_state"]["pending_slot"])
        self.assertFalse(payload["itinerary_draft"])
        self.assertEqual([], self.loader.ai_tools.search_calls)

    def test_tomorrow_only_does_not_offer_generation_even_with_model_ready_text(self):
        for prompt in ["내일", "내일이요"]:
            agent = self.agent([{
                "changed_slots": {"region": "2026-10-28", "start_location": "2026-10-28"},
                "user_intent": "generate_course",
                "assistant_message": "입력 조건을 정리했어요. 코스 만들기를 눌러주세요.",
            }])
            _, payload = agent.send(prompt)
            self.assertEqual("2026-10-28", payload["travel_state"]["start_date"])
            self.assertEqual("", payload["travel_state"]["region"])
            self.assertEqual("collecting", payload["stage"])
            self.assertFalse(payload["can_generate"])
            self.assertEqual("region", payload["travel_state"]["pending_slot"])
            self.assertNotIn("코스 만들기", payload["message"])
            self.assertNotIn("코스 만들기", [row["label"] for row in payload["suggested_replies"]])
            agent.itinerary_engine.generate.assert_not_called()

    def test_model_guesses_cannot_replace_unanswered_core_questions(self):
        invented = {
            "changed_slots": {"region": "부산", "destination": "부산", "start_location": "부산역",
                              "transport": "대중교통", "arrival_time": "10:00", "departure_time": "18:00"},
            "user_intent": "generate_course",
        }
        agent = self.agent([invented, invented])
        _, date_reply = agent.send("내일")
        self.assertFalse(date_reply["can_generate"])
        self.assertEqual("", date_reply["travel_state"]["region"])
        self.assertEqual("", date_reply["travel_state"]["transport"])
        self.assertEqual("", date_reply["travel_state"]["arrival_time"])
        _, region_reply = agent.send("부산", state_raw=json.dumps(date_reply["travel_state"]))
        self.assertEqual("부산", region_reply["travel_state"]["region"])
        self.assertEqual("", region_reply["travel_state"]["start_location"])
        self.assertEqual("", region_reply["travel_state"]["transport"])
        self.assertFalse(region_reply["can_generate"])
        self.assertEqual("start_location", region_reply["travel_state"]["pending_slot"])
        agent.itinerary_engine.generate.assert_not_called()

    def test_ready_flag_only_after_all_core_conditions_are_present(self):
        agent = self.agent()
        _, payload = agent.send("부산역", state_raw=json.dumps({
            "region": "부산", "days": 1, "transport": "대중교통",
            "arrival_time": "10:00", "departure_time": "18:00", "pending_slot": "start_location",
        }))
        self.assertTrue(payload["can_generate"])
        self.assertEqual("", payload["travel_state"]["pending_slot"])
        self.assertEqual("ready_to_generate", payload["stage"])
        self.assertEqual([], payload["missing_slots"])
        agent.itinerary_engine.generate.assert_not_called()

    def test_standalone_station_answers_missing_start_even_if_pending_slot_was_lost(self):
        for prompt in ["조치원역", "조치원역이요"]:
            with self.subTest(prompt=prompt):
                agent = self.agent([{
                    "changed_slots": {}, "user_intent": "provide_information",
                }])
                _, payload = agent.send(prompt, state_raw=json.dumps({
                    "region": "세종", "destination": "세종", "days": 1,
                    "start_date": "2026-10-29", "end_date": "2026-10-29",
                    "conversation_stage": "collecting", "pending_slot": "",
                }))

                self.assertEqual("조치원역", payload["travel_state"]["start_location"])
                self.assertEqual("transport", payload["travel_state"]["pending_slot"])
                self.assertNotIn("시작점", payload["message"])

    def test_high_confidence_condition_typos_are_normalized(self):
        cases = [
            ("서을", {"pending_slot": "region"}, "region", "서울"),
            ("조치원녁", {"region": "세종", "pending_slot": "start_location"}, "start_location", "조치원역"),
            ("대중교퉁이요", {"region": "세종", "start_location": "조치원역", "pending_slot": "transport"}, "transport", "대중교통"),
        ]
        for prompt, state, field, expected in cases:
            with self.subTest(prompt=prompt):
                changed = self.machine.extract(prompt, state)["changed_slots"]
                self.assertEqual(expected, changed[field])

        changed = self.machine.extract("카폐가 좋아요", {"region": "서울"})["changed_slots"]
        self.assertIn("카페", changed["preferences"])

    def test_unknown_place_is_not_fuzzy_changed_to_a_different_city(self):
        changed = self.machine.extract("부천", {"pending_slot": "region"})["changed_slots"]
        self.assertEqual("부천", changed["region"])
        self.assertNotEqual("부산", changed["region"])

    def test_raw_internal_connection_failure_is_not_public(self):
        guard = self.loader.model("agents/travel_reply_guard")()
        raw = "2026-10-27 1일 일정의 7개 방문 구간을 실제 장소와 미정 동선으로 검증했지만, 자연·전망대·문화시설·카페 구간을 끝까지 연결하지 못했어요."
        payload = guard.public_payload({"message": raw, "failure_stage": "place_search"})
        self.assertNotIn("연결하지 못", payload["message"])
        self.assertNotIn("7개", payload["message"])
        self.assertNotIn("미정 동선", payload["message"])


if __name__ == "__main__":
    unittest.main()
