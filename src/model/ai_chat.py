import time


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

    def _executor(self):
        if self.switch.enabled():
            return "harness", self.agent
        if self.legacy is None:
            self.legacy = self.legacy_factory()
        return "legacy", self.legacy

    def send(self, prompt, history_raw="[]", user_id="", thread_id=""):
        executor_name, executor = self._executor()
        started = time.monotonic()
        try:
            status, payload = executor.send(prompt, history_raw, user_id, thread_id)
        except Exception:
            self.monitor.record(
                executor_name,
                500,
                "unhandled_exception",
                int((time.monotonic() - started) * 1000),
            )
            raise
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
            )
        if executor_name == "legacy":
            payload = self._legacy_contract(payload)
        debug.update({
            "executor": executor_name,
            "model_name": debug.get("model_name") or payload.get("model", ""),
            "stage": debug.get("stage") or payload.get("stage", ""),
            "action": debug.get("action") or payload.get("action", ""),
            "fallback_reason": fallback_reason,
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
        return status, self.reply_guard.public_payload(payload)

    def _recover(self, prompt, history_raw, user_id, thread_id, payload, executor_name, reason):
        if executor_name == "legacy":
            try:
                status, recovered = self.agent.send(prompt, history_raw, user_id, thread_id)
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
