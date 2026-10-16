import datetime
import json
import unittest

from tests.test_ai_harness import IntegrationModelLoader, ModelLoader, SequenceProvider


class TravelEventTest(unittest.TestCase):
    def setUp(self):
        self.loader = ModelLoader()
        self.Events = self.loader.model("agents/travel_events")
        self.events = self.Events(today_provider=lambda: datetime.date(2026, 10, 5))
        self.state = self.loader.model("agents/travel_planner_state")().normalize({})

    def row(self, **changes):
        row = {
            "kind": "야구", "name": "LG vs 두산", "date": "2026-10-09",
            "time": "18:30", "venue": "잠실야구장", "source_url": "https://www.koreabaseball.com/Schedule/Schedule.aspx",
            "duration_minutes": None,
        }
        row.update(changes)
        return row

    def test_ambiguous_concert_asks_one_identifier(self):
        result = self.events.handle("이번주에 엄마랑 어떤 콘서트를 가", self.state)
        self.assertEqual("공연명이나 가수명을 알려주세요.", result["message"])
        self.assertEqual("event_name", self.state["pending_slot"])
        self.assertEqual("2026-10-11", self.state["event_request"]["end"])
        self.assertEqual({}, self.state["event_selection"])

    def test_named_event_queries_official_source_and_sets_fixed_time(self):
        calls = []
        self.state["must_visit_places"] = ["두산 야구", "경복궁"]
        self.events.sources.lookup = lambda *args: calls.append(args) or [self.row()]
        result = self.events.handle("이번주에 엄마랑 두산 야구 보러 가", self.state)
        self.assertEqual("야구", calls[0][0])
        self.assertEqual("두산", calls[0][1])
        self.assertEqual("18:30", self.state["event_selection"]["time"])
        self.assertEqual(["경복궁", "잠실야구장"], self.state["must_visit_places"])
        self.assertEqual("서울", self.state["region"])
        self.assertIn("공식 일정", result["message"])

    def test_event_keeps_existing_multiday_trip(self):
        self.state.update({"start_date": "2026-10-08", "end_date": "2026-10-10", "days": 3})
        self.events.select(self.state, self.row())
        self.assertEqual("2026-10-08", self.state["start_date"])
        self.assertEqual(3, self.state["days"])

    def test_multiple_sessions_require_selection_without_guessing(self):
        self.events.sources.lookup = lambda *args: [self.row(), self.row(date="2026-10-10")]
        result = self.events.handle("이번주 두산 야구", self.state)
        self.assertEqual(2, len(result["replies"]))
        self.assertEqual({}, self.state["event_selection"])
        self.events.handle("2번", self.state)
        self.assertEqual("2026-10-10", self.state["event_selection"]["date"])

    def test_source_failure_uses_ticket_without_inventing_schedule(self):
        self.events.sources.lookup = lambda *args: []
        result = self.events.handle("이번주 아이유 콘서트", self.state)
        self.assertNotIn("못", result["message"])
        self.assertEqual({}, self.state["event_selection"])
        self.state["start_date"] = "2026-10-10"
        self.events.handle("10월 10일 오후 7시", self.state)
        result = self.events.handle("올림픽공원", self.state)
        self.assertEqual("19:00", self.state["event_selection"]["time"])
        self.assertEqual("user", self.state["event_selection"]["source"])
        self.assertNotIn("공식 일정", result["message"])

    def test_unrelated_results_are_not_selected(self):
        self.events.sources.lookup = lambda *args: [self.row(name="롯데 vs 삼성")]
        self.events.handle("두산 야구", self.state)
        self.assertEqual({}, self.state["event_selection"])

    def test_official_kbo_parser_handles_rowspan_and_cancelled_games(self):
        sources = self.loader.model("agents/travel_event_sources")(lambda name: "")
        rows = [
            {"row": [
                {"Class": "day", "Text": "10.09(금)"}, {"Class": "time", "Text": "<b>18:30</b>"},
                {"Class": "play", "Text": "<span>LG</span><span>vs</span><span>두산</span>"},
                {"Text": "잠실"}, {"Text": "-"},
            ]},
            {"row": [
                {"Class": "time", "Text": "18:30"}, {"Class": "play", "Text": "<span>NC</span><span>vs</span><span>KT</span>"},
                {"Text": "수원"}, {"Text": "우천취소"},
            ]},
        ]
        sources._request = lambda *args, **kwargs: json.dumps({"rows": rows})
        result = sources.lookup("야구", "두산", datetime.date(2026, 10, 9), datetime.date(2026, 10, 9))
        self.assertEqual(1, len(result))
        self.assertEqual("잠실야구장", result[0]["venue"])

    def test_official_football_parser_ignores_unannounced_time(self):
        sources = self.loader.model("agents/travel_event_sources")(lambda name: "")
        sources._request = lambda *args, **kwargs: json.dumps({"data": {"scheduleList": [{
            "gameDate": "2026.10.09", "gameTime": "미정", "homeTeamName": "서울", "awayTeamName": "수원",
        }]}})
        self.assertEqual([], sources.lookup("축구", "서울", datetime.date(2026, 10, 9), datetime.date(2026, 10, 9)))

    def test_kopis_weekday_session_and_source(self):
        sources = self.loader.model("agents/travel_event_sources")(lambda name: "fixture-key")
        listing = "<dbs><db><mt20id>PF123</mt20id></db></dbs>"
        detail = """<dbs><db><prfnm>공연 A</prfnm><fcltynm>서울극장</fcltynm>
        <prfpdfrom>2026.10.09</prfpdfrom><prfpdto>2026.10.11</prfpdto>
        <dtguidance>금요일(19:30)/토요일(14:00,18:00)</dtguidance><prfruntime>2시간 10분</prfruntime></db></dbs>"""
        sources._request = lambda url: detail if "/PF123?" in url else listing
        rows = sources.lookup("연극", "공연 A", datetime.date(2026, 10, 9), datetime.date(2026, 10, 10))
        self.assertEqual(["19:30", "14:00", "18:00"], [row["time"] for row in rows])
        self.assertEqual(130, rows[0]["duration_minutes"])
        self.assertIn("PF123", rows[0]["source_url"])

    def test_chat_event_selection_survives_next_turn(self):
        loader = IntegrationModelLoader()
        types = loader.model("ai_harness/types")
        agent = loader.model("agents/travel_planner")(loader)
        agent.harness.config.model_provider = SequenceProvider(types, [
            types.ModelResponse(text="{}", tool_calls=[], model="fixture"),
            types.ModelResponse(text="{}", tool_calls=[], model="fixture"),
        ])
        agent.events.sources.lookup = lambda *args: [self.row(), self.row(date="2026-10-10")]
        _, payload = agent.send("이번주 두산 야구")
        _, selected = agent.send("2번", state_raw=json.dumps(payload["travel_state"]))
        self.assertEqual("ready_to_generate", selected["stage"])
        self.assertEqual("2026-10-10", selected["travel_state"]["event_selection"]["date"])

    def test_event_day_plan_reserves_time_and_avoids_overlap(self):
        loader = IntegrationModelLoader()
        engine = loader.model("agents/travel_itinerary_engine")(loader.ai_tools)
        machine = loader.model("agents/travel_planner_state")()
        state = machine.apply_generation_defaults(machine.normalize({
            "region": "서울", "start_date": "2026-10-09", "days": 1,
            "event_selection": self.row(),
        }))
        plan = engine._day_plan(state, 0, 1)
        self.assertEqual("fixed_event", plan["slots"][-1]["key"])
        self.assertEqual("18:30", plan["slots"][-1]["target_time"])
        for slot in plan["slots"][:-1]:
            self.assertLessEqual(engine._minutes(slot["target_time"], 0) + slot["duration_minutes"], 17 * 60)

    def test_full_itinerary_keeps_verified_event_time(self):
        loader = IntegrationModelLoader()
        tools = loader.ai_tools
        original = tools.execute_place_search
        def search(data):
            result = original(data)
            if data.get("keyword") == "부산시민회관" and result.get("results"):
                result["results"][0] = dict(result["results"][0], name="부산시민회관")
            return result
        tools.execute_place_search = search
        machine = loader.model("agents/travel_planner_state")()
        state = machine.apply_generation_defaults(machine.normalize({
            "region": "부산", "days": 1, "start_date": "2026-10-09",
            "start_location": "부산역", "must_visit_places": ["부산시민회관"],
            "event_selection": self.row(venue="부산시민회관", name="공연 A"),
        }))
        generated = loader.model("agents/travel_itinerary_engine")(tools).generate(state)
        self.assertTrue(generated["ok"], generated.get("failure_reason"))
        places = generated["draft"]["days"][0]["places"]
        event = next(place for place in places if place["schedule_slot"] == "fixed_event")
        self.assertEqual("18:30", event["time"])
        self.assertEqual("event", event["route_locked_reason"])
        self.assertTrue(event["route_time_fixed"])
        self.assertTrue(event["event_source_url"])
        for place in places:
            if place is not event:
                hour, minute = map(int, place["time"].split(":"))
                self.assertLessEqual(hour * 60 + minute + place["duration_minutes"], 18 * 60 + 30)

    def test_public_failure_messages_are_actionable(self):
        guard = self.loader.model("agents/travel_reply_guard")()
        payload = guard.public_payload({
            "message": "요청한 장소를 정확히 확인하지 못했어요.",
            "failure_stage": "place_search", "warnings": ["검색 결과 부족", "검증 실패"],
        })
        self.assertNotIn("못", payload["message"])
        self.assertEqual([], payload["warnings"])


if __name__ == "__main__":
    unittest.main()
