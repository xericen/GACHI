import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("course_catalog", ROOT / "src/model/struct/course.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Table:
    orm = None

    def __init__(self, rows):
        self.data = rows
        self.orm = self

    def create_table(self, safe=True):
        pass

    def rows(self, **where):
        where = {k: v for k, v in where.items() if k not in ["orderby", "order", "dump"]}
        return [dict(row) for row in self.data if all(row.get(k) == v for k, v in where.items())]

    def get(self, **where):
        return next(iter(self.rows(**where)), None)


class Core:
    def __init__(self):
        self.tables = {
            "course": Table([
                dict(id="mine", user_id="me", title="내 코스"),
                dict(id="shared", user_id="friend", title="친구 동행 코스"),
                dict(id="stranger", user_id="stranger", title="무관한 코스"),
            ]),
            "saved_course": Table([
                dict(user_id="me", course_id="saved", title="저장한 다른 사람 코스", places_json='[{"name":"장소"}]'),
                dict(user_id="me", course_id="mine", title="중복"),
                dict(user_id="other", course_id="private", title="다른 사람 저장"),
            ]),
            "companion_application": Table([
                dict(post_id="room-1", course_id="shared", owner_user_id="friend", applicant_user_id="me", status="accepted", updated="2026-10-16"),
                dict(post_id="room-2", course_id="mine", owner_user_id="me", applicant_user_id="friend", status="accepted", updated="2026-10-15"),
                dict(post_id="room-3", course_id="stranger", owner_user_id="stranger", applicant_user_id="other", status="accepted"),
                dict(post_id="room-4", course_id="saved", owner_user_id="friend", applicant_user_id="me", status="pending"),
            ]),
            "community_post": Table([
                dict(id="room-1", kind="companion", poll=json.dumps(dict(courseId="shared"))),
                dict(id="room-2", kind="companion", place="mine"),
                dict(id="room-3", kind="companion", place="stranger"),
                dict(id="room-4", kind="companion", place="saved"),
            ]),
        }

    def db(self, name):
        return self.tables[name]


class CourseCatalogTest(unittest.TestCase):
    def setUp(self):
        self.core = Core()
        self.course = module.Course(self.core)
        self.course.normalize = lambda row, **kwargs: dict(row)

    def test_saved_and_companion_courses_are_included_and_prioritized(self):
        rows = self.course.execution_catalog("me")
        self.assertEqual(["shared", "mine", "saved"], [row["id"] for row in rows])
        self.assertEqual(["companion", "mine", "saved"], [row["source"] for row in rows])
        self.assertEqual(["room-1"], rows[0]["companion_post_ids"])
        self.assertEqual(["room-2"], rows[1]["companion_post_ids"])
        self.assertEqual(1, rows[2]["place_count"])

    def test_only_current_users_accepted_matches_are_used(self):
        self.core.tables["companion_application"].data[0]["status"] = "declined"
        rows = self.course.execution_catalog("me")
        self.assertEqual(["mine", "saved"], [row["id"] for row in rows])
        self.assertNotIn("companion_post_ids", rows[1])
        self.assertEqual([], self.course.execution_catalog(""))

    def test_multiple_rooms_do_not_duplicate_the_course(self):
        self.core.tables["companion_application"].data.append(dict(
            post_id="room-5", course_id="mine", owner_user_id="me", applicant_user_id="another",
            status="accepted", updated="2026-10-14"))
        self.core.tables["community_post"].data.append(dict(id="room-5", kind="companion", place="mine"))
        rows = self.course.execution_catalog("me")
        mine = next(row for row in rows if row["id"] == "mine")
        self.assertEqual(["room-2", "room-5"], mine["companion_post_ids"])
        self.assertEqual(3, len(rows))

    def test_removed_room_does_not_remain_prioritized(self):
        self.core.tables["community_post"].data = []
        rows = self.course.execution_catalog("me")
        self.assertEqual(["mine", "saved"], [row["id"] for row in rows])
        self.assertFalse(any(row.get("companion_post_ids") for row in rows))


if __name__ == "__main__":
    unittest.main()
