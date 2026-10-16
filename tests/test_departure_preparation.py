import ast
import copy
import datetime
import importlib.util
import json
from pathlib import Path
import types
import unittest
import peewee as pw

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("departure", ROOT / "src/model/departure_preparation.py")
departure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(departure)


class Table:
    def __init__(self, model):
        self.orm = model
    def get(self, **where):
        return next(iter(self.rows(**where)), None)
    def rows(self, **where):
        query = self.orm.select()
        for key, value in where.items():
            query = query.where(getattr(self.orm, key) == value)
        return list(query.dicts())
    def insert(self, values):
        return self.orm.insert(**values).execute()
    def update(self, values, **where):
        query = self.orm.update(**values)
        for key, value in where.items():
            query = query.where(getattr(self.orm, key) == value)
        return query.execute()


class Core:
    def __init__(self):
        self.database = pw.SqliteDatabase(":memory:")
        class Base(pw.Model):
            class Meta:
                database = self.database
        self.tables = {}
        for name in ["departure_preparation", "mobile_push_job", "mobile_device"]:
            env = dict(wiz=types.SimpleNamespace(model=lambda _: types.SimpleNamespace(base=lambda _: Base)))
            exec((ROOT / f"src/model/db/{name}.py").read_text(), env)
            model = env["Model"]
            model.create_table()
            self.tables[name] = Table(model)
    def db(self, name):
        return self.tables[name]


def profile(**changes):
    data = dict(country="일본", transit="없음", nationality="대한민국", passport="check",
                communication="esim", payment="cash", insurance="needed", start="2027-03-01",
                end="2027-03-05", share=False, reminders=False)
    data.update(changes)
    return data


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.core = Core()
        self.engine = departure.Preparation(self.core)
        self.trip = dict(title="내 여행", destination="도쿄", start="2027-03-01", end="2027-03-05", country="")
    def tearDown(self):
        self.core.database.close()

    def test_reuses_saved_dates_and_recalculates_dday(self):
        trip = departure.trip_context(dict(title="여행", route=dict(start_date="2027-03-01", end_date="2027-03-05"), location="도쿄"))
        self.assertEqual("2027-03-01", trip["start"])
        plan = self.engine.plan(trip, {}, profile(start="2027-02-01", end="2027-02-02"))
        self.assertEqual("2027-03-01", plan["profile"]["start"])
        fixed = departure.generate(trip, plan["profile"], today=datetime.date(2027, 2, 1))
        self.assertEqual("D-28", fixed["dday"])
        self.assertEqual("2027-01-30", next(x for x in fixed["items"] if x["id"] == "entry")["due"])

    def test_dates_from_multiday_places_and_missing_date(self):
        trip = departure.trip_context(dict(places=[dict(date="2027-03-05"), dict(date="2027-03-01")]))
        self.assertEqual(("2027-03-01", "2027-03-05"), (trip["start"], trip["end"]))
        self.assertEqual("", departure.trip_context(dict(duration="3일"))["start"])

    def test_personal_conditions_select_different_items(self):
        a = self.engine.plan(self.trip, {}, profile())
        b = self.engine.plan(self.trip, {}, profile(nationality="미국", communication="ready", payment="ready", insurance="ready"))
        self.assertGreater(len(a["items"]), len(b["items"]))
        self.assertIn("미국", next(x for x in b["items"] if x["id"] == "entry")["reason"])

    def test_domestic_skips_overseas_tasks(self):
        plan = self.engine.plan(self.trip, {}, profile(country="대한민국"))
        self.assertEqual(["schedule"], [x["id"] for x in plan["items"]])

    def test_invalid_or_missing_conditions_rejected(self):
        for patch in [dict(nationality=""), dict(transit=""), dict(start="2027-02-30"),
                      dict(end="2027-02-01"), dict(communication="unknown")]:
            with self.assertRaises(ValueError):
                departure.normalize_profile(profile(**patch))

    def test_date_change_resets_only_affected_completed_items(self):
        old = self.engine.plan(self.trip, {}, profile())
        for item in old["items"]:
            item["done"] = True
        trip = dict(self.trip, start="2027-03-02", end="2027-03-06")
        new = self.engine.plan(trip, old)
        items = {x["id"]: x for x in new["items"]}
        self.assertTrue(items["money"]["done"])
        self.assertTrue(items["customs"]["done"])
        self.assertFalse(items["entry"]["done"])
        self.assertTrue(items["entry"]["recheck"])
        self.assertNotEqual(old["items"][0]["due"], new["items"][0]["due"])

    def test_nationality_change_only_invalidates_entry_and_arrival(self):
        old = self.engine.plan(self.trip, {}, profile())
        for item in old["items"]:
            item["done"] = True
        new = self.engine.plan(self.trip, old, profile(nationality="미국"))
        self.assertEqual({"entry", "arrival"}, set(new["changed"]))
        self.assertTrue(next(x for x in new["items"] if x["id"] == "insurance")["done"])

    def test_db_persistence_is_separate_per_person_and_trip(self):
        a = self.engine.plan(self.trip, {}, profile())
        a["items"][0]["done"] = True
        self.engine.save("room:one", "alice", a)
        self.engine.save("room:one", "bob", self.engine.plan(self.trip, {}, profile()))
        self.assertTrue(self.engine.load("room:one", "alice")["items"][0]["done"])
        self.assertFalse(self.engine.load("room:one", "bob")["items"][0]["done"])
        self.assertEqual({}, self.engine.load("room:two", "alice"))
        self.engine.save("room:one", "alice", a)
        self.assertEqual(2, len(self.engine.db().rows()))

    def test_course_edit_refreshes_persisted_preparation(self):
        self.core.tables["community_post"] = types.SimpleNamespace(rows=lambda **where: [])
        old = self.engine.plan(self.trip, {}, profile())
        for item in old["items"]:
            item["done"] = True
        self.engine.save("course:one", "alice", old)
        self.engine.refresh_course("one", dict(title="도쿄", region="도쿄", places=[dict(date="2027-03-03"), dict(date="2027-03-08")]))
        loaded = self.engine.load("course:one", "alice")
        self.assertEqual("2027-03-03", loaded["profile"]["start"])
        self.assertTrue(next(x for x in loaded["items"] if x["id"] == "entry")["recheck"])
        self.assertTrue(next(x for x in loaded["items"] if x["id"] == "money")["done"])

    def test_reminder_read_persists_and_changed_dates_use_new_ids(self):
        old = self.engine.plan(self.trip, {}, profile(reminders=True))
        old["read_reminders"] = [old["reminders"][0]["id"]]
        new = self.engine.plan(self.trip, old)
        self.assertTrue(new["reminders"][0]["read"])
        changed = self.engine.plan(dict(self.trip, start="2027-03-02", end="2027-03-06"), old)
        self.assertFalse(changed["reminders"][0]["read"])

    def test_push_reservation_deduplicates_and_cancels_obsolete_jobs(self):
        now = datetime.datetime.now()
        self.core.db("mobile_device").insert(dict(id="device", user_id="alice", device_token="token", platform="ios",
            enabled=True, created=now, updated=now))
        plan = self.engine.plan(self.trip, {}, profile(reminders=True))
        self.engine.schedule("course:one", "alice", plan)
        self.engine.schedule("course:one", "alice", plan)
        jobs = self.core.db("mobile_push_job")
        self.assertEqual(3, len(jobs.rows(status="queued")))
        first = jobs.rows()[0]
        jobs.update(dict(status="sent"), id=first["id"])
        self.engine.schedule("course:one", "alice", plan)
        self.assertEqual(1, len(jobs.rows(status="sent")))
        changed = self.engine.plan(dict(self.trip, start="2027-03-02", end="2027-03-06"), plan)
        self.engine.schedule("course:one", "alice", changed)
        self.assertEqual(3, len(jobs.rows(status="queued")))
        self.assertEqual(2, len(jobs.rows(status="cancelled")))
        changed["profile"]["reminders"] = False
        self.engine.schedule("course:one", "alice", changed)
        self.assertEqual(0, len(jobs.rows(status="queued")))


