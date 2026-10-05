import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
VIEW_TS = (ROOT / "src/app/page.access/view.ts").read_text(encoding="utf-8")
VIEW_PUG = (ROOT / "src/app/page.access/view.pug").read_text(encoding="utf-8")
API_PY = (ROOT / "src/app/page.access/api.py").read_text(encoding="utf-8")
STRUCT_PY = (ROOT / "src/model/struct.py").read_text(encoding="utf-8")
MOBILE_PY = (ROOT / "src/model/struct/mobile.py").read_text(encoding="utf-8")


class ProductGrowthFeatureTests(unittest.TestCase):
    def test_my_profile_no_longer_contains_trip_hub(self):
        self.assertNotIn('class="trip-hub-card"', VIEW_PUG)
        self.assertNotIn("public tripHubChecklist()", VIEW_TS)
        self.assertNotIn("public async openTripHubChat()", VIEW_TS)

    def test_server_notification_inbox_is_persisted_and_readable(self):
        self.assertIn('"user_notification"', STRUCT_PY)
        self.assertIn('notification_db = self.core.db("user_notification")', MOBILE_PY)
        self.assertIn("def notifications():", API_PY)
        self.assertIn("action == \"read_all\"", API_PY)
        self.assertIn("private async loadNotifications", VIEW_TS)

    def test_course_share_and_calendar_export_are_available(self):
        self.assertIn("public async shareCourse", VIEW_TS)
        self.assertIn("public async exportCourseCalendar", VIEW_TS)
        self.assertIn("BEGIN:VCALENDAR", VIEW_TS)
        self.assertIn("링크 공유", VIEW_PUG)

    def test_collaboration_storage_is_preserved_but_course_panel_is_removed(self):
        self.assertIn('"course_collaboration_item"', STRUCT_PY)
        self.assertIn('"course_collaboration_vote"', STRUCT_PY)
        self.assertIn("def course_collaboration():", API_PY)
        self.assertIn('action == "vote"', API_PY)
        self.assertIn('action == "status"', API_PY)
        self.assertIn("public async submitCourseCollaboration", VIEW_TS)
        self.assertNotIn("공동 코스 편집·투표", VIEW_PUG)
        self.assertNotIn('class="course-collaboration-panel"', VIEW_PUG)


if __name__ == "__main__":
    unittest.main()
