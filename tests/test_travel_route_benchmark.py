import unittest

from scripts.travel_route_benchmark import summarize


class TravelRouteBenchmarkTest(unittest.TestCase):
    def test_success_summary_includes_cross_day_connection_and_metrics(self):
        case = {"id": "success", "label": "성공"}
        data = {
            "stage": "draft_ready",
            "itinerary_draft": {
                "days": [
                    {"total_move_minutes": 20, "total_distance_meters": 3000, "places": [{}, {}]},
                    {
                        "total_move_minutes": 30,
                        "total_distance_meters": 4000,
                        "previous_day_connection": {"duration_minutes": 10, "distance_meters": 1000},
                        "places": [{}, {}],
                    },
                ],
                "quality": {"route_backtrack_count": 0, "checks": {"simple_route_ok": True}},
                "metadata": {
                    "elapsed_ms": 900,
                    "api_metrics": {
                        "tool_calls": 12, "place_search_calls": 4,
                        "directions_lookup_calls": 8, "external_api_calls": 3,
                    },
                    "candidate_pipeline": {
                        "stages": {
                            "raw_candidates": {"count": 30},
                            "region_validation_passed": {"count": 28},
                            "coordinate_validation_passed": {"count": 29},
                            "transport_reachable": {"count": 12},
                            "category_validation_passed": {"count": 27},
                            "mandatory_condition_passed": {"count": 14},
                            "route_candidates": {"count": 16},
                            "final_selected": {"count": 14},
                        },
                    },
                },
            },
        }

        result = summarize(case, 200, data, 1200)

        self.assertTrue(result["ok"])
        self.assertEqual(60, result["total_move_minutes"])
        self.assertEqual(8000, result["total_distance_meters"])
        self.assertEqual(12, result["tool_api_calls"])
        self.assertTrue(result["simple_route_ok"])
        self.assertEqual(30, result["raw_candidates"])
        self.assertEqual(12, result["transport_reachable"])
        self.assertEqual(14, result["final_selected"])

    def test_failure_summary_preserves_structured_shortage(self):
        case = {"id": "shortage", "label": "후보 부족"}
        data = {
            "stage": "error",
            "failure_reason": {
                "code": "insufficient_route_candidates",
                "shortage_categories": ["카페", "맛집"],
            },
            "metadata": {
                "elapsed_ms": 500,
                "api_metrics": {"tool_calls": 9, "place_search_calls": 9},
            },
        }

        result = summarize(case, 200, data, 700)

        self.assertFalse(result["ok"])
        self.assertEqual("insufficient_route_candidates", result["failure_code"])
        self.assertEqual(["카페", "맛집"], result["shortage_categories"])
        self.assertEqual(9, result["tool_api_calls"])
