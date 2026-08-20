import ast
import math
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "src/app/page.access/api.py"
FUNCTIONS = {
    "_naver_coordinate",
    "_walking_path",
    "_walking_instruction",
    "_openrouteservice_walking_payload",
    "_osm_foot_walking_payload",
}


def load_route_helpers():
    source = API_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS]
    module = ast.Module(body=selected, type_ignores=[])
    namespace = {"math": math}
    exec(compile(module, str(API_PATH), "exec"), namespace)
    return namespace


class FreeWalkingRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helpers = load_route_helpers()

    def test_osm_foot_route_is_normalized_with_korean_turns(self):
        payload = {
            "routes": [{
                "distance": 1234.4,
                "duration": 901.2,
                "geometry": {"coordinates": [[126.55, 33.24], [126.56, 33.25]]},
                "legs": [{"steps": [{
                    "distance": 120,
                    "duration": 80,
                    "name": "중정로",
                    "maneuver": {"type": "turn", "modifier": "left"},
                }]}],
            }]
        }
        routes = self.helpers["_osm_foot_walking_payload"](payload)

        self.assertEqual(routes[0]["provider"], "openstreetmap")
        self.assertEqual(routes[0]["total_time"], 16)
        self.assertEqual(routes[0]["total_distance"], 1234)
        self.assertIn("좌회전", routes[0]["steps"][0]["instruction"])

    def test_openrouteservice_route_is_normalized(self):
        payload = {
            "features": [{
                "geometry": {"coordinates": [[126.55, 33.24], [126.56, 33.25]]},
                "properties": {
                    "summary": {"distance": 800, "duration": 600},
                    "segments": [{"steps": [{
                        "type": 1,
                        "name": "해안로",
                        "distance": 90,
                        "duration": 70,
                    }]}],
                },
            }]
        }
        routes = self.helpers["_openrouteservice_walking_payload"](payload)

        self.assertEqual(routes[0]["provider"], "openrouteservice")
        self.assertEqual(routes[0]["total_time"], 10)
        self.assertIn("우회전", routes[0]["steps"][0]["instruction"])

    def test_coordinates_outside_korea_are_removed(self):
        path = self.helpers["_walking_path"]([[126.5, 33.3], [0, 0]])
        self.assertEqual(path, [{"lat": 33.3, "lng": 126.5}])


if __name__ == "__main__":
    unittest.main()
