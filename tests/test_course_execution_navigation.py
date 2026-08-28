from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
VIEW_TS = (ROOT / "src/app/page.access/view.ts").read_text(encoding="utf-8")
VIEW_PUG = (ROOT / "src/app/page.access/view.pug").read_text(encoding="utf-8")
API_PY = (ROOT / "src/app/page.access/api.py").read_text(encoding="utf-8")


class CourseExecutionNavigationTests(unittest.TestCase):
    def test_course_route_sheet_exposes_all_transport_modes(self):
        self.assertIn("{ key: 'transit', label: '대중교통'", VIEW_TS)
        self.assertIn("{ key: 'walk', label: '도보'", VIEW_TS)
        self.assertIn("{ key: 'car', label: '차량'", VIEW_TS)
        self.assertIn('class="gachi-route-travel-mode"', VIEW_PUG)
        self.assertIn('(click)="setTravelMode(mode.key)"', VIEW_PUG)

    def test_next_leg_is_shown_and_can_be_completed_from_route_sheet(self):
        self.assertIn("public executionNextSpot()", VIEW_TS)
        self.assertIn("public executionSegmentOriginLabel()", VIEW_TS)
        self.assertIn('{{executionSegmentOriginLabel()}}', VIEW_PUG)
        self.assertIn('(click)="toggleVisit(next, $event)"', VIEW_PUG)
        self.assertIn('{{next.order}}번 도착', VIEW_PUG)

    def test_manual_arrival_advances_origin_to_arrived_place(self):
        checkin = VIEW_TS.split("public async checkInSpot", 1)[1]
        checkin = checkin.split("public mapSpotsForLocation", 1)[0]

        self.assertIn("let spotCoordinate = this.spotLatLng(spot);", checkin)
        self.assertIn("this.executionLiveOrigin = arrivalCoordinate;", checkin)
        self.assertIn("this.mapStartCoordinate = arrivalCoordinate;", checkin)
        self.assertIn("this.mapRouteOverviewActive = !this.executionNextSpot();", checkin)

    def test_active_transit_leg_uses_odsay_and_keeps_overview_available(self):
        self.assertIn("private async renderExecutionTransitRoute", VIEW_TS)
        self.assertIn("wiz.call('odsay_transit_routes'", VIEW_TS)
        self.assertIn("this.mapRouteOverviewActive", VIEW_TS)
        self.assertIn("focusNextCourseLeg()", VIEW_PUG)
        self.assertIn("showFullCourseOverview()", VIEW_PUG)

    def test_course_guidance_stays_inside_the_web_map(self):
        self.assertNotIn("openMapDirections", VIEW_PUG)
        self.assertNotIn("nmap://route", VIEW_TS)
        self.assertNotIn("window.open(webFallback", VIEW_TS)
        self.assertIn("toggleExecutionNavigation($event)", VIEW_PUG)
        self.assertIn('class="gachi-navigation-hud"', VIEW_PUG)

    def test_live_guidance_refreshes_from_browser_gps(self):
        self.assertIn("private async startExecutionNavigation()", VIEW_TS)
        self.assertIn("navigator.geolocation.getCurrentPosition", VIEW_TS)
        self.assertIn("private async handleExecutionPosition", VIEW_TS)
        self.assertIn("forceRouteRefresh || reroute", VIEW_TS)
        self.assertIn("도착 반경 80m", VIEW_TS)

    def test_live_guidance_tracks_route_progress_and_reroutes_only_after_deviation(self):
        self.assertIn("private projectCoordinateToExecutionRoute", VIEW_TS)
        self.assertIn("private updateExecutionNavigationProgress", VIEW_TS)
        self.assertIn("this.executionNavigationStepIndex", VIEW_TS)
        self.assertIn("Date.now() - this.executionNavigationOffRouteSince >= 4000", VIEW_TS)
        self.assertIn("Date.now() - this.executionNavigationLastRerouteAt >= 12000", VIEW_TS)
        self.assertNotIn("moved >= 0.025 && elapsed >= 10000", VIEW_TS)

    def test_live_guidance_exposes_turn_distance_speed_eta_and_follow_camera(self):
        self.assertIn("executionNavigationNextDistance", VIEW_TS)
        self.assertIn("{{executionNavigationDistanceLabel()}}", VIEW_PUG)
        self.assertIn("km/h", VIEW_TS)
        self.assertIn("private followExecutionNavigationCamera", VIEW_TS)
        self.assertIn("path: 'NAV_ARROW'", VIEW_TS)

    def test_live_guidance_has_distance_voice_buckets_and_screen_wake_lock(self):
        self.assertIn("bucket === 'prepare'", VIEW_TS)
        self.assertIn("bucket === 'soon'", VIEW_TS)
        self.assertIn("wakeLock.request('screen')", VIEW_TS)
        self.assertIn("this.releaseExecutionWakeLock();", VIEW_TS)

    def test_navigation_mode_has_visible_turn_speed_map_and_arrival_hud(self):
        self.assertIn('class="gachi-navigation-hud"', VIEW_PUG)
        self.assertIn('{{executionNavigationDistanceLabel()}}', VIEW_PUG)
        self.assertIn('class="gachi-navigation-speed"', VIEW_PUG)
        self.assertIn('class="gachi-navigation-map-actions"', VIEW_PUG)
        self.assertIn('recenterExecutionNavigation($event)', VIEW_PUG)
        self.assertIn('resetExecutionNavigationCompass($event)', VIEW_PUG)
        self.assertIn('class="gachi-navigation-bottom"', VIEW_PUG)
        self.assertIn('{{executionNavigationEtaLabel()}}', VIEW_PUG)

    def test_navigation_mode_minimizes_legacy_course_sheet(self):
        self.assertIn('*ngIf="!executionNavigationActive && executionNextSpot()"', VIEW_PUG)
        self.assertIn('*ngIf="!executionNavigationActive && executionNextSpot() as next"', VIEW_PUG)
        self.assertIn('*ngIf="!executionNavigationActive", (click)="toggleMapRouteSheet()"', VIEW_PUG)
        self.assertNotIn('class="gachi-course-guidance", *ngIf="executionNavigationActive', VIEW_PUG)

    def test_entered_start_begins_immediately_and_gps_failure_does_not_stop_it(self):
        start = VIEW_TS.split("private async startExecutionNavigation()", 1)[1]
        start = start.split("private applyExecutionCourse", 1)[0]
        select = VIEW_TS.split("public async selectExecutionCourse", 1)[1]
        select = select.split("public async endExecutionCourse", 1)[0]

        self.assertIn("let origin = this.executionRouteOrigin();", start)
        self.assertIn("this.executionNavigationActive = true;", start)
        self.assertIn("this.scheduleNaverMapRender();", start)
        self.assertNotIn("this.executionNavigationActive = false;", start)
        self.assertNotIn("this.startExecutionGeofence();", select)

    def test_navigation_uses_fresh_live_location_and_only_next_target(self):
        start = VIEW_TS.split("private async startExecutionNavigation()", 1)[1]
        start = start.split("private applyExecutionCourse", 1)[0]
        position = VIEW_TS.split("private async handleExecutionPosition", 1)[1]
        position = position.split("public async checkInSpot", 1)[0]
        markers = VIEW_TS.split("private renderNaverMarkers", 1)[1]
        markers = markers.split("private renderNaverRoute", 1)[0]

        self.assertIn("await this.handleExecutionPosition(position, true);", start)
        self.assertIn("maximumAge: 0", start)
        self.assertIn("forceRouteRefresh ||", position)
        self.assertIn("this.executionNavigationUsingLiveLocation = true;", position)
        self.assertIn("? [this.executionNextSpot()].filter", markers)
        self.assertIn("this.executionNavigationActive ? this.executionNextSpot()", VIEW_TS)
        self.assertIn("!this.executionNavigationActive", VIEW_TS)

    def test_manual_arrival_keeps_fresh_gps_origin_when_navigation_is_active(self):
        checkin = VIEW_TS.split("public async checkInSpot", 1)[1]
        checkin = checkin.split("public mapSpotsForLocation", 1)[0]

        self.assertIn("let liveNavigationCoordinate", checkin)
        self.assertIn("liveNavigationCoordinate ||", checkin)
        self.assertIn("this.mapStartAddress = liveNavigationCoordinate ? '현재 위치'", checkin)

    def test_navigation_sheet_keeps_the_map_visible(self):
        self.assertNotIn('name="mapRouteStart"', VIEW_PUG)
        self.assertIn('[class.navigating]="executionNavigationActive"', VIEW_PUG)
        self.assertIn("public visibleExecutionNavigationSteps()", VIEW_TS)
        self.assertIn('class="gachi-navigation-bottom"', VIEW_PUG)
        self.assertIn('*ngIf="!executionNavigationActive && executionNextSpot() as next"', VIEW_PUG)
        self.assertIn('*ngIf="mapRouteSheetExpanded && !executionNavigationActive"', VIEW_PUG)

    def test_walk_mode_uses_free_real_footpath_route(self):
        self.assertIn("private async renderExecutionWalkingRoute", VIEW_TS)
        self.assertIn("wiz.call('free_walking_routes'", VIEW_TS)
        self.assertIn("routing.openstreetmap.de/routed-foot", API_PY)
        self.assertIn("OPENROUTESERVICE_API_KEY", API_PY)
        self.assertIn("_OPENROUTESERVICE_SAFE_DAILY_LIMIT = 1900", API_PY)
        self.assertNotIn("도보 경로는 거리 기반 예상 동선입니다.", VIEW_TS)

    def test_voice_guidance_stays_in_browser_without_paid_sdk(self):
        self.assertIn("speechSynthesis", VIEW_TS)
        self.assertIn("SpeechSynthesisUtterance", VIEW_TS)
        self.assertIn("toggleExecutionVoice($event)", VIEW_PUG)
        self.assertIn("음성 켜짐", VIEW_TS)


if __name__ == "__main__":
    unittest.main()