class ResponseExit(BaseException):
    def __init__(self, code, data):
        self.code, self.data = code, data


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.core = Core()
        self.engine = departure.Preparation(self.core)
        tree = ast.parse((ROOT / "src/app/page.access/api.py").read_text())
        fn = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "departure_preparation")
        self.code = compile(ast.Module(body=[fn], type_ignores=[]), "api.py", "exec")
        self.trip = dict(id="course", user_id="alice", title="도쿄", region="도쿄", places=[dict(date="2027-03-01")])
    def tearDown(self):
        self.core.database.close()
    def request(self, user="alice", query=None, accepted=True):
        query = query or dict(course_id="course")
        def status(code, **data):
            raise ResponseExit(code, data)
        def db(name):
            if name == "saved_course":
                return types.SimpleNamespace(get=lambda **kw: None)
            return self.core.db(name)
        struct = types.SimpleNamespace(db=db, course=types.SimpleNamespace(get=lambda *a, **kw: copy.deepcopy(self.trip)))
        env = dict(json=json, wiz=types.SimpleNamespace(
            request=types.SimpleNamespace(query=lambda k, default="": query.get(k, default)),
            response=types.SimpleNamespace(status=status), model=lambda name: lambda core: self.engine),
            struct=struct, _current_user_id=lambda: user,
            _accepted_companion_application=lambda *a: dict(owner_user_id="alice", applicant_user_id="bob") if accepted else None,
            _companion_post_row=lambda *a: dict(courseId="course", date="2027-03-01"),
            _companion_post_payload=lambda row: row,
            _course_row_with_day_metadata=lambda row: row, _json_loads=lambda value, fallback: json.loads(value or json.dumps(fallback)))
        exec(self.code, env)
        try:
            env["departure_preparation"]()
        except ResponseExit as result:
            return result.code, result.data
        self.fail("No response")

    def test_guest_and_unsaved_course_are_rejected(self):
        self.assertEqual(401, self.request(user="")[0])
        self.assertEqual(403, self.request(user="outsider")[0])
        self.assertEqual(403, self.request(user="outsider", query=dict(post_id="room"), accepted=False)[0])

    def test_private_conditions_never_appear_in_shared_response(self):
        self.engine.save("room:room", "bob", self.engine.plan(
            dict(title="旅", destination="도쿄", start="2027-03-01", end="2027-03-01", country=""), {}, profile(share=False)))
        query = dict(post_id="room")
        code, data = self.request(query=query)
        self.assertEqual(200, code)
        self.assertEqual([], data["preparation"]["shared"])
        bob = self.engine.load("room:room", "bob")
        bob["profile"]["share"] = True
        self.engine.save("room:room", "bob", bob)
        code, data = self.request(query=query)
        shared = data["preparation"]["shared"][0]
        self.assertEqual({"label", "completed", "total", "items"}, set(shared))
        self.assertTrue(all(set(item) == {"label", "done"} for item in shared["items"]))
        self.assertNotIn("대한민국", json.dumps(shared, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
