import datetime
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import Mock

spec = importlib.util.spec_from_file_location("zenly_proximity", Path(__file__).resolve().parents[1] / "src/model/struct/zenly.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SignalProximityTests(unittest.TestCase):
    def setUp(self):
        self.zenly = module.Zenly(Mock())
        self.zenly._is_together_blocked = Mock(return_value=False)
        self.origin = dict(id="a", lat=37.5, lng=127.0)
        self.peer = dict(id="b", lat=37.501, lng=127.0)

    def test_distance_self_and_block_rules(self):
        self.assertTrue(self.zenly._signal_peers_nearby(self.origin, self.peer))
        self.assertFalse(self.zenly._signal_peers_nearby(self.origin, dict(self.peer, lat=37.52)))
        self.assertFalse(self.zenly._signal_peers_nearby(self.origin, self.origin))
        self.assertFalse(self.zenly._signal_peers_nearby(self.origin, None))
        self.zenly._is_together_blocked.return_value = True
        self.assertFalse(self.zenly._signal_peers_nearby(self.origin, self.peer))

    def test_presence_expiry(self):
        db = Mock()
        self.zenly.db = Mock(return_value=db)
        now = datetime.datetime(2026, 10, 5, 12)
        self.zenly.now = lambda: now
        for seconds, expected in [(0, True), (60, True), (61, False), (-1, False)]:
            db.get.return_value = dict(self.peer, updated_at=now - datetime.timedelta(seconds=seconds))
            self.assertEqual(bool(self.zenly._signal_presence("b")), expected)

    def test_invalid_gps_never_writes(self):
        self.zenly.db = Mock()
        for lat, lng, accuracy in [(None, 127, 10), (91, 127, 10), (37, 181, 10),
                                   (float("nan"), 127, 10), (37, 127, 101), (37, 127, 0)]:
            self.assertIsNone(self.zenly.touch_signal_presence("a", lat, lng, accuracy))
        self.zenly.db.assert_not_called()

    def test_create_requires_other_live_neighbor_and_ignores_place(self):
        z = self.zenly
        z._report_restricted = lambda _: False
        z._daily_signal_count = lambda _: 0
        z.touch_signal_presence = Mock(return_value=self.origin)
        db = Mock()
        db.rows.return_value = [self.peer]
        db.get.return_value = dict(id="signal", user_id="a", lat=37.5, lng=127, expires_at=z.now())
        z.db = lambda _: db
        z._signal_payload = lambda row, _: row
        user = dict(id="a", email="a@example.test")
        z._signal_presence = lambda _: None
        self.assertEqual(z.create_signal(user, {})[0], 409)
        db.insert.assert_not_called()
        z._signal_presence = lambda _: self.peer
        self.assertEqual(z.create_signal(user, dict(place_id="remote"))[0], 200)
        inserted = db.insert.call_args.args[0]
        self.assertEqual(inserted["place_id"], "")
        self.assertEqual(inserted["lat"], self.origin["lat"])
        z.touch_signal_presence.return_value = None
        self.assertEqual(z.create_signal(user, {})[0], 400)

    def test_nearby_response_reports_signal_button_eligibility(self):
        z = self.zenly
        z.expire_signals = lambda: None
        z._signal_presence = lambda key: self.origin if key == "a" else self.peer
        class Condition:
            def __and__(self, other):
                return self

        class Field:
            def __eq__(self, other):
                return Condition()

            def __gt__(self, other):
                return Condition()

            def desc(self):
                return self

        signal_table = Mock(status=Field(), expires_at=Field(), created_at=Field())
        query = Mock()
        query.where.return_value.order_by.return_value.limit.return_value.dicts.return_value = []
        signal_table.select.return_value = query
        presence_db = Mock()
        presence_db.rows.return_value = [self.origin, self.peer]
        z.db = lambda name: presence_db if name == "signal_presence" else Mock(orm=signal_table)

        payload = z.nearby_signals(user_id="a")

        self.assertTrue(payload["hasNearbyTraveler"])
        self.assertEqual(payload["nearbyTravelerCount"], 1)

        presence_db.rows.return_value = [self.origin]
        payload = z.nearby_signals(user_id="a")
        self.assertFalse(payload["hasNearbyTraveler"])
        self.assertEqual(payload["nearbyTravelerCount"], 0)

    def test_respond_rejects_remote_before_response_write(self):
        z = self.zenly
        z.expire_signals = lambda: None
        db = Mock()
        db.get.return_value = dict(id="signal", user_id="b", status="active")
        z.db = lambda _: db
        z._signal_presence = lambda key: self.origin if key == "a" else dict(self.peer, lat=37.52)
        self.assertEqual(z.respond_signal("signal", dict(id="a"))[0], 403)
        db.insert.assert_not_called()


if __name__ == "__main__":
    unittest.main()
