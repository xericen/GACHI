import time


TravelPlannerAgent = wiz.model("agents/travel_planner")
LegacyAiChat = wiz.model("ai_chat_legacy")
AiHarnessSwitch = wiz.model("ai_harness_switch")
ChatStabilizationMonitor = wiz.model("ai_chat_observability")


class AiChatFacade:
    def __init__(self, wiz_context=None, agent=None, legacy_factory=None, switch=None, monitor=None):
        self.wiz = wiz_context or wiz
        self.agent = agent or TravelPlannerAgent(self.wiz)
        self.legacy_factory = legacy_factory or LegacyAiChat
        self.switch = switch or AiHarnessSwitch(self.wiz)
        self.monitor = monitor or ChatStabilizationMonitor()
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
        self.monitor.record(
            executor_name,
            status,
            fallback_reason,
            int((time.monotonic() - started) * 1000),
        )
        return status, payload

    def threads(self, user_id, limit=30):
        return self._executor()[1].threads(user_id, limit)

    def thread(self, user_id, thread_id):
        return self._executor()[1].thread(user_id, thread_id)

    def admin_settings(self):
        settings = self.agent.admin_settings()
        settings["harness_enabled"] = self.switch.enabled()
        return settings

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
        return settings


Model = AiChatFacade()
