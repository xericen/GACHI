import json
import re


class TravelReplyGuard:
    INTERNAL_PATTERN = re.compile(
        r"(?:place_search|directions_lookup|function[_ ]?call|functionResponse|"
        r"tool[_ ]?(?:call|result|log)s?|ValidationError|validation_failed|"
        r"tool_budget_exceeded|AI 응답을 검증하지 못|검증 실패)",
        re.IGNORECASE,
    )
    STRUCTURED_KEYS = {
        "extracted_slots", "changed_slots", "missing_slots", "user_intent",
        "action", "assistant_message",
    }

    def sanitize(self, message, stage="collecting", missing_slots=None, failure_stage=""):
        text = self._assistant_message(message)
        if not text or self._is_internal(text):
            return self.fallback(stage, missing_slots, failure_stage)
        return text

    def requires_recovery(self, status, payload):
        payload = payload if isinstance(payload, dict) else {}
        reason = str(payload.get("_fallback_reason") or "")
        message = str(payload.get("message") or payload.get("reply") or "")
        return (
            reason in {"validation_failed", "tool_budget_exceeded", "legacy_unverified_reply"}
            or self._is_internal(message)
            or (int(status or 0) >= 500 and "validation" in reason.lower())
        )

    def public_payload(self, payload):
        payload = dict(payload or {})
        stage = str(payload.get("stage") or "collecting")
        missing = payload.get("missing_slots") if isinstance(payload.get("missing_slots"), list) else []
        failure_stage = str(payload.get("failure_stage") or "")
        message = self.sanitize(
            payload.get("message") or payload.get("reply"), stage, missing, failure_stage,
        )
        payload["message"] = message
        payload["reply"] = message
        payload["warnings"] = [
            str(value).strip()
            for value in payload.get("warnings", [])
            if str(value).strip() and not self._is_internal(str(value))
        ]
        # Tool traces remain in observability metadata and are never part of the user contract.
        payload.pop("tool_logs", None)
        payload.pop("raw", None)
        return payload

    def recovery_payload(self, payload=None):
        payload = dict(payload or {})
        payload.setdefault("stage", "collecting")
        payload.setdefault("travel_state", {})
        payload.setdefault("itinerary_draft", {})
        payload.setdefault("missing_slots", [])
        payload.setdefault("action", "ask_clarification")
        payload.setdefault("failure_stage", "")
        payload.setdefault("warnings", [])
        payload["message"] = "여행 조건을 계속 정리해볼게요. 가고 싶은 지역과 여행 기간을 알려주세요."
        payload["reply"] = payload["message"]
        return self.public_payload(payload)

    def fallback(self, stage="collecting", missing_slots=None, failure_stage=""):
        missing = list(missing_slots or [])
        if failure_stage == "place_search":
            return "조건에 맞는 장소를 충분히 찾지 못했어요. 지역이나 원하는 분위기를 조금 넓혀볼까요?"
        if failure_stage == "directions":
            return "일부 이동 경로를 확인하지 못했어요. 가능한 동선으로 다시 계산해볼게요."
        if failure_stage == "model_config":
            return "답변 연결을 다시 확인하고 있어요. 여행 조건은 그대로 보관해둘게요."
        if stage == "draft_ready":
            return "코스 초안이 준비됐어요. 바꾸고 싶은 날짜나 장소를 말씀해주세요."
        if stage in ["generating", "revising"]:
            return "말씀해주신 조건을 반영해 코스를 정리하고 있어요."
        if stage == "ready_to_generate":
            return "여행 조건이 준비됐어요. 이 조건으로 코스를 만들어볼까요?"
        questions = {
            "region": "어느 지역으로 여행을 떠나고 싶으세요?",
            "days": "몇 일 동안 여행할 예정인가요?",
            "preferences": "어떤 분위기나 장소를 좋아하는지 하나만 알려주세요.",
        }
        for key in ["region", "days", "preferences"]:
            if key in missing:
                return questions[key]
        return "여행 조건을 계속 정리해볼게요. 다음으로 원하는 내용을 말씀해주세요."

    def _assistant_message(self, value):
        text = str(value or "").strip()
        if not text:
            return ""
        candidates = [text]
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            candidates.append(text[start:end + 1])
        for candidate in candidates:
            candidate = candidate.strip().strip("`")
            if candidate.lower().startswith("json"):
                candidate = candidate[4:].strip()
            try:
                data = json.loads(candidate)
            except Exception:
                continue
            if isinstance(data, dict):
                return str(data.get("assistant_message") or "").strip()
        return text

    def _is_internal(self, text):
        text = str(text or "")
        if self.INTERNAL_PATTERN.search(text):
            return True
        if text.lstrip().startswith("{") and any(f'"{key}"' in text for key in self.STRUCTURED_KEYS):
            return True
        return False


Model = TravelReplyGuard
