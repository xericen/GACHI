import copy
import json
import re
import time
import uuid


Types = wiz.model("ai_harness/types")
Harness = wiz.model("ai_harness/harness")
RetryPolicy = wiz.model("ai_harness/observability/retry")
StructuredLogger = wiz.model("ai_harness/observability/logging")
Gemini = wiz.model("ai_harness/providers/gemini")
ChatThreadStore = wiz.model("ai_harness/storage/chat_thread_store")
Settings = wiz.model("agents/travel_planner_settings")
StateMachine = wiz.model("agents/travel_planner_state")
ItineraryEngine = wiz.model("agents/travel_itinerary_engine")
RouteObservability = wiz.model("travel_route_observability")
ReplyGuard = wiz.model("agents/travel_reply_guard")
SYSTEM_PROMPT = wiz.model("agents/travel_planner_prompt")

MODEL_INTENTS = {
    "provide_information", "generate_course", "revise_course", "replace_place",
    "remove_place", "add_place", "change_schedule", "general_question",
    "destination_recommendation", "select_destination",
}
MODEL_CONTEXT_SCHEMA_VERSION = 1
MODEL_CONTEXT_JSON_BUDGET = 5200
MODEL_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["changed_slots", "user_intent", "assistant_message"],
    "properties": {
        "changed_slots": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "region": {"type": "string"},
                "destination": {"type": "string"},
                "origin": {"type": "string"},
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "days": {"type": "integer", "minimum": 1, "maximum": 14},
                "arrival_time": {"type": "string"},
                "departure_time": {"type": "string"},
                "companions": {"type": "array", "items": {"type": "string"}},
                "transport": {"type": "string"},
                "budget": {"type": "string"},
                "preferences": {"type": "array", "items": {"type": "string"}},
                "excluded_preferences": {"type": "array", "items": {"type": "string"}},
                "must_visit_places": {"type": "array", "items": {"type": "string"}},
                "start_location": {"type": "string"},
                "accommodation_area": {"type": "string"},
                "schedule_pace": {"type": "string"},
                "walking_tolerance": {"type": "string"},
                "rest_preference": {"type": "string"},
            },
        },
        "user_intent": {"type": "string", "enum": sorted(MODEL_INTENTS)},
        "assistant_message": {"type": "string"},
    },
}


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
        self.route_observability = RouteObservability(wiz_context)
        provider = Gemini.Provider(Gemini.Config(
            api_key=self.settings.api_key(),
            model=self.settings.model(),
            timeout=self.settings.timeout(),
            temperature=self.settings.temperature(),
            max_output_tokens=self.settings.max_output_tokens(),
            response_schema=MODEL_RESPONSE_SCHEMA,
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
            max_prompt_chars=8000,
            max_history_message_chars=900,
            message_builder=TravelMessageBuilder(),
        )
        self.harness = Harness(
            config=config,
            retry_policy=RetryPolicy(max_retries=2, base_delay=0.5, max_delay=2.0, jitter=0.15),
            logger=self.logger,
        )

    def send(
        self, prompt, history_raw="[]", user_id="", thread_id="", client_message_id="",
        request_id="", state_raw="{}",
    ):
        started = time.monotonic()
        prompt = str(prompt or "").strip()
        client_message_id = str(client_message_id or "").strip()[:96]
        request_id = str(request_id or uuid.uuid4().hex)
        user_message_id = f"user-{client_message_id}" if client_message_id else f"user-{uuid.uuid4().hex}"
        response_message_id = f"assistant-{request_id}"
        if not prompt:
            return 400, self._error_payload("질문을 입력해주세요.", "collecting", "travel_conditions", "invalid_input")

        history = self.history_decoder.decode(history_raw)
        state = self._load_state(user_id, thread_id, history, state_raw)
        expected_state_version = int(state.get("state_version") or 0)
        condition_command = self._condition_edit_command(prompt, state)
        generation_confirmation = self._is_generation_confirmation(prompt, state)
        if condition_command and condition_command != "menu":
            state = self._clear_condition(state, condition_command)
        deterministic = self.state_machine.extract(prompt, state)
        structured, model_name, interaction_id, fallback_reason, context_meta = self._extract_with_model(prompt, history, state)
        changed = self._safe_changed_slots(structured.get("changed_slots"))
        changed.update(deterministic.get("changed_slots") or {})
        state = self.state_machine.merge(state, changed)

        recovery_strategy = self._recovery_strategy(prompt, state)
        if recovery_strategy:
            state["recovery_strategy"] = recovery_strategy
            if recovery_strategy == "fewer_places":
                state["schedule_pace"] = "여유롭게"
            elif recovery_strategy == "relax_preferences":
                state["preferences"] = self._unique(
                    list(state.get("preferences") or []) + ["자연", "맛집", "카페", "문화"]
                )
            generation_confirmation = True

        intent = deterministic.get("user_intent") or "provide_information"
        if condition_command:
            intent = "provide_information"
        elif recovery_strategy:
            intent = "generate_course"
        elif generation_confirmation and state.get("conversation_stage") == "ready_to_generate":
            intent = "generate_course"
        model_intent = str(structured.get("user_intent") or "provide_information")
        if intent == "provide_information" and model_intent == "general_question" and not changed:
            intent = model_intent
        elif intent == "provide_information" and model_intent == "generate_course" and self._model_generation_allowed(prompt, state):
            intent = model_intent
        elif intent == "provide_information" and state.get("itinerary_draft") and model_intent in [
            "revise_course", "replace_place", "remove_place", "add_place", "change_schedule",
        ]:
            intent = model_intent
        if intent == "destination_recommendation":
            state["intent"] = "destination_recommendation"
            state["generation_requested"] = False
        elif state.get("intent") == "destination_recommendation" and intent in ["provide_information", "general_question"]:
            intent = "destination_recommendation"
        if intent == "select_destination":
            state["intent"] = "itinerary_generation"
            state["conversation_stage"] = "destination_selected"
            state["pending_slot"] = ""
            state["generation_requested"] = True
            intent = "generate_course"
        if intent == "generate_course":
            state["generation_requested"] = True
        elif intent == "provide_information" and state.get("generation_requested"):
            ready_state = self.state_machine.apply_generation_defaults(state)
            if not self.state_machine.missing_slots(ready_state):
                state = ready_state
                intent = "generate_course"
        action = self.state_machine.action_for(intent)
        warnings = []
        tool_logs = []
        generation_metadata = {}
        failure_stage = ""
        failure_reason = {}
        message = str(structured.get("assistant_message") or "").strip()
        missing = self.state_machine.missing_slots(state)
        destination_candidates = []

        if condition_command == "menu":
            state["conversation_stage"] = "editing_conditions"
            state["generation_requested"] = False
            state["conditions_confirmed"] = False
            state["pending_slot"] = "condition_to_edit"
            state["feasibility_status"] = "conditions_complete"
            action = "ask_clarification"
            message = "어떤 여행 조건을 수정할까요? 한 가지를 선택해주세요."
        elif condition_command:
            state["conversation_stage"] = "collecting"
            state["generation_requested"] = False
            state["conditions_confirmed"] = False
            state["pending_slot"] = condition_command
            state["feasibility_status"] = "conditions_incomplete"
            action = "ask_clarification"
            message = self.state_machine.next_question(
                [condition_command], [], False, state=state,
            )
        elif intent == "destination_recommendation":
            state["intent"] = "destination_recommendation"
            missing = self.state_machine.destination_missing_slots(state)
            if missing:
                state["conversation_stage"] = "collecting_destination_preferences"
                slot, question = self.state_machine.destination_next_question(state, meaningful_answer=bool(changed))
                state["pending_slot"] = slot
                asked = list(state.get("asked_slots") or [])
                if slot and slot not in asked:
                    asked.append(slot)
                state["asked_slots"] = asked
                action = "ask_clarification"
                message = question
            else:
                destination_candidates = self._recommend_destinations(state)
                state["destination_candidates"] = copy.deepcopy(destination_candidates)
                state["conversation_stage"] = "destination_candidates_ready"
                state["pending_slot"] = ""
                state["asked_slots"] = []
                action = "recommend_destinations"
                days = int(state.get("days") or 1)
                duration = "당일" if days == 1 else f"{days - 1}박 {days}일"
                message = f"{state.get('origin')}에서 {state.get('transport')}으로 다녀오기 좋은 {duration} 여행지예요. 마음에 드는 지역을 선택해주세요."
        elif intent == "generate_course":
            state = self.state_machine.apply_generation_defaults(state)
            missing = self.state_machine.missing_slots(state)
            if missing:
                state["conversation_stage"] = "collecting"
                state["conditions_confirmed"] = False
                state["feasibility_status"] = "conditions_incomplete"
                action = "ask_clarification"
                message = self._clarification(state, missing, changed)
                failure_stage = "travel_conditions"
            elif not generation_confirmation:
                state["conversation_stage"] = "ready_to_generate"
                state["conditions_confirmed"] = False
                state["feasibility_status"] = "conditions_complete"
                state["pending_slot"] = ""
                action = "answer_only"
                message = (
                    "입력 조건을 정리했어요. 아직 실제 장소와 이동 동선은 확인 전이에요. "
                    "조건을 확인한 뒤 코스 만들기를 눌러주세요."
                )
            else:
                state["conversation_stage"] = "checking_feasibility"
                state["conditions_confirmed"] = True
                state["feasibility_status"] = "checking"
                generated = self.itinerary_engine.generate(state)
                route_health = self.route_observability.record(
                    generated, state, request_id=request_id, operation="generate",
                )
                tool_logs = generated.get("tool_logs") or []
                generation_metadata = copy.deepcopy(generated.get("metadata") or {})
                generation_metadata["route_health"] = route_health
                warnings.extend(generated.get("warnings") or [])
                if generated.get("ok"):
                    draft = generated.get("draft") or {}
                    state["itinerary_draft"] = draft
                    state["collected_place_ids"] = self._draft_place_ids(draft)
                    state["conversation_stage"] = "draft_ready"
                    state["feasibility_status"] = "available"
                    state["generation_requested"] = False
                    state["asked_slots"] = []
                    state["pending_slot"] = ""
                    action = "generate_itinerary"
                    message = "여행 조건과 실제 장소 이동시간을 반영해 코스 초안을 만들었어요. 날짜별 일정을 확인하고 원하는 부분을 말해주세요."
                else:
                    state["conversation_stage"] = "error"
                    state["generation_requested"] = False
                    state["conditions_confirmed"] = True
                    state["feasibility_status"] = "unavailable"
                    state["pending_slot"] = "recovery_action"
                    action = "ask_clarification"
                    failure_stage = generated.get("failure_stage") or "place_search"
                    failure_reason = copy.deepcopy(generated.get("failure_reason") or {})
                    message = generated.get("message") or (
                        "입력한 조건으로 실제 장소와 이동 동선을 끝까지 검증하지 못했어요."
                    )
        elif intent in ["revise_course", "replace_place", "remove_place", "add_place", "change_schedule"]:
            action = "revise_itinerary"
            if not state.get("itinerary_draft"):
                state["conversation_stage"] = "collecting"
                missing = self.state_machine.missing_slots(state)
                message = self._clarification(state, missing, changed) if missing else "먼저 이 조건으로 코스를 만든 뒤 수정할 수 있어요."
                failure_stage = "travel_conditions"
            else:
                state = self.state_machine.apply_generation_defaults(state)
                state["conversation_stage"] = "revising"
                revised = self.itinerary_engine.revise(state, prompt, intent)
                route_health = self.route_observability.record(
                    revised, state, request_id=request_id, operation="revise",
                )
                tool_logs = revised.get("tool_logs") or []
                generation_metadata = copy.deepcopy(revised.get("metadata") or {})
                generation_metadata["route_health"] = route_health
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
                state["feasibility_status"] = "conditions_incomplete"
                action = "ask_clarification" if intent != "general_question" else "answer_only"
                if intent != "general_question" or not message:
                    message = self._clarification(state, missing, changed)
            else:
                state = self.state_machine.apply_generation_defaults(state)
                state["conversation_stage"] = "ready_to_generate" if not state.get("itinerary_draft") else "draft_ready"
                state["feasibility_status"] = "conditions_complete" if not state.get("itinerary_draft") else "available"
                action = "answer_only"
                if intent != "general_question":
                    message = (
                        "요청한 조건을 반영했어요."
                        if state.get("itinerary_draft")
                        else "입력 조건을 정리했어요. 실제 장소와 이동 동선은 코스 만들기를 누른 뒤 확인해요."
                    )
                elif not message:
                    message = "입력 조건을 정리했어요. 실제 장소와 이동 동선은 아직 확인 전이에요."

        if intent == "general_question" and fallback_reason in ["missing_api_key", "model_disabled", "provider_error", "model_error"]:
            state["conversation_stage"] = "error"
            failure_stage = "model_config"
            message = "현재 AI 모델 연결을 확인하고 있어요. 잠시 후 다시 질문해주세요."

        missing = (
            self.state_machine.destination_missing_slots(state)
            if state.get("intent") == "destination_recommendation"
            and state.get("conversation_stage") != "destination_selected"
            else self.state_machine.missing_slots(state)
        )
        message = self.reply_guard.sanitize(
            message,
            state.get("conversation_stage") or "collecting",
            missing,
            failure_stage,
        )
        suggested_replies = self._suggested_replies(state, failure_stage)
        state["state_version"] = expected_state_version + 1
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
            "failure_reason": failure_reason,
            "metadata": generation_metadata,
            "progress_steps": list(self.PROGRESS_STEPS),
            "model": model_name or self.settings.model(),
            "interaction_id": interaction_id,
            "tool_logs": [item.to_legacy() for item in tool_logs],
            "destination_candidates": copy.deepcopy(destination_candidates or state.get("destination_candidates") or []),
            "suggested_replies": suggested_replies,
            "request_id": request_id,
            "client_message_id": client_message_id,
            "conversation_id": thread_id,
            "user_message_id": user_message_id,
            "response_message_id": response_message_id,
        }

        if user_id:
            stored = self.store.append_turn(
                thread_id,
                user_id,
                prompt,
                message,
                history,
                travel_state=state,
                user_message_id=user_message_id,
                response_message_id=response_message_id,
                client_message_id=client_message_id,
                request_id=request_id,
                expected_state_version=expected_state_version,
            )
            if stored:
                if stored.conflict:
                    latest_state = self.state_machine.normalize(stored.current_state)
                    conflict_message = "다른 요청이 먼저 반영되어 최신 여행 조건을 유지했어요. 방금 요청을 다시 보내주세요."
                    payload.update({
                        "message": conflict_message,
                        "reply": conflict_message,
                        "thread_id": stored.thread_id,
                        "title": stored.title,
                        "conversation_id": stored.thread_id,
                        "stage": latest_state.get("conversation_stage") or "collecting",
                        "travel_state": copy.deepcopy(latest_state),
                        "itinerary_draft": copy.deepcopy(latest_state.get("itinerary_draft") or {}),
                        "missing_slots": self.state_machine.missing_slots(latest_state),
                        "action": "answer_only",
                        "failure_stage": "",
                        "failure_reason": {},
                        "tool_logs": [],
                        "destination_candidates": copy.deepcopy(latest_state.get("destination_candidates") or []),
                        "suggested_replies": self._suggested_replies(latest_state, ""),
                    })
                    state = latest_state
                    action = "answer_only"
                    fallback_reason = "state_conflict_recovered"
                else:
                    payload.update({"thread_id": stored.thread_id, "title": stored.title})
                    payload["conversation_id"] = stored.thread_id
                self.logger.emit(
                    "conversation_stored",
                    run_id="",
                    thread_id=stored.thread_id,
                    is_new=stored.is_new,
                    stage=payload["stage"],
                    state_version=state.get("state_version", 0),
                    conflict=bool(stored.conflict),
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
            "context_schema_version": context_meta.get("schema_version", MODEL_CONTEXT_SCHEMA_VERSION),
            "context_chars": context_meta.get("chars", 0),
            "context_truncated": bool(context_meta.get("truncated")),
        }
        return 200, payload

    def threads(self, user_id, limit=30):
        return self.store.list(user_id, limit)

    def thread(self, user_id, thread_id):
        return self.store.get(thread_id, user_id)

    def delete_thread(self, user_id, thread_id):
        return self.store.delete(thread_id, user_id)

    def admin_settings(self):
        return self.settings.admin_view()

    def update_admin_settings(self, data):
        return self.settings.update(data)

    def _extract_with_model(self, prompt, history, state):
        model_prompt, context_meta = self._model_prompt(prompt, state)
        if not self.settings.enabled():
            return self._empty_structured(), self.settings.model(), "", "model_disabled", context_meta
        if not self.settings.api_key():
            return self._empty_structured(), self.settings.model(), "", "missing_api_key", context_meta
        try:
            result = self.harness.run(model_prompt, history)
            structured, recovered = self.response_parser.parse(result.reply)
            reason = "json_parse_recovered" if recovered else "none"
            return structured, result.model, result.interaction_id, reason, context_meta
        except Exception as error:
            code = str(getattr(error, "code", "") or "model_error")
            return self._empty_structured(), self.settings.model(), "", code, context_meta

    def _load_state(self, user_id, thread_id, history, state_raw="{}"):
        if user_id and thread_id:
            stored = self.store.get_state(thread_id, user_id)
            if stored:
                return self.state_machine.normalize(stored)
        state = self.state_machine.normalize(self._decode_client_state(state_raw))
        for message in history:
            if message.role != "user":
                continue
            extracted = self.state_machine.extract(message.content, state)
            state = self.state_machine.merge(state, extracted.get("changed_slots"))
            if extracted.get("user_intent") == "generate_course":
                state["generation_requested"] = True
                state = self.state_machine.apply_generation_defaults(state)
            elif extracted.get("user_intent") == "destination_recommendation" or state.get("intent") == "destination_recommendation":
                state["intent"] = "destination_recommendation"
                missing = self.state_machine.destination_missing_slots(state)
                state["pending_slot"] = missing[0] if missing else ""
        return state

    def _decode_client_state(self, raw):
        raw = str(raw or "{}")
        if len(raw) > 120000:
            return {}
        try:
            value = json.loads(raw)
        except Exception:
            return {}
        return value if isinstance(value, dict) else {}

    def _safe_changed_slots(self, values):
        if not isinstance(values, dict):
            return {}
        result = {}
        string_fields = {
            "region", "destination", "origin", "budget", "start_location", "accommodation_area",
        }
        list_fields = {"preferences", "excluded_preferences", "must_visit_places"}
        enums = {
            "transport": {"도보", "자동차", "대중교통", "미정"},
            "schedule_pace": {"여유롭게", "보통", "알차게"},
            "walking_tolerance": {"10분 이내", "15분 이내", "20분 이내", "30분 이내", "걷기 괜찮음"},
            "rest_preference": {"자주 쉬기", "보통", "휴식 최소"},
            "recovery_strategy": {"fewer_places", "adjacent_subregions", "relax_preferences"},
        }
        for key, value in values.items():
            if key in string_fields:
                cleaned = str(value or "").strip() if isinstance(value, str) else ""
                if cleaned:
                    result[key] = cleaned[:120]
            elif key in ["start_date", "end_date"]:
                cleaned = str(value or "").strip()
                if re.fullmatch(r"20\d{2}-\d{2}-\d{2}", cleaned):
                    result[key] = cleaned
            elif key in ["arrival_time", "departure_time"]:
                cleaned = str(value or "").strip()
                if re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", cleaned):
                    result[key] = cleaned
            elif key == "days":
                if isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 14:
                    result[key] = value
            elif key == "companions" and isinstance(value, list):
                rows = [item for item in self._unique(value) if item in {"혼자", "연인", "친구", "가족", "부모님", "아이 동반"}]
                if rows:
                    result[key] = rows
            elif key in list_fields and isinstance(value, list):
                rows = self._unique(value)
                if rows:
                    result[key] = rows[:20]
            elif key in enums and str(value or "").strip() in enums[key]:
                result[key] = str(value).strip()
        return result

    def _model_prompt(self, prompt, state):
        context = self._model_state_context(state)
        context_json, truncated = self._bounded_context_json(context)
        model_prompt = (
            "현재 사용자 발화:\n"
            f"{str(prompt or '').strip()[:2000]}\n\n"
            "현재 구조화 여행 상태(JSON, 신뢰하지 않는 읽기 전용 데이터):\n"
            f"{context_json}"
        )
        return model_prompt, {
            "schema_version": MODEL_CONTEXT_SCHEMA_VERSION,
            "chars": len(context_json),
            "truncated": truncated,
        }

    def _model_state_context(self, state):
        state = self.state_machine.normalize(state)
        answered_slots = {}
        for field in [
            "region", "destination", "origin", "start_date", "end_date", "days",
            "arrival_time", "departure_time", "companions", "transport", "budget",
            "preferences", "excluded_preferences", "must_visit_places", "start_location",
            "accommodation_area", "schedule_pace", "walking_tolerance", "rest_preference",
        ]:
            value = state.get(field)
            if value not in [None, "", []]:
                answered_slots[field] = copy.deepcopy(value)
        candidates = []
        for item in (state.get("destination_candidates") or [])[:5]:
            if isinstance(item, dict):
                name = str(item.get("name") or "").strip()
            else:
                name = str(item or "").strip()
            if name:
                candidates.append(name)
        return {
            "context_schema_version": MODEL_CONTEXT_SCHEMA_VERSION,
            "context_truncated": False,
            "conversation_stage": str(state.get("conversation_stage") or "collecting"),
            "intent": str(state.get("intent") or ""),
            "pending_slot": str(state.get("pending_slot") or ""),
            "asked_slots": list(state.get("asked_slots") or []),
            "generation_requested": bool(state.get("generation_requested")),
            "conditions_confirmed": bool(state.get("conditions_confirmed")),
            "state_version": int(state.get("state_version") or 0),
            "answered_slots": answered_slots,
            "destination_candidates": candidates,
            "itinerary_summary": self._itinerary_summary(state.get("itinerary_draft") or {}),
        }

    def _bounded_context_json(self, context):
        context = copy.deepcopy(context if isinstance(context, dict) else {})
        encoded = self._context_json(context)
        if len(encoded) <= MODEL_CONTEXT_JSON_BUDGET:
            return encoded, False

        context["context_truncated"] = True
        context["asked_slots"] = list(context.get("asked_slots") or [])[:8]
        context["destination_candidates"] = [
            self._context_text(value, 50)
            for value in list(context.get("destination_candidates") or [])[:3]
        ]
        answered = {}
        for key, value in dict(context.get("answered_slots") or {}).items():
            if isinstance(value, list):
                answered[key] = [self._context_text(item, 80) for item in value[:10]]
            elif isinstance(value, str):
                answered[key] = self._context_text(value, 120)
            else:
                answered[key] = value
        context["answered_slots"] = answered
        summary = dict(context.get("itinerary_summary") or {})
        summary["title"] = self._context_text(summary.get("title"), 100)
        compact_days = []
        for day in list(summary.get("days") or [])[:14]:
            if not isinstance(day, dict):
                continue
            compact_days.append({
                "day": day.get("day"),
                "places": [self._context_text(place, 80) for place in list(day.get("places") or [])[:4]],
            })
        summary["days"] = compact_days
        context["itinerary_summary"] = summary
        encoded = self._context_json(context)

        while len(encoded) > MODEL_CONTEXT_JSON_BUDGET:
            reducible = [day for day in compact_days if len(day.get("places") or []) > 1]
            if not reducible:
                break
            max(reducible, key=lambda row: len(row.get("places") or []))["places"].pop()
            encoded = self._context_json(context)

        if len(encoded) > MODEL_CONTEXT_JSON_BUDGET:
            for day in compact_days:
                day["places"] = [self._context_text(place, 40) for place in day.get("places") or []]
            encoded = self._context_json(context)

        if len(encoded) > MODEL_CONTEXT_JSON_BUDGET:
            context["itinerary_summary"] = {
                "title": summary.get("title", ""),
                "days": [{"day": day.get("day"), "place_count": len(day.get("places") or [])} for day in compact_days],
            }
            encoded = self._context_json(context)
        if len(encoded) > MODEL_CONTEXT_JSON_BUDGET:
            context = {
                "context_schema_version": MODEL_CONTEXT_SCHEMA_VERSION,
                "context_truncated": True,
                "conversation_stage": self._context_text(context.get("conversation_stage"), 40),
                "intent": self._context_text(context.get("intent"), 40),
                "pending_slot": self._context_text(context.get("pending_slot"), 40),
                "state_version": int(context.get("state_version") or 0),
            }
            encoded = self._context_json(context)
        return encoded, True

    def _context_json(self, value):
        return (
            json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026")
        )

    def _context_text(self, value, limit):
        value = " ".join(str(value or "").split())
        return value[:max(0, int(limit or 0))]

    def _itinerary_summary(self, draft):
        if not isinstance(draft, dict) or not draft.get("days"):
            return {}
        days = []
        for index, day in enumerate((draft.get("days") or [])[:14], start=1):
            if not isinstance(day, dict):
                continue
            places = []
            for place in (day.get("places") or [])[:8]:
                if not isinstance(place, dict):
                    continue
                name = str(place.get("name") or "").strip()
                category = str(place.get("category") or "").strip()
                if name:
                    places.append(f"{name} ({category})" if category else name)
            days.append({"day": int(day.get("day") or index), "places": places})
        return {"title": str(draft.get("title") or "").strip(), "days": days}

    def _model_generation_allowed(self, prompt, state):
        text = " ".join(str(prompt or "").strip().split())
        affirmative = text in {"응", "네", "예", "좋아", "좋아요", "그대로", "그대로 해줘", "해줘"}
        return bool(
            state.get("conversation_stage") == "ready_to_generate"
            and affirmative
        )

    def _recommend_destinations(self, state):
        catalog = [
            {"name": "강릉", "themes": ["바다", "감성카페", "사진 명소"], "transit": True, "seoul": 9, "burden": "KTX 약 2시간"},
            {"name": "전주", "themes": ["한옥", "맛집", "문화"], "transit": True, "seoul": 8, "burden": "KTX·버스 약 2시간"},
            {"name": "춘천", "themes": ["호수", "자연", "카페"], "transit": True, "seoul": 10, "burden": "ITX 약 1시간 20분"},
            {"name": "경주", "themes": ["역사", "야경", "사진 명소"], "transit": True, "seoul": 6, "burden": "KTX 포함 약 2시간 30분"},
            {"name": "속초", "themes": ["바다", "시장", "자연"], "transit": True, "seoul": 7, "burden": "고속버스 약 2시간 20분"},
            {"name": "여수", "themes": ["바다", "야경", "맛집"], "transit": True, "seoul": 5, "burden": "KTX 약 3시간"},
            {"name": "부산", "themes": ["바다", "맛집", "도시 여행"], "transit": True, "seoul": 4, "burden": "KTX 약 2시간 40분"},
            {"name": "통영", "themes": ["섬", "바다", "케이블카"], "transit": False, "seoul": 3, "burden": "버스 약 4시간"},
        ]
        origin = str(state.get("origin") or "")
        transport = str(state.get("transport") or "")
        companions = set(state.get("companions") or [])
        preferences = set(state.get("preferences") or [])
        romantic = {"강릉", "전주", "경주", "여수", "춘천"}
        family = {"경주", "속초", "부산", "전주"}

        def score(item):
            value = item.get("seoul", 0) if origin in ["서울", "인천", "수원"] else 5
            if transport in ["대중교통", "도보"] and item.get("transit"):
                value += 4
            if "연인" in companions and item["name"] in romantic:
                value += 3
            if companions.intersection({"가족", "아이 동반", "부모님"}) and item["name"] in family:
                value += 3
            value += len(preferences.intersection(set(item["themes"]))) * 2
            return value

        rows = sorted(catalog, key=lambda item: (-score(item), catalog.index(item)))[:3]
        return [
            {
                "name": item["name"],
                "reason": self._destination_reason(item, companions),
                "travel_burden": item["burden"] if origin in ["서울", "인천", "수원"] else "출발지 기준 이동편 확인 필요",
                "themes": list(item["themes"]),
                "transport_note": "대중교통 여행에 편리함" if item["transit"] else "현지 이동수단 확인 권장",
            }
            for item in rows
        ]

    def _destination_reason(self, item, companions):
        theme = "·".join(item.get("themes", [])[:2])
        if "연인" in companions:
            return f"{theme} 중심으로 함께 즐기기 좋은 커플 여행지"
        if companions.intersection({"가족", "아이 동반", "부모님"}):
            return f"{theme} 중심으로 가족이 함께 둘러보기 좋은 여행지"
        if "친구" in companions:
            return f"{theme} 중심으로 친구와 알차게 여행하기 좋은 곳"
        return f"{theme} 중심으로 짧은 여행을 구성하기 좋은 곳"

    def _is_generation_confirmation(self, prompt, state):
        text = " ".join(str(prompt or "").strip().split())
        if state.get("conversation_stage") == "ready_to_generate" and text in {
            "응", "네", "예", "좋아", "좋아요", "그대로", "그대로 해줘", "해줘",
        }:
            return True
        if "이 조건으로" in text and any(token in text for token in ["코스", "일정"]):
            return True
        if any(token in text for token in [
            "이 조건으로 코스", "이 조건으로 일정", "조건 확인했어", "그대로 코스",
            "코스 만들기", "다시 코스 만들어", "재시도",
        ]):
            return True
        return bool(
            state.get("conversation_stage") == "ready_to_generate"
            and any(token in text for token in ["만들어줘", "짜줘", "시작해줘"])
        )

    def _condition_edit_command(self, prompt, state):
        text = " ".join(str(prompt or "").strip().split())
        if text in ["조건 수정", "여행 조건 수정", "조건을 수정할게", "여행 조건을 수정할게"]:
            return "menu"
        mappings = [
            (["시작 위치 수정", "출발 위치 수정", "시작점 수정"], "start_location"),
            (["숙소 수정", "숙소 위치 수정", "숙소 변경"], "accommodation_area"),
            (["교통 수정", "교통수단 수정", "교통 변경", "교통수단 변경"], "transport"),
            (["일정 속도 수정", "일정 밀도 수정", "여행 속도 수정"], "schedule_pace"),
            (["취향 수정", "선호 수정"], "preferences"),
            (["날짜 수정", "여행 날짜 수정", "기간 수정"], "days"),
        ]
        for tokens, target in mappings:
            if any(token in text for token in tokens):
                return target
        return ""

    def _clear_condition(self, state, slot):
        state = self.state_machine.normalize(state)
        if slot == "preferences":
            state["preferences"] = []
            state["excluded_preferences"] = []
        elif slot == "days":
            state["days"] = None
            state["start_date"] = ""
            state["end_date"] = ""
            state["arrival_time"] = ""
            state["departure_time"] = ""
        elif slot in ["start_location", "accommodation_area", "transport", "schedule_pace"]:
            state[slot] = ""
        state["pending_slot"] = slot
        state["conditions_confirmed"] = False
        state["feasibility_status"] = "conditions_incomplete"
        return state

    def _recovery_strategy(self, prompt, state):
        if state.get("conversation_stage") != "error":
            return ""
        text = " ".join(str(prompt or "").strip().split())
        if "장소 수 줄" in text or "여유롭게 다시" in text:
            return "fewer_places"
        if "인접 권역" in text:
            return "adjacent_subregions"
        if "취향 조건 완화" in text or "취향 범위" in text:
            return "relax_preferences"
        return ""

    def _suggested_replies(self, state, failure_stage=""):
        state = self.state_machine.normalize(state)
        stage = str(state.get("conversation_stage") or "collecting")
        slot = str(state.get("pending_slot") or "")

        def rows(values):
            return [{"label": label, "prompt": prompt} for label, prompt in values]

        if stage == "editing_conditions" or slot == "condition_to_edit":
            return rows([
                ("시작 위치", "시작 위치 수정"), ("숙소", "숙소 수정"), ("교통", "교통 수정"),
                ("일정 속도", "일정 속도 수정"), ("취향", "취향 수정"),
                ("날짜·시간", "날짜 수정"),
            ])
        if stage == "error" or slot == "recovery_action":
            return rows([
                ("장소 수 줄이기", "여유롭게 다시 코스 만들어줘"),
                ("인접 권역 포함", "인접 권역을 포함해 다시 코스 만들어줘"),
                ("취향 조건 완화", "취향 조건 완화해서 다시 코스 만들어줘"),
                ("교통 변경", "교통 변경"),
            ])
        if stage == "ready_to_generate":
            return rows([
                ("코스 만들기", "이 조건으로 코스 만들어줘"),
                ("조건 수정", "조건 수정"),
            ])
        if stage == "draft_ready":
            return rows([
                ("장소 줄이기", "장소 수를 줄여줘"),
                ("덜 걷기", "걷는 거 적게 바꿔줘"),
                ("식당 교체", "식당을 다른 곳으로 교체해줘"),
                ("둘째 날 다시", "둘째 날만 다시 만들어줘"),
            ])
        options = {
            "region": [("서울", "서울"), ("부산", "부산"), ("제주", "제주")],
            "transport": [("도보", "도보"), ("대중교통", "대중교통"), ("자동차", "자동차")],
            "schedule_pace": [("여유롭게", "여유롭게"), ("보통", "보통"), ("알차게", "알차게")],
            "walking_tolerance": [
                ("10분 이내", "걷기는 10분 이내"), ("20분 이내", "걷기는 20분 이내"),
                ("걷기 괜찮음", "걷기는 괜찮아요"),
            ],
            "rest_preference": [
                ("자주 쉬기", "자주 쉬기"), ("보통", "휴식은 보통"), ("휴식 최소", "휴식 최소"),
            ],
            "preferences": [
                ("자연", "자연"), ("맛집", "맛집"), ("카페", "카페"), ("문화", "문화"),
            ],
            "days": [("당일", "당일"), ("1박 2일", "1박 2일"), ("2박 3일", "2박 3일")],
        }
        if slot == "start_location":
            region = str(state.get("region") or "")
            location_options = {
                "제주": [("제주공항", "제주공항"), ("제주버스터미널", "제주버스터미널")],
                "서울": [("서울역", "서울역"), ("김포공항", "김포공항")],
                "부산": [("부산역", "부산역"), ("김해공항", "김해공항")],
            }
            return rows(location_options.get(region, []))
        if slot == "accommodation_area":
            region = str(state.get("region") or "")
            return rows([
                (f"{region} 시내" if region else "시내", f"숙소는 {region} 시내" if region else "숙소는 시내"),
                ("숙소 직접 입력", "숙소 위치를 직접 입력할게"),
            ])
        return rows(options.get(slot, []))

    def _clarification(self, state, missing, changed):
        meaningful = bool(changed)
        asked = list(state.get("asked_slots") or [])
        slot = self.state_machine.next_question_slot(missing, asked, meaningful)
        if slot and slot not in asked:
            asked.append(slot)
            state["asked_slots"] = asked
        state["pending_slot"] = slot
        return self.state_machine.next_question(
            missing,
            asked[:-1] if slot else asked,
            meaningful,
            state=state,
        )

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
            "changed_slots": {},
            "user_intent": "provide_information",
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
                intent = str(data.get("user_intent") or "provide_information")
                return {
                    "changed_slots": data.get("changed_slots") if isinstance(data.get("changed_slots"), dict) else {},
                    "user_intent": intent if intent in MODEL_INTENTS else "provide_information",
                    "assistant_message": str(data.get("assistant_message") or "").strip(),
                }, False
        return {
            "changed_slots": {}, "user_intent": "provide_information", "assistant_message": "",
        }, True


Model = TravelPlannerAgent
