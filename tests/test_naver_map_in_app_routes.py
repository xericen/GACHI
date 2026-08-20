from pathlib import Path
import ast
import math
import unittest


ROOT = Path(__file__).resolve().parents[1]
VIEW_TS = (ROOT / "src/app/page.access/view.ts").read_text(encoding="utf-8")
VIEW_PUG = (ROOT / "src/app/page.access/view.pug").read_text(encoding="utf-8")
VIEW_SCSS = (ROOT / "src/app/page.access/view.scss").read_text(encoding="utf-8")
API_PY = (ROOT / "src/app/page.access/api.py").read_text(encoding="utf-8")


class NaverMapInAppRouteTests(unittest.TestCase):
    def test_transit_and_walking_cta_stay_in_current_route_sheet(self):
        handler = VIEW_TS.split("public async openMapPlaceNavigation", 1)[1]
        handler = handler.split("public mapPlaceNavigationButtonLabel", 1)[0]

        self.assertNotIn("openNaverMapRoute", handler)
        self.assertIn("대중교통 예상 경로 보기", VIEW_TS)
        self.assertIn("도보 예상 경로 보기", VIEW_TS)

    def test_estimated_route_has_summary_steps_and_map_line(self):
        estimator = VIEW_TS.split("private drawEstimatedMapPlaceRoute", 1)[1]
        estimator = estimator.split("private mapTransitCountdown", 1)[0]

        self.assertIn("this.mapPlaceRouteSummary = `예상", estimator)
        self.assertIn("this.mapPlaceRouteSteps = [", estimator)
        self.assertIn("new google.maps.Polyline", estimator)
        self.assertIn("노선·환승·실시간 도착 정보는 제공되지 않습니다.", estimator)

    def test_route_button_waits_for_internal_steps(self):
        self.assertIn(
            "mapPlaceRouteLoading || mapPlaceRouteSteps.length === 0",
            VIEW_PUG,
        )
        self.assertNotIn("실제 경로와 운행정보는 NAVER 지도에서 확인합니다.", VIEW_PUG)

    def test_transit_routes_use_server_side_odsay_integration(self):
        self.assertIn("wiz.call('odsay_transit_routes'", VIEW_TS)
        self.assertIn("private mapOdsayTransitStep", VIEW_TS)
        self.assertIn("버스 번호·승하차 정류장·환승 순서", VIEW_TS)
        self.assertIn("def odsay_transit_routes():", API_PY)
        self.assertIn("_project_env_value(\"ODSAY_API_KEY\")", API_PY)
        self.assertIn("https://api.odsay.com/v1/api/searchPubTransPathT", API_PY)
        self.assertIn('"Origin": "https://travel.wizide.com"', API_PY)
        self.assertIn('"Referer": "https://travel.wizide.com/"', API_PY)

    def test_odsay_response_normalizes_bus_numbers_and_stops(self):
        tree = ast.parse(API_PY)
        names = {
            "_odsay_number",
            "_odsay_path_point",
            "_odsay_append_path_point",
            "_odsay_transit_payload",
        }
        selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
        namespace = {"math": math}
        exec(compile(ast.Module(body=selected, type_ignores=[]), "api.py", "exec"), namespace)
        routes = namespace["_odsay_transit_payload"]({
            "result": {
                "path": [{
                    "pathType": 2,
                    "info": {"totalTime": 34, "totalDistance": 12400, "totalWalk": 480},
                    "subPath": [{
                        "trafficType": 2,
                        "sectionTime": 21,
                        "distance": 9200,
                        "stationCount": 12,
                        "startName": "시청앞",
                        "endName": "한림프라자",
                        "lane": [{"busNo": "100", "busID": "bus-100"}],
                        "startX": 126.97,
                        "startY": 37.56,
                        "endX": 127.10,
                        "endY": 37.40,
                    }],
                }]
            }
        })

        self.assertEqual(routes[0]["line_labels"], ["100"])
        self.assertEqual(routes[0]["steps"][0]["start_name"], "시청앞")
        self.assertEqual(routes[0]["steps"][0]["end_name"], "한림프라자")
        self.assertEqual(routes[0]["steps"][0]["lanes"][0]["bus_no"], "100")

    def test_route_refresh_is_in_summary_header_and_map_rotation_is_removed(self):
        route_sheet = VIEW_PUG.split('section(class="gachi-place-navigation-sheet"', 1)[1]
        route_sheet = route_sheet.split('button(type="button", class="gachi-course-dim"', 1)[0]

        self.assertIn('class="refresh"', route_sheet)
        self.assertIn('refreshMapPlaceRoute($event)', route_sheet)
        self.assertNotIn('aria-label="지도 45도 회전"', VIEW_PUG)

    def test_route_sheet_can_hide_fully_and_reopen_from_route_bar(self):
        self.assertIn("transform: translateY(calc(100% + 18px));", VIEW_SCSS)
        self.assertIn("pointer-events: none;", VIEW_SCSS)
        self.assertIn('class="gachi-place-route-expand"', VIEW_PUG)
        self.assertIn('expandMapPlaceRouteSheet()', VIEW_PUG)
        self.assertIn("? this.mapPlaceRouteSheetDragHeight", VIEW_TS)


if __name__ == "__main__":
    unittest.main()
