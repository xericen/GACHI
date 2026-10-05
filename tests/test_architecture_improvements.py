import urllib.error
import unittest
from pathlib import Path

from tests.test_ai_harness import ModelLoader


ROOT = Path(__file__).resolve().parents[1]


class Response:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, _limit=-1):
        return self.payload


class ArchitectureImprovementTests(unittest.TestCase):
    def test_external_api_adapter_has_one_success_and_failure_contract(self):
        Client = ModelLoader().model("external_api")
        success = Client(opener=lambda *_args, **_kwargs: Response(b'{"ok":true}')).get_json(
            "fixture", "https://example.test"
        )
        self.assertEqual({"ok": True}, success["data"])
        self.assertEqual("fixture", success["provider"])
        self.assertFalse(success["retryable"])

        def unavailable(*_args, **_kwargs):
            raise urllib.error.URLError("offline")

        failed = Client(opener=unavailable).get_json("fixture", "https://example.test")
        self.assertFalse(failed["ok"])
        self.assertEqual("network_or_timeout", failed["error_code"])
        self.assertTrue(failed["retryable"])

    def test_planner_separates_request_state_and_exposes_evidence_and_retry(self):
        component = (ROOT / "src/app/page.access/view.ts").read_text(encoding="utf-8")
        template = (ROOT / "src/app/page.access/view.pug").read_text(encoding="utf-8")
        self.assertIn("interface PlannerRequestState", component)
        self.assertIn("public plannerTravelState: any = {};", component)
        self.assertIn("public plannerRequestState: PlannerRequestState", component)
        self.assertIn('data-testid="planner-evidence"', template)
        self.assertIn('data-testid="planner-api-retry"', template)

    def test_location_retention_scrubs_precise_coordinates(self):
        zenly = (ROOT / "src/model/struct/zenly.py").read_text(encoding="utf-8")
        expiry = (ROOT / "scripts/expireSignals.js").read_text(encoding="utf-8")
        for field in ["home_lat=None", "home_lng=None", "stay_lat=None", "stay_lng=None"]:
            self.assertIn(field, zenly)
        self.assertIn("c.home_lat = NULL", expiry)
        self.assertIn("INTERVAL 30 DAY", expiry)


if __name__ == "__main__":
    unittest.main()
