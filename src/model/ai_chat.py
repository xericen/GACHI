import datetime
import json
import os
import re
import urllib.error
import urllib.request

DEFAULT_MODEL = "gemini-2.5-flash"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
MAX_TOOL_LOOPS = 5
MODEL_SETTING_KEY = "ai_model_config"
SUPPORTED_MODELS = [
    dict(id="gemini-2.5-flash-lite", name="Gemini 2.5 Flash Lite", description="빠른 응답과 낮은 호출 비용에 적합"),
    dict(id="gemini-2.5-flash", name="Gemini 2.5 Flash", description="복합 일정 생성과 도구 호출에 적합"),
]

SYSTEM_INSTRUCTION = """
당신은 GACHI의 한국어 대화형 여행 일정 빌더 AI입니다.
친구와 채팅하듯 자연스럽고 가볍게 답하되, 장소 추천은 실제 일정으로 옮길 수 있을 만큼 구체적으로 작성하세요.
현재 질문과 최근 대화에서 지역, 날짜/시간대, 동행, 예산, 취향, 이동 선호를 추론하고, 부족한 정보는 한 번에 최대 2개만 짧게 물어보세요.
정보가 조금 부족해도 대화를 멈추지 말고 "일단 이렇게 잡아볼게요"처럼 합리적인 가정과 함께 초안을 제안하세요.
실시간 영업 여부, 예약 가능 여부, 정확한 가격은 확정하지 말고 "확인 필요", "대략", "예상"으로 표시하세요.

도구 사용 필수 규칙:
- 장소명, 카페, 음식점, 관광지, 숙소, 쇼핑 장소를 추천하거나 일정에 넣기 전에는 반드시 place_search를 호출하세요.
- place_search 결과의 results 배열에 있는 실제 장소명만 답변에 사용할 수 있습니다. results가 비어 있으면 찾지 못했다고 말하고 장소를 지어내지 마세요.
- 장소 간 이동수단, 소요 시간, 거리를 말하기 전에는 반드시 directions_lookup을 호출하세요.
- directions_lookup이 estimated 또는 not_available이면 "예상" 또는 "확인 필요"를 붙이세요.
- 사용자가 "거기서", "다음", "근처"처럼 말하면 최근 도구 결과와 대화 맥락을 기준으로 exclude_place_ids를 채워 중복 추천을 피하세요.

일반 답변은 6줄 이내로 유지하고, 일정 제안이 필요할 때는 반드시 아래 형식을 지키세요.

[일정 제안]
요약: 지역 · 동행 · 시간대 · 분위기
동선: [장소명 | 위치: 시/구/동 또는 주소 | 할 일: 한 줄] (이동수단 예상 N분 · N.km) → [다음 장소명 | 위치: ... | 할 일: ...]
장소 상세:
1. 장소명 - 위치 - 추천 이유 - 예상 체류 N분 - 확인 필요 사항
2. 장소명 - 위치 - 추천 이유 - 예상 체류 N분 - 확인 필요 사항
가져오기: "내 일정으로 가져오기"를 누르면 이 순서 그대로 플래너에서 수정할 수 있다고 안내하세요.

화살표 동선 규칙:
- 장소는 최소 2곳, 최대 5곳으로 제안하세요.
- 각 화살표 괄호에는 반드시 이동수단, 예상 소요 시간, 예상 거리 중 확인 가능한 값을 넣으세요.
- 장소명만 나열하지 말고 위치와 할 일을 함께 적으세요.
- 사용자가 특정 장소를 바꾸거나 추가하면 기존 동선의 순서와 이동 시간을 다시 계산한 형태로 다시 제안하세요.
- 마지막에는 다음 대화를 유도하는 짧은 질문 하나만 붙이세요.
""".strip()


