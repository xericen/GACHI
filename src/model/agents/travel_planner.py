import copy
import json
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

    def send(self, prompt, history_raw="[]", user_id="", thread_id="", client_message_id="", request_id=""):
        started = time.monotonic()
        prompt = str(prompt or "").strip()
        client_message_id = str(client_message_id or "").strip()[:96]
        request_id = str(request_id or uuid.uuid4().hex)
        user_message_id = f"user-{client_message_id}" if client_message_id else f"user-{uuid.uuid4().hex}"
        response_message_id = f"assistant-{request_id}"
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
        failure_stage = ""
        message = str(structured.get("assistant_message") or "").strip()
        missing = self.state_machine.missing_slots(state)
        destination_candidates = []

        if intent == "destination_recommendation":
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
                action = "ask_clarification"
                message = self._clarification(state, missing, changed)
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
                    state["generation_requested"] = False
                    state["asked_slots"] = []
                    state["pending_slot"] = ""
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
                message = self._clarification(state, missing, changed) if missing else "먼저 이 조건으로 코스를 만든 뒤 수정할 수 있어요."
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
                    message = self._clarification(state, missing, changed)
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
            "destination_candidates": copy.deepcopy(destination_candidates or state.get("destination_candidates") or []),
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
            )
            if stored:
                payload.update({"thread_id": stored.thread_id, "title": stored.title})
                payload["conversation_id"] = stored.thread_id
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
            if extracted.get("user_intent") == "generate_course":
                state["generation_requested"] = True
                state = self.state_machine.apply_generation_defaults(state)
            elif extracted.get("user_intent") == "destination_recommendation" or state.get("intent") == "destination_recommendation":
                state["intent"] = "destination_recommendation"
                missing = self.state_machine.destination_missing_slots(state)
                state["pending_slot"] = missing[0] if missing else ""
        return state

    def _safe_changed_slots(self, values):
        if not isinstance(values, dict):
            return {}
        allowed = {
            "region", "destination", "origin", "start_date", "end_date", "days", "arrival_time", "departure_time",
            "companions", "transport", "budget", "preferences", "excluded_preferences",
            "must_visit_places", "accommodation_area",
        }
        return {key: value for key, value in values.items() if key in allowed}

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

    def _clarification(self, state, missing, changed):
        meaningful = bool(changed)
        asked = list(state.get("asked_slots") or [])
        slot = self.state_machine.next_question_slot(missing, asked, meaningful)
        if slot and slot not in asked:
            asked.append(slot)
            state["asked_slots"] = asked
        return self.state_machine.next_question(missing, asked[:-1] if slot else asked, meaningful)

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
