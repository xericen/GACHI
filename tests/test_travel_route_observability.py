import os
import tempfile
import unittest

from tests.test_ai_harness import IntegrationModelLoader


class TravelRouteObservabilityTest(unittest.TestCase):
    def setUp(self):
        self.loader = IntegrationModelLoader()
        self.Monitor = self.loader.model("travel_route_observability")
        self.temp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temp.name, "route.jsonl")
        self.monitor = self.Monitor(path=self.path)

    def tearDown(self):
        self.temp.cleanup()

    def result(self, elapsed_ms=1200, simple=True, raw=30, selected=7):
        return {
            "ok": True,
            "draft": {
                "quality": {
                    "checks": {"simple_route_ok": simple},
                    "route_diagnostics": {"reasons": [] if simple else ["large_detour"]},
                },
                "metadata": {
                    "elapsed_ms": elapsed_ms,
                    "api_metrics": {
                        "total_route_requests": 12,
                        "route_cache_hits": 8,
                        "route_cache_misses": 4,
                        "successful_external_calls": 4,
                        "failed_external_calls": 0,
                        "route_optimization_ms": 200,
                    },
                    "candidate_pipeline": {
                        "stages": {"raw_candidates": {"count": raw}},
                        "returned_final_selection_count": selected,
                        "required_places": selected,
                    },
                },
            },
        }

    def test_record_persists_anonymized_route_metrics(self):
        health = self.monitor.record(
            self.result(), {"region": "제주", "transport": "대중교통", "days": 3},
            request_id="request-1",
        )

        self.assertTrue(os.path.exists(self.path))
        self.assertEqual(1, health["summary"]["window"])
        self.assertEqual(12, health["summary"]["total_route_requests"])
        self.assertNotIn("prompt", health["latest"])

    def test_summary_alerts_on_repeated_latency_and_route_quality_drop(self):
        for index in range(5):
            self.monitor.record(
                self.result(elapsed_ms=70000, simple=False),
                {"region": "제주", "transport": "대중교통", "days": 3},
                request_id=f"request-{index}",
            )

        summary = self.monitor.summary()
        self.assertIn("generation_time_spike", summary["alerts"])
        self.assertIn("simple_route_quality_drop", summary["alerts"])
        self.assertEqual(0, summary["simple_route_false_rate"] - 1)


if __name__ == "__main__":
    unittest.main()
