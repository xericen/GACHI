import copy
import json
import time


Types = wiz.model("ai_harness/types")
Harness = wiz.model("ai_harness/harness")
RetryPolicy = wiz.model("ai_harness/observability/retry")
StructuredLogger = wiz.model("ai_harness/observability/logging")
Gemini = wiz.model("ai_harness/providers/gemini")
ChatThreadStore = wiz.model("ai_harness/storage/chat_thread_store")
Settings = wiz.model("agents/travel_planner_settings")
StateMachine = wiz.model("agents/travel_planner_state")
ItineraryEngine = wiz.model("agents/travel_itinerary_engine")
ReplyGuard = wiz.model("agents/travel_reply_guard")
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
    PROGRESS_STEPS = ["여행 조건 정리 중", "장소 검색 중", "동선 계산 중", "일정 구성 중"]

    def __init__(self, wiz_context):
        self.wiz = wiz_context
        self.settings = Settings(wiz_context)
        self.logger = StructuredLogger()
        self.history_decoder = HistoryDecoder()
        self.state_machine = StateMachine()
        self.reply_guard = ReplyGuard()
        self.response_parser = self._response_parser()
        self.store = self._build_store()
        self.ai_tools = self.wiz.model("ai_tools")
        self.itinerary_engine = ItineraryEngine(self.ai_tools)
        provider = Gemini.Provider(Gemini.Config(
            api_key=self.settings.api_key(),
            model=self.settings.model(),
            timeout=self.settings.timeout(),
            temperature=self.settings.temperature(),
            max_output_tokens=self.settings.max_output_tokens(),
        ))
        config = Types.HarnessConfig(
            system_prompt=SYSTEM_PROMPT,
            tools=[],
            model_provider=provider,
            validators=[],
            max_tool_iterations=0,
            max_validation_retries=0,
            max_validation_tool_iterations=0,
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
        started = time.monotonic()
        prompt = str(prompt or "").strip()
        if not prompt:
            return 400, self._error_payload("질문을 입력해주세요.", "collecting", "travel_conditions", "invalid_input")

        history = self.history_decoder.decode(history_raw)
        state = self._load_state(user_id, thread_id, history)
        deterministic = self.state_machine.extract(prompt, state)
        structured, model_name, interaction_id, fallback_reason = self._extract_with_model(prompt, history)
        changed = self._safe_changed_slots(structured.get("extracted_slots"))
        changed.update(self._safe_changed_slots(structured.get("changed_slots")))
        changed.update(deterministic.get("changed_slots") or {})
        state = self.state_machine.merge(state, changed)

        intent = deterministic.get("user_intent") or "provide_information"
        model_intent = str(structured.get("user_intent") or "provide_information")
        if intent == "provide_information" and model_intent == "general_question":
            intent = model_intent
        elif intent == "provide_information" and state.get("itinerary_draft") and model_intent in [
            "revise_course", "replace_place", "remove_place", "add_place", "change_schedule",
        ]:
            intent = model_intent
        action = self.state_machine.action_for(intent)
        warnings = []
        tool_logs = []
        failure_stage = ""
        message = str(structured.get("assistant_message") or "").strip()
        missing = self.state_machine.missing_slots(state)

        if intent == "generate_course":
            state = self.state_machine.apply_generation_defaults(state)
            missing = self.state_machine.missing_slots(state)
            if missing:
                state["conversation_stage"] = "collecting"
                action = "ask_clarification"
                message = self.state_machine.next_question(missing)
                failure_stage = "travel_conditions"
            else:
                state["conversation_stage"] = "generating"
                generated = self.itinerary_engine.generate(state)
                tool_logs = generated.get("tool_logs") or []
                warnings.extend(generated.get("warnings") or [])
                if generated.get("ok"):
                    draft = generated.get("draft") or {}
                    state["itinerary_draft"] = draft
                    state["collected_place_ids"] = self._draft_place_ids(draft)
                    state["conversation_stage"] = "draft_ready"
                    action = "generate_itinerary"
                    message = "여행 조건과 실제 장소 이동시간을 반영해 코스 초안을 만들었어요. 날짜별 일정을 확인하고 원하는 부분을 말해주세요."
                else:
                    state["conversation_stage"] = "error"
                    action = "generate_itinerary"
                    failure_stage = generated.get("failure_stage") or "place_search"
                    message = generated.get("message") or "조건에 맞는 장소를 충분히 찾지 못했어요."
        elif intent in ["revise_course", "replace_place", "remove_place", "add_place", "change_schedule"]:
            action = "revise_itinerary"
            if not state.get("itinerary_draft"):
                state["conversation_stage"] = "collecting"
                missing = self.state_machine.missing_slots(state)
                message = self.state_machine.next_question(missing) if missing else "먼저 이 조건으로 코스를 만든 뒤 수정할 수 있어요."
                failure_stage = "travel_conditions"
            else:
                state = self.state_machine.apply_generation_defaults(state)
                state["conversation_stage"] = "revising"
                revised = self.itinerary_engine.revise(state, prompt, intent)
                tool_logs = revised.get("tool_logs") or []
                warnings.extend(revised.get("warnings") or [])
                if revised.get("ok"):
                    draft = revised.get("draft") or {}
                    state["itinerary_draft"] = draft
                    state["collected_place_ids"] = self._draft_place_ids(draft)
                    state["conversation_stage"] = "draft_ready"
                    message = "기존 코스에서 요청한 부분만 수정하고 이동시간을 다시 계산했어요."
                else:
                    state["conversation_stage"] = "draft_ready"
                    failure_stage = revised.get("failure_stage") or "revision_target"
                    message = revised.get("message") or "수정할 대상을 확인하지 못했어요."
        else:
            missing = self.state_machine.missing_slots(state)
            if missing:
                state["conversation_stage"] = "collecting"
                action = "ask_clarification" if intent != "general_question" else "answer_only"
                if intent != "general_question" or not message:
                    message = self.state_machine.next_question(missing)
            else:
                state = self.state_machine.apply_generation_defaults(state)
                state["conversation_stage"] = "ready_to_generate" if not state.get("itinerary_draft") else "draft_ready"
                action = "answer_only" if intent == "general_question" else "ask_clarification"
                if not message:
                    message = "여행 조건이 준비됐어요. 이 조건으로 코스를 만들어볼까요?"

        if intent == "general_question" and fallback_reason in ["missing_api_key", "model_disabled", "provider_error", "model_error"]:
            state["conversation_stage"] = "error"
            failure_stage = "model_config"
            message = "현재 AI 모델 연결을 확인하고 있어요. 잠시 후 다시 질문해주세요."

        missing = self.state_machine.missing_slots(state)
        message = self.reply_guard.sanitize(
            message,
            state.get("conversation_stage") or "collecting",
            missing,
            failure_stage,
        )
        payload = {
            "message": message,
            "reply": message,
            "thread_id": thread_id,
            "stage": state.get("conversation_stage") or "collecting",
            "travel_state": copy.deepcopy(state),
            "itinerary_draft": copy.deepcopy(state.get("itinerary_draft") or {}),
            "missing_slots": missing,
            "action": action,
            "warnings": self._unique(warnings),
            "failure_stage": failure_stage,
            "progress_steps": list(self.PROGRESS_STEPS),
            "model": model_name or self.settings.model(),
            "interaction_id": interaction_id,
            "tool_logs": [item.to_legacy() for item in tool_logs],
        }

        if user_id:
            stored = self.store.append_turn(
                thread_id,
                user_id,
                prompt,
                message,
                history,
                travel_state=state,
            )
            if stored:
                payload.update({"thread_id": stored.thread_id, "title": stored.title})
                self.logger.emit(
                    "conversation_stored",
                    run_id="",
                    thread_id=stored.thread_id,
                    is_new=stored.is_new,
                    stage=payload["stage"],
                )

        payload["_fallback_reason"] = fallback_reason or "none"
        payload["_debug"] = {
            "executor": "harness",
            "model_name": payload["model"],
            "stage": payload["stage"],
            "action": action,
            "tool_calls": [log.call.name for log in tool_logs],
            "fallback_reason": fallback_reason or "none",
            "elapsed_ms": self._ms(started),
        }
        return 200, payload

    def threads(self, user_id, limit=30):
        return self.store.list(user_id, limit)

    def thread(self, user_id, thread_id):
        return self.store.get(thread_id, user_id)

    def admin_settings(self):
        return self.settings.admin_view()

    def update_admin_settings(self, data):
        return self.settings.update(data)

    def _extract_with_model(self, prompt, history):
        if not self.settings.enabled():
            return self._empty_structured(), self.settings.model(), "", "model_disabled"
        if not self.settings.api_key():
            return self._empty_structured(), self.settings.model(), "", "missing_api_key"
        try:
            result = self.harness.run(prompt, history)
            structured, recovered = self.response_parser.parse(result.reply)
            reason = "json_parse_recovered" if recovered else "none"
            return structured, result.model, result.interaction_id, reason
        except Exception as error:
            code = str(getattr(error, "code", "") or "model_error")
            return self._empty_structured(), self.settings.model(), "", code

    def _load_state(self, user_id, thread_id, history):
        if user_id and thread_id:
            stored = self.store.get_state(thread_id, user_id)
            if stored:
                return self.state_machine.normalize(stored)
        state = self.state_machine.normalize({})
        for message in history:
            if message.role != "user":
                continue
            extracted = self.state_machine.extract(message.content, state)
            state = self.state_machine.merge(state, extracted.get("changed_slots"))
        return state

    def _safe_changed_slots(self, values):
        if not isinstance(values, dict):
            return {}
        allowed = {
            "region", "start_date", "end_date", "days", "arrival_time", "departure_time",
            "companions", "transport", "budget", "preferences", "excluded_preferences",
            "must_visit_places", "accommodation_area",
        }
        return {key: value for key, value in values.items() if key in allowed}

    def _draft_place_ids(self, draft):
        rows = []
        for day in draft.get("days", []) if isinstance(draft, dict) else []:
            for place in day.get("places", []) or []:
                place_id = str(place.get("place_id") or "").strip()
                if place_id and place_id not in rows:
                    rows.append(place_id)
        return rows

    def _build_store(self):
        db = self.wiz.model("portal/season/orm").use("chat_thread")
        try:
            db.orm.create_table(safe=True)
            model = db.orm
            database = model._meta.database
            columns = [column.name for column in database.get_columns(model._meta.table_name)]
            if "travel_state" not in columns:
                database.execute_sql("ALTER TABLE `chat_thread` ADD COLUMN `travel_state` LONGTEXT NULL")
        except Exception:
            pass
        return ChatThreadStore(db)

    def _response_parser(self):
        # WIZ model loading exposes only Model, so keep parsing local to this executor.
        return _InlineStructuredParser()

    def _empty_structured(self):
        return {
            "extracted_slots": {},
            "changed_slots": {},
            "missing_slots": [],
            "user_intent": "provide_information",
            "action": "answer_only",
            "assistant_message": "",
        }

    def _error_payload(self, message, stage, failure_stage, fallback_reason):
        return {
            "message": message,
            "reply": message,
            "stage": stage,
            "travel_state": self.state_machine.normalize({}),
            "itinerary_draft": {},
            "missing_slots": ["region", "days", "preferences"],
            "action": "ask_clarification",
            "warnings": [],
            "failure_stage": failure_stage,
            "_fallback_reason": fallback_reason,
        }

    def _unique(self, values):
        rows = []
        for value in values or []:
            value = str(value or "").strip()
            if value and value not in rows:
                rows.append(value)
        return rows

    def _ms(self, started):
        return max(0, int((time.monotonic() - started) * 1000))


class _InlineStructuredParser:
    def parse(self, raw):
        text = str(raw or "").strip()
        candidates = [text]
        if "```" in text:
            candidates.extend(part.strip() for part in text.split("```") if "{" in part)
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            candidates.append(text[start:end + 1])
        for candidate in candidates:
            candidate = candidate.strip()
            if candidate.lower().startswith("json"):
                candidate = candidate[4:].strip()
            try:
                data = json.loads(candidate)
            except Exception:
                continue
            if isinstance(data, dict):
                return {
                    "extracted_slots": data.get("extracted_slots") if isinstance(data.get("extracted_slots"), dict) else {},
                    "changed_slots": data.get("changed_slots") if isinstance(data.get("changed_slots"), dict) else {},
                    "missing_slots": data.get("missing_slots") if isinstance(data.get("missing_slots"), list) else [],
                    "user_intent": str(data.get("user_intent") or "provide_information"),
                    "action": str(data.get("action") or "answer_only"),
                    "assistant_message": str(data.get("assistant_message") or "").strip(),
                }, False
        return {
            "extracted_slots": {}, "changed_slots": {}, "missing_slots": [],
            "user_intent": "provide_information", "action": "answer_only", "assistant_message": "",
        }, True


Model = TravelPlannerAgent