class AiChat:
    def send(self, prompt, history_raw="[]", user_id="", thread_id=""):
        prompt = self._trim_text(prompt, 2000)
        if not prompt:
            return 400, dict(message="질문을 입력해주세요.")

        if not self._enabled():
            return 503, dict(message="AI 여행 모델이 관리자에 의해 중지되었습니다.")

        if not self._api_key():
            return 500, dict(message="AI API 키가 설정되지 않았습니다.")

        try:
            result = self._call_gemini(prompt, self._parse_history(history_raw))
            reply = result.get("reply", "")
        except urllib.error.HTTPError as error:
            status = error.code if error.code < 500 else 502
            return status, dict(message=self._error_message(error))
        except Exception:
            return 502, dict(message="AI 응답을 가져오지 못했습니다. 잠시 후 다시 시도해주세요.")

        if not reply:
            return 502, dict(message="AI 응답이 비어 있습니다. 다시 질문해주세요.")

        payload = dict(
            reply=reply,
            model=self._model(),
            interaction_id=result.get("interaction_id", ""),
            tool_logs=result.get("tool_logs", []),
        )
        itinerary_proposal = result.get("itinerary_proposal")
        if itinerary_proposal:
            payload["itinerary_proposal"] = itinerary_proposal

        if user_id:
            payload.update(self._save_thread(user_id, thread_id, prompt, reply, history_raw))
        return 200, payload

    def admin_settings(self):
        runtime = self._runtime_config()
        model = self._model()
        models = [dict(item) for item in SUPPORTED_MODELS]
        if model and model not in [item["id"] for item in models]:
            models.append(dict(id=model, name=model, description="현재 환경 설정 모델"))

        enabled = self._enabled()
        api_key_configured = bool(self._api_key())
        if not enabled:
            status = "disabled"
        elif api_key_configured:
            status = "ready"
        else:
            status = "missing_key"

        return dict(
            provider="Google Gemini",
            enabled=enabled,
            model=model,
            timeout=self._timeout(),
            temperature=self._temperature(),
            max_output_tokens=self._max_output_tokens(),
            api_key_configured=api_key_configured,
            status=status,
            models=models,
            tools=["장소 검색", "경로 조회"],
            updated_at=runtime.get("_updated_at", "")
        )

    def update_admin_settings(self, data):
        data = data if isinstance(data, dict) else {}
        model = str(data.get("model") or "").strip()
        allowed_models = [item["id"] for item in SUPPORTED_MODELS]
        current_model = self._model()
        if current_model and current_model not in allowed_models:
            allowed_models.append(current_model)
        if model not in allowed_models:
            raise ValueError("지원하는 AI 모델을 선택해주세요.")

        payload = dict(
            enabled=self._as_bool(data.get("enabled"), True),
            model=model,
            timeout=self._bounded_int(data.get("timeout"), 30, 5, 60),
            temperature=self._bounded_float(data.get("temperature"), 0.45, 0, 1),
            max_output_tokens=self._bounded_int(data.get("max_output_tokens"), 900, 256, 2048),
            updated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self._save_runtime_config(payload)
        return self.admin_settings()

    def threads(self, user_id, limit=30):
        if not user_id:
            return []

        rows = self._thread_db().rows(
            user_id=user_id,
            orderby="updated",
            order="DESC",
            page=1,
            dump=limit
        )
        return [self._thread_summary(row) for row in rows]

    def thread(self, user_id, thread_id):
        if not user_id or not thread_id:
            return None

        row = self._thread_db().get(id=thread_id, user_id=user_id)
        if row is None:
            return None

        return dict(
            id=row.get("id", ""),
            title=row.get("title", ""),
            messages=self._parse_thread_messages(row.get("messages", "[]")),
            created=str(row.get("created", "")),
            updated=str(row.get("updated", ""))
        )

    def _config_value(self, name, default=""):
        try:
            config = wiz.config("ai")
            gemini = getattr(config, "gemini", None)
            if gemini is not None:
                value = getattr(gemini, name, None)
                if value is not None:
                    return str(value).strip()
        except Exception:
            pass
        return default

    def _settings_db(self):
        db = wiz.model("portal/season/orm").use("app_setting")
        try:
            db.orm.create_table(safe=True)
        except Exception:
            pass
        return db

    def _runtime_config(self):
        try:
            row = self._settings_db().get(key=MODEL_SETTING_KEY)
            if row is None:
                return {}
            data = json.loads(row.get("value") or "{}")
            if not isinstance(data, dict):
                return {}
            data["_updated_at"] = str(row.get("updated") or data.get("updated_at") or "")
            return data
        except Exception:
            return {}

    def _save_runtime_config(self, data):
        db = self._settings_db()
        row = db.get(key=MODEL_SETTING_KEY)
        payload = dict(
            key=MODEL_SETTING_KEY,
            value=json.dumps(data, ensure_ascii=False),
            updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        if row is None:
            db.insert(payload)
        else:
            db.update(payload, id=row["id"])

    def _as_bool(self, value, default=True):
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        return str(value).strip().lower() in ["1", "true", "yes", "on"]

    def _bounded_int(self, value, default, minimum, maximum):
        try:
            return max(minimum, min(int(value), maximum))
        except Exception:
            return default

    def _bounded_float(self, value, default, minimum, maximum):
        try:
            return round(max(minimum, min(float(value), maximum)), 2)
        except Exception:
            return default

    def _api_key(self):
        key = (
            os.environ.get("GOOGLE_AI_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )
        if key:
            return key.strip()
        return self._config_value("api_key", "")

    def _model(self):
        runtime = self._runtime_config()
        model = str(runtime.get("model") or "").strip()
        if model:
            return model
        model = os.environ.get("GEMINI_MODEL", "").strip()
        if model:
            return model
        return self._config_value("model", DEFAULT_MODEL) or DEFAULT_MODEL

    def _timeout(self):
        runtime = self._runtime_config()
        raw = runtime.get("timeout")
        if raw is None:
            raw = os.environ.get("GEMINI_TIMEOUT", "").strip() or self._config_value("timeout", "30")
        return self._bounded_int(raw, 30, 5, 60)

    def _temperature(self):
        return self._bounded_float(self._runtime_config().get("temperature"), 0.45, 0, 1)

    def _max_output_tokens(self):
        return self._bounded_int(self._runtime_config().get("max_output_tokens"), 900, 256, 2048)

    def _enabled(self):
        return self._as_bool(self._runtime_config().get("enabled"), True)

    def _trim_text(self, value, limit=1200):
        text = str(value or "").strip()
        if len(text) > limit:
            return text[:limit].rstrip()
        return text

    def _parse_history(self, raw):
        try:
            rows = json.loads(raw or "[]")
        except Exception:
            return []

        if not isinstance(rows, list):
            return []

        history = []
        for row in rows[-12:]:
            if not isinstance(row, dict):
                continue
            role = str(row.get("role", "")).strip()
            if role not in ["user", "assistant"]:
                continue
            text = self._trim_text(row.get("text", ""), 900)
            if not text:
                continue
            history.append(dict(role=role, text=text))
        return history

    def _parse_thread_messages(self, raw):
        try:
            rows = json.loads(raw or "[]")
        except Exception:
            return []

        if not isinstance(rows, list):
            return []

        messages = []
        for row in rows[-80:]:
            if not isinstance(row, dict):
                continue
            role = str(row.get("role", "")).strip()
            if role not in ["user", "assistant"]:
                continue
            text = self._trim_text(row.get("text", ""), 2000)
            if not text:
                continue
            messages.append(dict(
                role=role,
                text=text,
                created=str(row.get("created", ""))
            ))
        return messages

    def _thread_db(self):
        db = wiz.model("portal/season/orm").use("chat_thread")
        try:
            db.orm.create_table(safe=True)
        except Exception:
            pass
        return db

    def _now(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _thread_title(self, prompt):
        title = " ".join(str(prompt or "").strip().split())
        if len(title) > 36:
            title = title[:36].rstrip() + "..."
        return title or "새 여행 상담"

    def _thread_summary(self, row):
        messages = self._parse_thread_messages(row.get("messages", "[]"))
        preview = ""
        if messages:
            preview = messages[-1].get("text", "")
            if len(preview) > 52:
                preview = preview[:52].rstrip() + "..."
        return dict(
            id=row.get("id", ""),
            title=row.get("title", "") or "새 여행 상담",
            preview=preview,
            message_count=len(messages),
            created=str(row.get("created", "")),
            updated=str(row.get("updated", ""))
        )

    def _save_thread(self, user_id, thread_id, prompt, reply, history_raw):
        db = self._thread_db()
        now = self._now()
        row = db.get(id=thread_id, user_id=user_id) if thread_id else None
        messages = self._parse_thread_messages(row.get("messages", "[]")) if row else self._parse_history(history_raw)
        messages.append(dict(role="user", text=prompt, created=now))
        messages.append(dict(role="assistant", text=reply, created=now))
        messages = messages[-80:]

        title = row.get("title", "") if row else self._thread_title(prompt)
        data = dict(
            user_id=user_id,
            title=title,
            messages=json.dumps(messages, ensure_ascii=False),
            updated=now
        )

        if row:
            db.update(data, id=row["id"], user_id=user_id)
            saved_id = row["id"]
        else:
            data["created"] = now
            saved_id = db.insert(data)

        return dict(thread_id=saved_id, title=title)

    def _build_input(self, prompt, history):
        lines = []
        if history:
            lines.append("최근 대화:")
            for item in history:
                role = "사용자" if item["role"] == "user" else "AI"
                lines.append(f"{role}: {item['text']}")
            lines.append("")
        lines.append("현재 사용자 질문:")
        lines.append(prompt)
        return "\n".join(lines)

    def _build_interaction_input(self, prompt, history):
        return [{
            "type": "user_input",
            "content": self._build_input(prompt, history),
        }]

    def _extract_reply(self, data):
        parts = []
        for step in data.get("steps", []):
            if step.get("type") == "thought":
                continue
            if step.get("type") == "function_call":
                continue

            content = step.get("content")
            if isinstance(content, str) and content.strip():
                parts.append(content.strip())
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
                        parts.append(str(item.get("text")).strip())

            text = step.get("text")
            if text:
                parts.append(str(text).strip())

        if parts:
            return "\n\n".join(parts).strip()

        output_text = data.get("output_text") or data.get("outputText")
        if output_text:
            return str(output_text).strip()
        return ""

    def _error_message(self, error):
        try:
            raw = error.read().decode("utf-8")
            data = json.loads(raw)
            message = data.get("error", {}).get("message") or data.get("message")
            if message:
                return str(message)
        except Exception:
            pass
        return "Gemini API 호출에 실패했습니다."

    def _call_gemini(self, prompt, history):
        input_steps = self._build_interaction_input(prompt, history)
        tool_logs = []
        last_data = {}
        interaction_id = ""
        validation_retry_used = False

        for _ in range(MAX_TOOL_LOOPS):
            data = self._post_interaction(input_steps)
            last_data = data
            interaction_id = data.get("id") or interaction_id
            steps = data.get("steps", [])
            if isinstance(steps, list) and steps:
                input_steps.extend(steps)

            function_calls = self._extract_function_calls(data)
            if function_calls:
                for call in function_calls:
                    result = self._execute_tool(call["name"], call.get("arguments", {}))
                    log = {
                        "functionCall": {
                            "id": call.get("id", ""),
                            "name": call["name"],
                            "arguments": call.get("arguments", {}),
                        },
                        "functionResponse": result,
                    }
                    tool_logs.append(log)
                    self._log_tool_event(log)
                    input_steps.append(self._function_result_step(call, result))
                continue

            reply = self._extract_reply(data)
            unknown_mentions = self._unknown_place_mentions(reply, tool_logs)
            if unknown_mentions:
                self._log_tool_violation(reply, unknown_mentions, tool_logs)
                if not validation_retry_used:
                    validation_retry_used = True
                    input_steps.append({
                        "type": "user_input",
                        "content": (
                            "검증 실패: 방금 응답에 place_search 결과에 없는 장소명이 포함되었거나 "
                            "장소 추천 전 place_search가 호출되지 않았습니다. "
                            f"문제 항목: {', '.join(unknown_mentions)}. "
                            "실제 tool_result에 있는 장소만 사용해서 다시 답하세요. "
                            "tool_result가 없다면 찾지 못했다고 답하세요."
                        ),
                    })
                    continue
            return {
                "reply": reply,
                "raw": data,
                "interaction_id": interaction_id,
                "tool_logs": tool_logs,
                "itinerary_proposal": self._extract_itinerary_proposal(reply),
            }

        reply = self._extract_reply(last_data)
        return {
            "reply": reply,
            "raw": last_data,
            "interaction_id": interaction_id,
            "tool_logs": tool_logs,
            "itinerary_proposal": self._extract_itinerary_proposal(reply),
        }

    def _post_interaction(self, input_steps):
        payload = dict(
            model=self._model(),
            store=False,
            input=input_steps,
            tools=self._tool_declarations(),
            system_instruction=SYSTEM_INSTRUCTION,
            generation_config=dict(
                temperature=self._temperature(),
                max_output_tokens=self._max_output_tokens(),
            ),
        )

        request = urllib.request.Request(
            GEMINI_URL,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key(),
            },
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=self._timeout()) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)

    def _tool_declarations(self):
        try:
            return wiz.model("ai_tools").function_declarations()
        except Exception:
            return []

    def _extract_function_calls(self, data):
        calls = []
        for step in data.get("steps", []):
            if step.get("type") != "function_call":
                continue
            name = str(step.get("name") or "").strip()
            if not name:
                continue
            calls.append(dict(
                id=str(step.get("id") or step.get("call_id") or "").strip(),
                name=name,
                arguments=self._parse_tool_arguments(step.get("arguments", {})),
            ))
        return calls

    def _parse_tool_arguments(self, value):
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                data = json.loads(value)
                return data if isinstance(data, dict) else {}
            except Exception:
                return {}
        return {}

    def _execute_tool(self, name, arguments):
        try:
            tools = wiz.model("ai_tools")
            if name == "place_search":
                return tools.execute_place_search(arguments)
            if name == "directions_lookup":
                return tools.execute_directions_lookup(arguments)
            return {"status": "error", "message": f"지원하지 않는 함수입니다: {name}"}
        except Exception as error:
            return {"status": "error", "message": str(error)}

    def _function_result_step(self, call, result):
        return {
            "type": "function_result",
            "name": call["name"],
            "call_id": call.get("id", ""),
            "result": [{
                "type": "text",
                "text": json.dumps(result, ensure_ascii=False),
            }],
        }

    def _allowed_tool_place_names(self, tool_logs):
        names = []
        for log in tool_logs:
            if log.get("functionCall", {}).get("name") != "place_search":
                continue
            response = log.get("functionResponse") or {}
            for row in response.get("results", []) or []:
                name = str(row.get("name", "")).strip()
                if name:
                    names.append(name)
        return names

    def _unknown_place_mentions(self, reply, tool_logs):
        if not reply:
            return []

        used_place_search = any(log.get("functionCall", {}).get("name") == "place_search" for log in tool_logs)
        looks_like_place_answer = any(token in reply for token in ["[일정 제안]", "동선:", "장소 상세:", "맛집", "카페", "관광지"])
        if looks_like_place_answer and not used_place_search:
            return ["place_search_missing"]

        allowed = self._allowed_tool_place_names(tool_logs)
        if not allowed:
            return []

        candidates = []
        for match in re.findall(r"\[([^\]|]{2,50})(?:\||\])", reply):
            candidates.append(match.strip())
        for line in reply.splitlines():
            match = re.match(r"\s*\d+\.\s*([^-|()]{2,50})", line)
            if match:
                candidates.append(match.group(1).strip())

        unknown = []
        for name in candidates:
            if name in ["일정 제안", "내 일정으로 가져오기"]:
                continue
            if not self._matches_allowed_place(name, allowed):
                unknown.append(name)
        return list(dict.fromkeys(unknown))

    def _matches_allowed_place(self, name, allowed):
        normalized = self._normalize_name(name)
        for item in allowed:
            allowed_name = self._normalize_name(item)
            if normalized == allowed_name or normalized in allowed_name or allowed_name in normalized:
                return True
        return False

    def _normalize_name(self, value):
        return re.sub(r"\s+", "", str(value or "").lower())

    def _extract_itinerary_proposal(self, reply):
        if not reply:
            return None

        candidates = []
        stripped = reply.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            candidates.append(stripped)
        for match in re.findall(r"```json\s*(\{.*?\})\s*```", reply, flags=re.S):
            candidates.append(match)

        for raw in candidates:
            try:
                data = json.loads(raw)
            except Exception:
                continue
            if isinstance(data, dict) and data.get("itinerary_proposal"):
                return data.get("itinerary_proposal")
        return None

    def _log_tool_event(self, log):
        function_call = log.get("functionCall", {}) if isinstance(log, dict) else {}
        payload = {
            "tool": function_call.get("name", ""),
            "has_response": bool(log.get("response")) if isinstance(log, dict) else False,
        }
        try:
            print("[ai_tool_call] " + json.dumps(payload, ensure_ascii=False))
        except Exception:
            pass

    def _log_tool_violation(self, reply, unknown_mentions, tool_logs):
        payload = {
            "unknown_mention_count": len(unknown_mentions or []),
            "reply_length": len(reply or ""),
            "tools": [
                log.get("functionCall", {}).get("name", "")
                for log in (tool_logs or [])
                if isinstance(log, dict)
            ],
        }
        try:
            print("[ai_tool_violation] " + json.dumps(payload, ensure_ascii=False))
        except Exception:
            pass


Model = AiChat()
