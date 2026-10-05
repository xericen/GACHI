import ast
import copy
import datetime
import importlib.util
import json
import pathlib
import types
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "src/model" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


replan = load("travel_replan")
Growth = load("travel_growth").TravelGrowth


def place(pid, lat=37.0, lng=127.0, checked=False, category="공원", day=1):
    return dict(place_id=pid, name=pid, lat=lat, lng=lng, checked=checked,
                category=category, day=day, date="", order=1, checkin_method="auto" if checked else "")


class MemoryTable:
    def __init__(self, rows=()):
        self.data = [copy.deepcopy(r) for r in rows]
        self.orm = types.SimpleNamespace(create_table=lambda **kwargs: None)

    def rows(self, **kwargs):
        filters = {k: v for k, v in kwargs.items() if k not in ["orderby", "order", "dump"]}
        return [copy.deepcopy(r) for r in self.data if all(r.get(k) == v for k, v in filters.items())]

    def get(self, **kwargs):
        return next(iter(self.rows(**kwargs)), None)

    def insert(self, data):
        if any(r.get("id") == data["id"] for r in self.data):
            raise ValueError("duplicate")
        self.data.append(copy.deepcopy(data))
        return data["id"]

    def update(self, data, **kwargs):
        for row in self.data:
            if all(row.get(k) == v for k, v in kwargs.items()):
                row.update(copy.deepcopy(data))

    def delete(self, **kwargs):
        self.data = [r for r in self.data if not all(r.get(k) == v for k, v in kwargs.items())]


class Core:
    def __init__(self):
        self.tables = {}
        self.places = [place("one", checked=True), place("two", checked=True)]
        self.completed = {"alice", "bob"}
        self.course = types.SimpleNamespace(get=self.get_course, execution=self.execution,
            _execution_checkin_map=lambda cid, uid: {p["place_id"]: dict(method="auto", checked_at="now") for p in self.places} if uid in self.completed else {})
        self.user = types.SimpleNamespace(get=lambda uid: dict(id=uid, name=uid))

    def db(self, name):
        return self.tables.setdefault(name, MemoryTable())

    def get_course(self, course_id, include_places=False):
        return dict(id=course_id, user_id="alice", is_public=True, is_hidden=False,
                    region="서울", category="카페", tags=["문화"])

    def execution(self, course_id, user_id):
        ps = copy.deepcopy(self.places)
        for p in ps:
            p["checked"] = user_id in self.completed
        return dict(course=dict(id=course_id, region="서울", title="코스"), places=ps)


class ReplanTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime(2026, 10, 5, 14, 0)
        self.execution = dict(course=dict(id="trip"), places=[
            place("visited", checked=True), place("fixed", lat=37.001), place("park", lat=37.002)])
        self.candidates = [place("실내 박물관", lat=37.003, category="박물관")]

    def test_rain_replaces_only_unvisited_unlocked_and_does_not_mutate(self):
        original = copy.deepcopy(self.execution)
        result = replan.build_replan(self.execution, self.candidates, fixed_ids=["fixed"], rain=True, now=self.now)
        self.assertEqual(["visited", "fixed", "실내 박물관"], [p["place_id"] for p in result["execution"]["places"]])
        self.assertEqual(original, self.execution)
        self.assertEqual("강수 예보", result["detected"][0])

    def test_no_verified_nearby_candidate_preserves_schedule_with_warning(self):
        candidate = place("먼 박물관", lat=40, category="박물관")
        result = replan.build_replan(self.execution, [candidate], rain=True, now=self.now)
        self.assertEqual([p["place_id"] for p in self.execution["places"]],
                         [p["place_id"] for p in result["execution"]["places"]])
        self.assertTrue(result["warnings"])

    def test_invalid_fixed_id_is_rejected(self):
        with self.assertRaises(ValueError):
            replan.build_replan(self.execution, [], fixed_ids=["other"])

    def test_fixed_closed_place_is_kept_and_explained(self):
        result = replan.build_replan(self.execution, self.candidates,
            fixed_ids=["fixed"], closed_ids=["fixed"], now=self.now)
        self.assertEqual("fixed", result["execution"]["places"][1]["place_id"])
        self.assertTrue(any("고정" in w for w in result["warnings"]))

    def test_delay_preserves_day_and_fixed_slots(self):
        self.execution["places"] += [place("future", day=2)]
        result = replan.build_replan(self.execution, [], fixed_ids=["fixed"], delay=45, now=self.now)
        self.assertEqual("visited", result["execution"]["places"][0]["place_id"])
        self.assertEqual("fixed", result["execution"]["places"][1]["place_id"])
        self.assertEqual("future", result["execution"]["places"][3]["place_id"])

    def test_delay_shifts_pending_time_without_changing_fixed_appointment(self):
        self.execution["places"][1]["visit_time"] = "15:00"
        self.execution["places"][2]["visit_time"] = "16:00"
        result = replan.build_replan(self.execution, [], fixed_ids=["fixed"], delay=30, now=self.now)
        self.assertEqual("15:00", result["execution"]["places"][1]["visit_time"])
        self.assertEqual("16:30", result["execution"]["places"][2]["visit_time"])
        self.assertTrue(any("시각" in c["reason"] for c in result["changes"]))

    def test_future_itinerary_does_not_use_today_weather(self):
        for p in self.execution["places"]:
            p["date"] = "2026-10-06"
        result = replan.build_replan(self.execution, self.candidates, rain=True, delay=30, now=self.now)
        self.assertFalse(result["changes"])
        self.assertTrue(any("오늘" in w for w in result["warnings"]))

    def test_monthly_closure_and_cafe_street_are_not_invented_as_evidence(self):
        self.assertTrue(replan.closed_today(dict(rest_date="매주 월요일 휴무"), self.now.date()))
        self.assertFalse(replan.closed_today(dict(rest_date="매월 마지막 월요일"), self.now.date()))
        self.assertFalse(replan.indoors(dict(name="카페거리", category="관광지")))
        self.assertFalse(replan.coordinate(dict(lat=float("nan"), lng=127)))


