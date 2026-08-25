import base64
import hashlib
import hmac
import json


class Controller:
    def __init__(self, wiz, socketio):
        self.secret = wiz.model("auth_config").jwt_secret()
        self.socketio = socketio
        self.namespace = "/wiz/app/main/page.access"
        self.event_cursor = 0
        struct_marker = "gachi_companion_chat_struct"
        self.struct = getattr(wiz.server.app, struct_marker, None)
        if self.struct is None:
            self.struct = wiz.model("struct")
            setattr(wiz.server.app, struct_marker, self.struct)
        marker = "gachi_companion_message_fanout_started"
        if not getattr(wiz.server.app, marker, False):
            self.event_cursor = self._latest_event_id()
            setattr(wiz.server.app, marker, True)
            socketio.start_background_task(target=self._fanout_loop)

    def connect(self, wiz):
        pass

    def join(self, wiz, data, io, flask):
        user_id = self._verified_user_id((data or {}).get("token", ""))
        if not user_id:
            return
        io.join("user:{}".format(user_id))
        io.emit("direct_chat_ready", {"connected": True}, to=flask.request.sid)

    def _verified_user_id(self, token):
        token = str(token or "")
        if token.startswith("Bearer "):
            token = token[7:]
        parts = token.split(".")
        if len(parts) != 3:
            return ""
        signing_input = "{}.{}".format(parts[0], parts[1]).encode("utf-8")
        expected = hmac.new(self.secret, signing_input, hashlib.sha256).digest()
        try:
            actual = self._decode(parts[2])
            if not hmac.compare_digest(expected, actual):
                return ""
            payload = json.loads(self._decode(parts[1]).decode("utf-8"))
            return str(payload.get("sub") or "")[:32]
        except Exception:
            return ""

    def _decode(self, value):
        value = value + ("=" * (-len(value) % 4))
        return base64.urlsafe_b64decode(value.encode("utf-8"))

    def _fanout_loop(self):
        while True:
            try:
                self._fanout_chat_events()
            except Exception:
                pass
            self.socketio.sleep(0.25)

    def _latest_event_id(self):
        event_db = self.struct.db("companion_chat_event")
        event_db.orm.create_table(safe=True)
        rows = event_db.rows(orderby="id", order="DESC", dump=1)
        return int(rows[0].get("id") or 0) if rows else 0

    def _fanout_chat_events(self):
        event_db = self.struct.db("companion_chat_event")
        event_db.orm.create_table(safe=True)
        rows = event_db.rows(
            query=lambda model, query: query.where(model.id > self.event_cursor),
            orderby="id",
            order="ASC",
            dump=500
        )
        application_db = self.struct.db("companion_application")
        application_db.orm.create_table(safe=True)
        for row in rows:
            event_id = int(row.get("id") or 0)
            if event_id <= self.event_cursor:
                continue
            post_id = str(row.get("post_id") or "")
            self.event_cursor = event_id
            try:
                payload = json.loads(row.get("payload_json") or "{}")
            except Exception:
                payload = {}
            if not isinstance(payload, dict):
                continue
            event_type = str(row.get("event_type") or "")
            if event_type in [
                "together_meeting_message",
                "together_meeting_ended",
                "together_meeting_read",
                "together_meeting_typing",
                "together_location_update",
                "together_location_consent",
                "together_participant_blocked",
            ]:
                participants = payload.pop("participantKeys", [])
                if not isinstance(participants, list):
                    continue
                for user_id in set(str(value or "")[:32] for value in participants):
                    if user_id:
                        self.socketio.emit(
                            event_type,
                            payload,
                            namespace=self.namespace,
                            to="user:{}".format(user_id)
                        )
                continue
            if event_type not in ["direct_message", "direct_message_read"]:
                continue
            application = application_db.get(post_id=post_id, status="accepted")
            if application is None:
                continue
            participants = {
                str(application.get("owner_user_id") or ""),
                str(application.get("applicant_user_id") or "")
            }
            for user_id in participants:
                if user_id:
                    self.socketio.emit(
                        event_type,
                        payload,
                        namespace=self.namespace,
                        to="user:{}".format(user_id)
                    )
