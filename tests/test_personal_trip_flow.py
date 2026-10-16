import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("personal_trip", ROOT / "src/model/personal_trip.py")
personal_trip = importlib.util.module_from_spec(spec)
spec.loader.exec_module(personal_trip)


class FakeOrm:
    def create_table(self, safe=True):
        return None


class FakeDb:
    def __init__(self):
        self.orm = FakeOrm()
        self.data = {}

    def get(self, **where):
        return next((dict(row) for row in self.data.values()
                     if all(row.get(key) == value for key, value in where.items())), None)

    def rows(self, **where):
        where = {key: value for key, value in where.items() if key not in ["orderby", "order", "dump"]}
        rows = [dict(row) for row in self.data.values()
                if all(row.get(key) == value for key, value in where.items())]
        return sorted(rows, key=lambda row: row.get("updated"), reverse=True)

    def insert(self, row):
        self.data[row["id"]] = dict(row)
        return row["id"]

    def update(self, values, **where):
        for key, row in list(self.data.items()):
            if all(row.get(field) == value for field, value in where.items()):
                self.data[key] = dict(row, **values)


class FakeCore:
    def __init__(self):
        self.table = FakeDb()

    def db(self, name):
        assert name == "personal_trip"
        return self.table


class PersonalTripModelTest(unittest.TestCase):
    def setUp(self):
        self.engine = personal_trip.PersonalTrip(FakeCore())
        self.course = dict(id="course-1", title="도쿄 산책", location="도쿄")

    def test_dates_and_status_are_stored_outside_original_course(self):
        original = dict(self.course)
        row = self.engine.save("user-1", self.course, "2027-03-01", "2027-03-05", "saved")
        self.assertEqual(original, self.course)
        self.assertEqual("saved", row["course_source"])
        self.assertEqual("planned", row["status"])
        self.assertEqual("2027-03-01", row["start_date"])
        active = self.engine.set_status("user-1", row["id"], "active")
        self.assertEqual("active", active["status"])

    def test_dates_are_optional_and_existing_dates_survive_reload(self):
        original = dict(self.course)
        row = self.engine.save("user-1", self.course)
        self.assertEqual("", row["start_date"])
        self.assertEqual("", row["end_date"])
        self.assertEqual(original, self.course)
        self.engine.save("user-1", self.course, "2027-03-01", "2027-03-05")
        row = self.engine.save("user-1", self.course)
        self.assertEqual("2027-03-01", row["start_date"])
        self.assertEqual("2027-03-05", row["end_date"])

    def test_invalid_date_range_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "시작일과 종료일"):
            self.engine.save("user-1", self.course, "2027-03-05", "2027-03-01")

    def test_partial_dates_are_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.save("user-1", self.course, "2027-03-01", "")
        with self.assertRaises(ValueError):
            self.engine.save("user-1", self.course, "invalid", "2027-03-05")

    def test_records_are_scoped_by_user_and_course(self):
        first = self.engine.save("user-1", self.course, "2027-03-01", "2027-03-05")
        second = self.engine.save("user-2", self.course, "2027-04-01", "2027-04-05")
        self.assertNotEqual(first["id"], second["id"])
        self.assertIsNone(self.engine.get("user-2", first["id"]))


class PersonalTripIntegrationContractTest(unittest.TestCase):
    def test_map_flow_uses_current_trip_choice_not_course_companion_type(self):
        view = (ROOT / "src/app/page.access/view.ts").read_text()
        template = (ROOT / "src/app/page.access/view.pug").read_text()
        api = (ROOT / "src/app/page.access/api.py").read_text()
        course_model = (ROOT / "src/model/struct/course.py").read_text()

        self.assertIn("chooseTravelMode('solo')", template)
        self.assertIn("chooseTravelMode('companion')", template)
        self.assertNotIn("이번 여행 날짜", template)
        self.assertIn("openMyTripDeparture()", template)
        self.assertIn("지도에서 여행 시작", view)
        self.assertNotIn("String(course.companion_type || '') === 'solo'", view)
        self.assertIn("source=\"saved\"", course_model)
        self.assertIn('(\"trip:\" + trip_id)', api)


if __name__ == "__main__":
    unittest.main()