class GrowthTests(unittest.TestCase):
    def setUp(self):
        self.core = Core()
        self.growth = Growth(self.core)
        self.core.db("companion_application").data = [dict(id="app", course_id="trip",
            owner_user_id="alice", applicant_user_id="bob", status="accepted")]

    def test_review_requires_both_completion_and_confirmed_relationship(self):
        self.core.completed.remove("bob")
        with self.assertRaises(PermissionError):
            self.growth.submit_review("alice", "trip", "bob", 5, "후기")
        self.core.completed.add("bob")
        with self.assertRaises(PermissionError):
            self.growth.submit_review("stranger", "trip", "alice", 5, "후기")
        with self.assertRaises(PermissionError):
            self.growth.submit_review("alice", "trip", "alice", 5, "자기 평가")

    def test_verified_review_persists_evidence_and_prevents_duplicate(self):
        self.growth.submit_review("alice", "trip", "bob", 4, "약속 시간을 지켰어요")
        trust = self.growth.trust("bob")
        self.assertEqual((1, 4.0, 1), (trust["count"], trust["average"], trust["reviewers"]))
        reviews = self.growth.reviews("alice", "trip")
        self.assertEqual(2, reviews["reviews"][0]["automatic"])
        with self.assertRaises(ValueError):
            self.growth.submit_review("alice", "trip", "bob", 5, "중복 후기")

    def test_invalid_rating_and_empty_comment_are_rejected(self):
        for rating, comment in [(6, "후기"), (0, "후기"), (5, " ")]:
            with self.assertRaises(ValueError):
                self.growth.submit_review("alice", "trip", "bob", rating, comment)

    def test_no_reviews_is_no_rating_not_fabricated_perfect_score(self):
        trust = self.growth.trust("bob")
        self.assertIsNone(trust["average"])
        self.assertEqual(0, trust["count"])

    def test_saved_follow_and_actual_execution_signals_are_account_scoped(self):
        self.core.db("saved_course").data = [dict(user_id="alice", location="제주", title="바다 여행", route_json='{"tags":["자연"]}')]
        self.core.db("user_content_state").data = [dict(user_id="alice", content_type="author_follow", content_id="bob", state="active")]
        self.growth.save_event("alice", "course_execute", "trip", {})
        signals = self.growth.signals("alice")
        self.assertIn("bob", signals["followed_authors"])
        self.assertIn("trip", signals["executed_courses"])
        self.assertIn("자연", signals["terms"])
        self.assertFalse(self.growth.signals("stranger")["executed_courses"])
        self.assertFalse(self.growth.signals("stranger")["followed_authors"])

    def test_personalization_opt_out_does_not_return_behavior(self):
        self.core.db("user_setting").data = [dict(user_id="alice", account_json='{"personalizedRecommendations":false}')]
        self.growth.save_event("alice", "course_execute", "trip", {})
        signals = self.growth.signals("alice")
        self.assertFalse(signals["enabled"])
        self.assertFalse(signals["terms"])
        self.assertFalse(signals["executed_courses"])

    def test_private_course_access_is_limited_to_owner_and_accepted_companion(self):
        self.core.course.get = lambda cid, include_places=False: dict(id=cid, user_id="alice", is_public=False, is_hidden=False)
        self.assertTrue(self.growth.accessible("alice", "trip"))
        self.assertTrue(self.growth.accessible("bob", "trip"))
        self.assertFalse(self.growth.accessible("stranger", "trip"))

    def test_replan_persistence_invalidates_when_original_itinerary_changes(self):
        execution = self.growth.execution("alice", "trip")
        proposal = dict(execution=copy.deepcopy(execution), changes=[])
        proposal["execution"]["places"].append(place("extra"))
        self.growth.persist_replan("alice", "trip", proposal)
        self.assertEqual(3, len(self.growth.execution("alice", "trip")["places"]))
        self.core.places.append(place("edited"))
        self.assertEqual("edited", self.growth.execution("alice", "trip")["places"][-1]["place_id"])


    def test_editing_original_schedule_invalidates_persisted_replan(self):
        execution = self.growth.execution("alice", "trip")
        proposal = dict(execution=copy.deepcopy(execution), changes=[])
        proposal["execution"]["places"][0]["name"] = "재계획 이름"
        self.growth.persist_replan("alice", "trip", proposal)
        self.core.places[0]["visit_time"] = "15:00"
        restored = self.growth.execution("alice", "trip")
        self.assertEqual("one", restored["places"][0]["name"])
        self.assertEqual("15:00", restored["places"][0]["visit_time"])


