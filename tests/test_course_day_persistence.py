from pathlib import Path
import importlib.util
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "course_struct",
    ROOT / "src/model/struct/course.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
Course = MODULE.Course


class MemoryTable:
    def __init__(self, rows=None):
        self.data = list(rows or [])

    def delete(self, **filters):
        self.data = [
            row for row in self.data
            if not all(row.get(key) == value for key, value in filters.items())
        ]

    def insert(self, row):
        self.data.append(dict(row))
        return row.get("id")

    def rows(self, **filters):
        filters.pop("orderby", None)
        filters.pop("order", None)
        return [
            dict(row) for row in self.data
            if all(row.get(key) == value for key, value in filters.items())
        ]

    def get(self, **filters):
        return next((dict(row) for row in self.data if all(row.get(key) == value for key, value in filters.items())), None)


class MemoryCore:
    def __init__(self):
        self.tables = {
            "course_place": MemoryTable(),
            "place": MemoryTable([{"id": "place-1"}, {"id": "place-2"}]),
        }

    def db(self, name):
        return self.tables[name]


class CourseDayPersistenceTests(unittest.TestCase):
    def test_course_place_metadata_keeps_composed_day(self):
        core = MemoryCore()
        course = Course(core)
        course._sync_course_places("course-1", [
            {"place_id": "place-1", "day": 1, "day_label": "1일차", "visit_time": "09:00"},
            {"place_id": "place-2", "day": 2, "day_label": "2일차", "visit_time": "10:00"},
        ])

        rows = core.tables["course_place"].rows(course_id="course-1")
        self.assertEqual(len(rows), 2)
        self.assertFalse(rows[0]["memo"].startswith("__gachi_item__"))
        self.assertTrue(rows[1]["memo"].startswith("__gachi_item__"))
        metadata = course._course_place_meta("course-1")
        self.assertEqual(metadata["place-1"].get("day", 1), 1)
        self.assertEqual(metadata["place-2"]["day"], 2)
        self.assertEqual(metadata["place-2"]["day_label"], "2일차")

    def test_page_api_has_runtime_day_metadata_fallback(self):
        api_source = (ROOT / "src/app/page.access/api.py").read_text(encoding="utf-8")
        route_source = (ROOT / "src/route/api.course.item/controller.py").read_text(encoding="utf-8")

        self.assertIn("def _sync_course_place_day_metadata", api_source)
        self.assertIn("_sync_course_place_day_metadata(row.get(\"id\"), data.get(\"places\", []))", api_source)
        self.assertIn("def _course_row_with_day_metadata", api_source)
        self.assertIn("def _row_with_day_metadata", route_source)
        self.assertIn("row = _row_with_day_metadata(struct, row)", route_source)

    def test_frontend_payload_embeds_day_metadata_for_stale_runtime(self):
        view_source = (ROOT / "src/app/page.access/view.ts").read_text(encoding="utf-8")

        self.assertIn("private courseBuilderStoredPlaceMemo", view_source)
        self.assertIn("return `__gachi_item__${JSON.stringify(meta)}`", view_source)
        self.assertIn("private profileCourseStoredPlaceMeta", view_source)
        self.assertIn("storedMeta.day_label || place.day_label", view_source)

    def test_owned_course_archive_is_persistent_and_reversible(self):
        api_source = (ROOT / "src/app/page.access/api.py").read_text(encoding="utf-8")
        model_source = (ROOT / "src/model/struct/course.py").read_text(encoding="utf-8")
        view_source = (ROOT / "src/app/page.access/view.ts").read_text(encoding="utf-8")
        template_source = (ROOT / "src/app/page.access/view.pug").read_text(encoding="utf-8")

        self.assertIn('archived_value = wiz.request.query("archived", "")', api_source)
        self.assertIn('if archived_value != "":', api_source)
        self.assertIn('archive_tag = "__gachi_archived__"', api_source)
        self.assertIn('row["archived"] = archive_tag in tags', model_source)
        self.assertIn("public async toggleMyCourseArchive", view_source)
        self.assertIn("private myCourseArchivePayload", view_source)
        self.assertIn("data: JSON.stringify(this.myCourseArchivePayload(course, archived))", view_source)
        self.assertIn("public archivedMyProfileCourses()", view_source)
        self.assertIn('class="course-blog-top-archive"', template_source)
        self.assertNotIn("span {{myCourseDeleteSubmittingId ? '삭제 중' : '삭제'}}", template_source)

        style_source = (ROOT / "src/app/page.access/view.scss").read_text(encoding="utf-8")
        self.assertIn(":not(.resume-top-actions):not(.course-blog-top-actions)", style_source)
        self.assertIn("flex-wrap: nowrap;", style_source)

    def test_course_builder_supports_family_companion(self):
        view_source = (ROOT / "src/app/page.access/view.ts").read_text(encoding="utf-8")
        template_source = (ROOT / "src/app/page.access/view.pug").read_text(encoding="utf-8")

        self.assertIn("family: '가족'", view_source)
        self.assertIn("['couple', 'friend', 'family', 'solo']", view_source)
        self.assertEqual(template_source.count("setCourseCompanionType('family')"), 2)
        style_source = (ROOT / "src/app/page.access/view.scss").read_text(encoding="utf-8")
        self.assertIn("grid-template-columns: repeat(4, minmax(0, 1fr));", style_source)


if __name__ == "__main__":
    unittest.main()
