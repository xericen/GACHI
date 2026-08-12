import copy
import json
import threading
import time
import uuid


TravelPlannerAgent = wiz.model("agents/travel_planner")
LegacyAiChat = wiz.model("ai_chat_legacy")
AiHarnessSwitch = wiz.model("ai_harness_switch")
ChatStabilizationMonitor = wiz.model("ai_chat_observability")
ReplyGuard = wiz.model("agents/travel_reply_guard")


class AiChatFacade:
    def __init__(self, wiz_context=None, agent=None, legacy_factory=None, switch=None, monitor=None):
        self.wiz = wiz_context or wiz
        self.agent = agent or TravelPlannerAgent(self.wiz)
        self.legacy_factory = legacy_factory or LegacyAiChat
        self.switch = switch or AiHarnessSwitch(self.wiz)
        self.monitor = monitor or ChatStabilizationMonitor()
        self.reply_guard = ReplyGuard()
        self.legacy = None
        self._request_lock = threading.Lock()
        self._request_cache = {}

    def _executor(self):
        if self.switch.enabled():
            return "harness", self.agent
        if self.legacy is None:
            self.legacy = self.legacy_factory()
        return "legacy", self.legacy

    def send(self, prompt, history_raw="[]", user_id="", thread_id="", client_message_id="", state_raw="{}"):
        client_message_id = str(client_message_id or "").strip()[:96]
        request_id = uuid.uuid4().hex
        cache_key = f"{user_id or 'anonymous'}:{client_message_id}" if client_message_id else ""
        if cache_key:
            with self._request_lock:
                cached = self._request_cache.get(cache_key)
                if cached and cached.get("state") == "complete":
                    return int(cached["status"]), copy.deepcopy(cached["payload"])
                if cached and cached.get("state") == "in_flight":
                    return 409, {
                        "message": "같은 메시지를 이미 처리하고 있어요.",
                        "reply": "같은 메시지를 이미 처리하고 있어요.",
                        "stage": "collecting",
                        "action": "answer_only",
                        "request_id": cached.get("request_id", request_id),
                        "client_message_id": client_message_id,
                        "conversation_id": thread_id,
                    }
                self._request_cache[cache_key] = {"state": "in_flight", "request_id": request_id}
        executor_name, executor = self._executor()
        started = time.monotonic()
        try:
            if executor_name == "harness":
                status, payload = executor.send(
                    prompt, history_raw, user_id, thread_id, client_message_id, request_id, state_raw,
                )
            else:
                status, payload = executor.send(prompt, history_raw, user_id, thread_id)
        except Exception as error:
            status = 200
            payload = self._transient_recovery_payload(prompt, state_raw)
            payload["_fallback_reason"] = f"runtime_{type(error).__name__}_recovered"
            executor_name = f"{executor_name}_recovery"
        payload = dict(payload or {})
        fallback_reason = str(payload.pop("_fallback_reason", "") or self._infer_fallback_reason(status, payload))
        debug = payload.pop("_debug", {}) if isinstance(payload.get("_debug", {}), dict) else {}
        if self.reply_guard.requires_recovery(status, dict(payload, _fallback_reason=fallback_reason)):
            status, payload, debug, fallback_reason, executor_name = self._recover(
                prompt,
                history_raw,
                user_id,
                thread_id,
                payload,
                executor_name,
                fallback_reason,
                state_raw,
            )
        if executor_name == "legacy":
            payload = self._legacy_contract(payload)
        debug.update({
            "executor": executor_name,
            "model_name": debug.get("model_name") or payload.get("model", ""),
            "stage": debug.get("stage") or payload.get("stage", ""),
            "action": debug.get("action") or payload.get("action", ""),
            "fallback_reason": fallback_reason,
            "request_id": request_id,
            "client_message_id": client_message_id,
            "conversation_id": str(payload.get("thread_id") or thread_id or ""),
            "user_message_id": str(
                payload.get("user_message_id")
                or (f"user-{client_message_id}" if client_message_id else "")
            ),
            "response_message_id": str(payload.get("response_message_id") or f"assistant-{request_id}"),
        })
        travel_state = payload.get("travel_state") if isinstance(payload.get("travel_state"), dict) else {}
        companions = list(travel_state.get("companions") or [])
        debug.update({
            "travel_state": {
                "days": travel_state.get("days"),
                "companion": companions[0] if companions else "",
                "transport": str(travel_state.get("transport") or ""),
            },
            "days": travel_state.get("days"),
            "companion": companions[0] if companions else "",
            "transport": str(travel_state.get("transport") or ""),
        })
        self.monitor.record(
            executor_name,
            status,
            fallback_reason,
            int((time.monotonic() - started) * 1000),
            metadata=debug,
        )
        payload.setdefault("request_id", request_id)
        payload.setdefault("client_message_id", client_message_id)
        payload.setdefault("conversation_id", str(payload.get("thread_id") or thread_id or ""))
        payload.setdefault("user_message_id", f"user-{client_message_id}" if client_message_id else "")
        payload.setdefault("response_message_id", f"assistant-{request_id}")
        public_payload = self.reply_guard.public_payload(payload)
        if cache_key:
            with self._request_lock:
                self._request_cache[cache_key] = {
                    "state": "complete",
                    "request_id": request_id,
                    "status": status,
                    "payload": copy.deepcopy(public_payload),
                }
                if len(self._request_cache) > 500:
                    oldest_key = next(iter(self._request_cache))
                    if oldest_key != cache_key:
                        self._request_cache.pop(oldest_key, None)
        return status, public_payload

    def _transient_recovery_payload(self, prompt, state_raw):
        try:
            source = json.loads(state_raw) if isinstance(state_raw, str) else state_raw
            source = source if isinstance(source, dict) else {}
        except Exception:
            source = {}
        state_machine = getattr(self.agent, "state_machine", None)
        try:
            state = state_machine.normalize(source)
            extracted = state_machine.extract(prompt, state)
            state = state_machine.merge(state, extracted.get("changed_slots") or {})
        except Exception:
            state = dict(source)
        draft = state.get("itinerary_draft") if isinstance(state.get("itinerary_draft"), dict) else {}
        stage = "draft_ready" if draft.get("days") else "collecting"
        state["conversation_stage"] = stage
        message = (
            "기존 코스와 입력한 조건은 유지했어요. 같은 요청을 한 번 더 보내주세요."
            if draft.get("days")
            else "입력한 여행 조건은 유지했어요. 같은 요청을 한 번 더 보내주세요."
        )
        return {
            "message": message,
            "reply": message,
            "stage": stage,
            "travel_state": state,
            "itinerary_draft": draft,
            "missing_slots": [],
            "action": "answer_only",
            "warnings": [],
            "failure_stage": "",
        }

    def _recover(self, prompt, history_raw, user_id, thread_id, payload, executor_name, reason, state_raw="{}"):
        if executor_name == "legacy":
            try:
                status, recovered = self.agent.send(
                    prompt, history_raw, user_id, thread_id, "", "", state_raw,
                )
                recovered = dict(recovered or {})
                debug = recovered.pop("_debug", {}) if isinstance(recovered.get("_debug"), dict) else {}
                recovered.pop("_fallback_reason", None)
                if status == 200:
                    return 200, recovered, debug, f"{reason}_recovered", "harness_recovery"
            except Exception:
                pass
        return 200, self.reply_guard.recovery_payload(payload), {}, f"{reason}_recovered", executor_name

    def threads(self, user_id, limit=30):
        return self._executor()[1].threads(user_id, limit)

    def thread(self, user_id, thread_id):
        return self._executor()[1].thread(user_id, thread_id)

    def delete_thread(self, user_id, thread_id):
        return self._executor()[1].delete_thread(user_id, thread_id)

    def admin_settings(self):
        settings = self.agent.admin_settings()
        settings["harness_enabled"] = self.switch.enabled()
        settings["active_executor"] = "harness" if settings["harness_enabled"] else "legacy"
        return settings

    def _legacy_contract(self, payload):
        payload = dict(payload or {})
        message = str(payload.get("message") or payload.get("reply") or "")
        payload.setdefault("message", message)
        payload.setdefault("reply", message)
        payload.setdefault("stage", "collecting")
        payload.setdefault("travel_state", {})
        payload.setdefault("itinerary_draft", {})
        payload.setdefault("missing_slots", [])
        payload.setdefault("action", "answer_only")
        payload.setdefault("warnings", [])
        payload.setdefault("failure_stage", "")
        return payload

    def _infer_fallback_reason(self, status, payload):
        status = int(status or 0)
        if status == 200:
            return "none"
        if status == 400:
            return "invalid_input"
        if status == 503:
            return "model_disabled"
        if status == 500:
            return "missing_key_or_internal_error"
        if status == 502:
            return "unclassified_502"
        return "http_error"

    def update_admin_settings(self, data):
        data = data if isinstance(data, dict) else {}
        model_fields = set(data.keys()) - {"harness_enabled"}
        settings = self.agent.update_admin_settings(data) if model_fields else self.agent.admin_settings()
        if "harness_enabled" in data:
            self.switch.set_enabled(data.get("harness_enabled"))
        settings["harness_enabled"] = self.switch.enabled()
        settings["active_executor"] = "harness" if settings["harness_enabled"] else "legacy"
        return settings


Model = AiChatFacade()