class GrowthApiTests(unittest.TestCase):
    def setUp(self):
        self.core = Core()
        self.core.completed = set()
        self.growth = Growth(self.core)
        source = (ROOT / "src/app/page.access/api.py").read_text()
        tree = ast.parse(source)
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name in ["travel_growth", "course_checkin"]]
        self.query = {}
        self.responses = []
        self.wiz = types.SimpleNamespace(
            request=types.SimpleNamespace(query=lambda key, default="": self.query.get(key, default)),
            response=types.SimpleNamespace(status=lambda code, **data: self.responses.append((code, data))))
        scope = dict(wiz=self.wiz, _current_user_id=lambda: "alice", struct=self.core,
                     travel_growth_model=self.growth, travel_replan_model=replan.build_replan,
                     _json_loads=lambda value, fallback: json.loads(value),
                     _safe_bool=lambda value, default=False: value in [True, "true", "1"],
                     hashlib=__import__("hashlib"), secrets=__import__("secrets"), json=json)
        exec(compile(ast.Module(body=functions, type_ignores=[]), "<growth-api>", "exec"), scope)
        self.api = scope["travel_growth"]
        self.checkin = scope["course_checkin"]

    def call(self, **query):
        self.query = query
        self.responses = []
        self.api()
        return self.responses[-1]

    def test_replan_preview_and_apply_uses_server_snapshot(self):
        code, preview = self.call(action="replan", course_id="trip", fixed_ids='["one"]')
        self.assertEqual(200, code)
        self.assertIn("token", preview)
        code, data = self.call(action="apply_replan", course_id="trip", token=preview["token"])
        self.assertEqual(200, code)
        self.assertEqual(2, len(data["execution"]["places"]))
        # Preview token cannot be reused.
        self.assertEqual(400, self.call(action="apply_replan", course_id="trip", token=preview["token"])[0])

    def test_stale_visit_record_rejects_apply_and_keeps_schedule(self):
        _, preview = self.call(action="replan", course_id="trip")
        self.core.completed.add("alice")
        code, data = self.call(action="apply_replan", course_id="trip", token=preview["token"])
        self.assertEqual(400, code)
        self.assertIn("변경", data["message"])
        self.assertIsNone(self.growth.event("alice", "travel_replan", "trip"))

    def test_forged_token_or_unknown_action_cannot_mutate(self):
        self.call(action="replan", course_id="trip")
        self.assertEqual(400, self.call(action="apply_replan", course_id="trip", token="forged")[0])
        self.assertEqual(400, self.call(action="other", course_id="trip")[0])

    def test_checkin_rejects_foreign_place_and_far_gps(self):
        for request in [dict(course_id="trip", place_id="fake"),
                        dict(course_id="trip", place_id="one", method="auto", lat="0", lng="0")]:
            self.query = request
            self.responses = []
            self.checkin()
            self.assertEqual(400, self.responses[-1][0])


class BehavioralRankingTests(unittest.TestCase):
    def test_ai_candidate_tie_uses_behavior_without_overriding_explicit_preference(self):
        from tests.test_ai_harness import ModelLoader, FixtureAiTools
        engine = ModelLoader().model("agents/travel_itinerary_engine")(FixtureAiTools())
        museum = dict(place_id="museum", name="미술관", category="문화", lat=37, lng=127)
        cafe = dict(place_id="cafe", name="카페", category="카페", lat=37, lng=127)
        picked = engine._pick_best([museum, cafe], set(), None, dict(behavioral_terms=["카페"]))
        self.assertEqual("cafe", picked["place_id"])
        picked = engine._pick_best([museum, cafe], set(), None,
                                   dict(preferences=["문화"], behavioral_terms=["카페"]))
        self.assertEqual("museum", picked["place_id"])
        self.assertEqual(0, engine._behavioral_preference_score(cafe,
                             dict(behavioral_terms=["카페"], excluded_preferences=["카페"])))


if __name__ == "__main__":
    unittest.main()
