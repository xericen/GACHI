import json
import re

Types = wiz.model("ai_harness/types")
Harness = wiz.model("ai_harness/harness")
RetryPolicy = wiz.model("ai_harness/observability/retry")
StructuredLogger = wiz.model("ai_harness/observability/logging")
Gemini = wiz.model("ai_harness/providers/gemini")
ChatThreadStore = wiz.model("ai_harness/storage/chat_thread_store")
Settings = wiz.model("agents/travel_planner_settings")
TravelTools = wiz.model("agents/travel_planner_tools")
Validator = wiz.model("agents/travel_planner_validator")
SYSTEM_PROMPT = wiz.model("agents/travel_planner_prompt")


class TravelMessageBuilder:
    def build(self, normalized):
        lines = []
        if normalized.history:
            lines.append("최근 대화:")
            for item in normalized.history:
                role = "사용자" if item.role == "user" else "AI"
                lines.append(f"{role}: {item.content}")
            lines.append("")
        lines.append("현재 사용자 질문:")
        lines.append(normalized.prompt)
        return [Types.Message(role="user", content="\n".join(lines))]


class HistoryDecoder:
    def decode(self, raw):
        try:
            rows = json.loads(raw or "[]")
        except Exception:
            return []
        if not isinstance(rows, list):
            return []
        messages = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            role = str(row.get("role") or "").strip()
            if role not in ["user", "assistant"]:
                continue
            messages.append(Types.Message(role=role, content=str(row.get("text") or "")))
        return messages


class TravelPlannerAgent:
    def __init__(self, wiz_context):
        self.wiz = wiz_context
        self.settings = Settings(wiz_context)
        self.logger = StructuredLogger()
        self.history_decoder = HistoryDecoder()
        self.store = self._build_store()
        provider = Gemini.Provider(Gemini.Config(
            api_key=self.settings.api_key(),
            model=self.settings.model(),
            timeout=self.settings.timeout(),
            temperature=self.settings.temperature(),
            max_output_tokens=self.settings.max_output_tokens(),
        ))
        tools = TravelTools.build(self.wiz.model("ai_tools"))
        config = Types.HarnessConfig(
            system_prompt=SYSTEM_PROMPT,
            tools=tools,
            model_provider=provider,
            validators=[Validator()],
            max_tool_iterations=5,
            max_validation_retries=1,
            max_validation_tool_iterations=2,
            history_window=12,
            max_prompt_chars=2000,
            max_history_message_chars=900,
            message_builder=TravelMessageBuilder(),
        )
        self.harness = Harness(
            config=config,
            retry_policy=RetryPolicy(max_retries=2, base_delay=0.5, max_delay=2.0, jitter=0.15),
            logger=self.logger,
        )

    def send(self, prompt, history_raw="[]", user_id="", thread_id=""):
        if not str(prompt or "").strip():
            return 400, {"message": "질문을 입력해주세요."}
        if not self.settings.enabled():
            return 503, {"message": "AI 여행 모델이 관리자에 의해 중지되었습니다."}
        if not self.settings.api_key():
            return 500, {"message": "AI API 키가 설정되지 않았습니다."}
        try:
            result = self.harness.run(prompt, self.history_decoder.decode(history_raw))
        except Exception as error:
            code = str(getattr(error, "code", "") or "")
            if code == "invalid_input":
                return 400, {"message": "질문을 입력해주세요.", "_fallback_reason": code}
            if code in ["validation_failed", "tool_budget_exceeded"]:
                return 502, {"message": "AI 응답을 검증하지 못했습니다. 다시 질문해주세요.", "_fallback_reason": code}
            if code == "provider_error":
                status = int(getattr(error, "status_code", 502) or 502)
                status = status if status < 500 else 502
                return status, {
                    "message": str(getattr(error, "message", "") or "Gemini API 호출에 실패했습니다."),
                    "_fallback_reason": code,
                }
            return 502, {
                "message": "AI 응답을 가져오지 못했습니다. 잠시 후 다시 시도해주세요.",
                "_fallback_reason": code or "unexpected_error",
            }

        if not result.reply:
            return 502, {"message": "AI 응답이 비어 있습니다. 다시 질문해주세요.", "_fallback_reason": "empty_response"}
        payload = {
            "reply": result.reply,
            "model": result.model or self.settings.model(),
            "interaction_id": result.interaction_id,
            "tool_logs": [item.to_legacy() for item in result.tool_logs],
        }
        proposal = self._extract_itinerary_proposal(result.reply)
        if proposal:
            payload["itinerary_proposal"] = proposal
        if user_id:
            stored = self.store.append_turn(
                thread_id,
                user_id,
                result.normalized_input.prompt,
                result.reply,
                result.normalized_input.history,
            )
            if stored:
                payload.update({"thread_id": stored.thread_id, "title": stored.title})
                self.logger.emit(
                    "conversation_stored",
                    run_id=result.metadata.get("run_id", ""),
                    thread_id=stored.thread_id,
                    is_new=stored.is_new,
                )
        return 200, payload

    def threads(self, user_id, limit=30):
        return self.store.list(user_id, limit)

    def thread(self, user_id, thread_id):
        return self.store.get(thread_id, user_id)

    def admin_settings(self):
        return self.settings.admin_view()

    def update_admin_settings(self, data):
        return self.settings.update(data)

    def _build_store(self):
        db = self.wiz.model("portal/season/orm").use("chat_thread")
        try:
            db.orm.create_table(safe=True)
        except Exception:
            pass
        return ChatThreadStore(db)

    def _extract_itinerary_proposal(self, reply):
        if not reply:
            return None
        candidates = []
        stripped = reply.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            candidates.append(stripped)
        candidates.extend(re.findall(r"```json\s*(\{.*?\})\s*```", reply, flags=re.S))
        for raw in candidates:
            try:
                data = json.loads(raw)
            except Exception:
                continue
            if isinstance(data, dict) and data.get("itinerary_proposal"):
                return data.get("itinerary_proposal")
        return None


Model = TravelPlannerAgent
