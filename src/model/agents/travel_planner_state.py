import copy
import datetime
import json
import re


STAGES = {
    "collecting", "ready_to_generate", "generating", "draft_ready",
    "revising", "completed", "error",
}
INTENTS = {
    "provide_information", "generate_course", "revise_course", "replace_place",
    "remove_place", "add_place", "change_schedule", "general_question",
}
ACTIONS = {"ask_clarification", "generate_itinerary", "revise_itinerary", "answer_only"}
STATE_FIELDS = [
    "region", "start_date", "end_date", "days", "arrival_time", "departure_time",
    "companions", "transport", "budget", "preferences", "excluded_preferences",
    "must_visit_places", "accommodation_area", "collected_place_ids", "itinerary_draft",
    "conversation_stage",
]
LIST_FIELDS = {
    "companions", "preferences", "excluded_preferences", "must_visit_places", "collected_place_ids",
}
REGIONS = [
    "서울", "부산", "제주", "제주도", "강릉", "경주", "춘천", "속초", "양양", "통영",
    "거제", "포항", "울산", "대전", "광주", "세종", "인천", "수원", "전주", "여수",
    "충주", "제천", "안동", "군산", "목포", "순천", "남해", "하동", "평창", "대구",
]
PREFERENCE_ALIASES = {
    "바다": ["바다", "해변", "해안"],
    "자연": ["자연", "공원", "산책", "숲"],
    "맛집": ["맛집", "먹거리", "음식", "미식"],
    "카페": ["카페", "커피", "디저트", "브런치"],
    "문화": ["문화", "박물관", "미술관", "전시"],
    "야경": ["야경", "밤풍경", "전망"],
    "쇼핑": ["쇼핑", "시장"],
    "액티비티": ["액티비티", "레포츠", "체험"],
    "사진 명소": ["사진 명소", "사진 찍기 좋은", "포토 스팟", "인생샷"],
    "실내": ["실내 위주", "실내 중심", "비 오는 날", "비오는 날"],
}


def default_state():
    return {
        "region": "",
        "start_date": "",
        "end_date": "",
        "days": None,
        "arrival_time": "",
        "departure_time": "",
        "companions": [],
        "transport": "",
        "budget": "",
        "preferences": [],
        "excluded_preferences": [],
        "must_visit_places": [],
        "accommodation_area": "",
        "collected_place_ids": [],
        "itinerary_draft": {},
        "conversation_stage": "collecting",
    }


class StructuredResponseParser:
    def parse(self, raw):
        text = str(raw or "").strip()
        candidates = [text]
        candidates.extend(re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S | re.I))
        match = re.search(r"\{.*\}", text, flags=re.S)
        if match:
            candidates.append(match.group(0))
        for candidate in candidates:
            try:
                value = json.loads(candidate)
            except Exception:
                continue
            if isinstance(value, dict):
                return self._normalize(value, text), False
        return self._normalize({"assistant_message": text}, text), True

    def _normalize(self, value, fallback_text):
        intent = str(value.get("user_intent") or "provide_information")
        action = str(value.get("action") or "answer_only")
        return {
            "extracted_slots": value.get("extracted_slots") if isinstance(value.get("extracted_slots"), dict) else {},
            "changed_slots": value.get("changed_slots") if isinstance(value.get("changed_slots"), dict) else {},
            "missing_slots": value.get("missing_slots") if isinstance(value.get("missing_slots"), list) else [],
            "user_intent": intent if intent in INTENTS else "provide_information",
            "action": action if action in ACTIONS else "answer_only",
            "assistant_message": str(value.get("assistant_message") or fallback_text or "").strip(),
        }


class TravelStateMachine:
    def normalize(self, raw):
        state = default_state()
        if isinstance(raw, dict):
            for field in STATE_FIELDS:
                if field in raw:
                    state[field] = copy.deepcopy(raw[field])
        for field in LIST_FIELDS:
            state[field] = self._unique(state.get(field))
        try:
            state["days"] = int(state["days"]) if state.get("days") not in [None, ""] else None
        except Exception:
            state["days"] = None
        if state["days"] is not None:
            state["days"] = max(1, min(state["days"], 14))
        if not isinstance(state.get("itinerary_draft"), dict):
            state["itinerary_draft"] = {}
        if state.get("conversation_stage") not in STAGES:
            state["conversation_stage"] = "collecting"
        return state

    def extract(self, prompt, state=None):
        text = self._clean(prompt)
        current = self.normalize(state)
        changed = {}

        regions = [(text.rfind(region), region) for region in REGIONS if region in text]
        if regions:
            selected_region = max(regions, key=lambda item: item[0])[1]
            changed["region"] = "제주" if selected_region == "제주도" else selected_region

        stay = re.search(r"(\d+)\s*박\s*(\d+)\s*일", text)
        if stay:
            changed["days"] = max(1, min(int(stay.group(2)), 14))
        else:
            day_match = re.search(r"(?<!박)(\d{1,2})\s*일(?:간|동안|짜리)?(?:로|으로|\s|$)", text)
            if day_match:
                changed["days"] = max(1, min(int(day_match.group(1)), 14))
            elif "당일" in text:
                changed["days"] = 1

        dates = re.findall(r"(20\d{2})[.\-/년]\s*(\d{1,2})[.\-/월]\s*(\d{1,2})일?", text)
        if dates:
            normalized_dates = [self._date(*parts) for parts in dates]
            changed["start_date"] = normalized_dates[0]
            if len(normalized_dates) > 1:
                changed["end_date"] = normalized_dates[-1]
                changed["days"] = self._date_days(normalized_dates[0], normalized_dates[-1])

        arrival = self._time_near(text, ["도착", "시작"])
        departure = self._time_near(text, ["출발", "돌아", "복귀", "끝"])
        if arrival:
            changed["arrival_time"] = arrival
        if departure:
            changed["departure_time"] = departure

        if any(token in text for token in ["차 없이", "뚜벅이", "대중교통", "지하철", "버스"]):
            changed["transport"] = "대중교통"
        elif any(token in text for token in ["렌터카", "렌트카", "자동차", "자차", "차로"]):
            changed["transport"] = "자동차"
        elif "도보" in text or "걸어서" in text:
            changed["transport"] = "도보"

        companions = []
        companion_map = {
            "혼자": "혼자", "친구": "친구", "연인": "연인", "데이트": "연인",
            "가족": "가족", "부모님": "부모님", "아이": "아이 동반",
        }
        for token, label in companion_map.items():
            if token in text:
                companions.append(label)
        if companions:
            changed["companions"] = companions

        budget = re.search(r"(?:예산|비용)?\s*(\d+(?:\.\d+)?)\s*(만원|만\s*원|원)", text)
        if budget:
            changed["budget"] = f"{budget.group(1)}{budget.group(2).replace(' ', '')}"

        preferences = []
        excluded = list(current.get("excluded_preferences") or [])
        for label, aliases in PREFERENCE_ALIASES.items():
            for alias in aliases:
                if alias not in text:
                    continue
                around = text[max(0, text.index(alias) - 8):text.index(alias) + len(alias) + 10]
                if any(token in around for token in ["빼", "제외", "싫", "안 가", "말고"]):
                    excluded.append(label)
                else:
                    preferences.append(label)
                break
        if preferences:
            changed["preferences"] = self._unique(list(current.get("preferences") or []) + preferences)
        if excluded != list(current.get("excluded_preferences") or []):
            changed["excluded_preferences"] = self._unique(excluded)

        accommodation = re.search(r"(?:숙소|호텔)(?:는|은|가|이)?\s*([가-힣A-Za-z0-9 ]{2,20}?)(?:에|쪽|근처|이야|입니다|로)", text)
        if accommodation:
            changed["accommodation_area"] = accommodation.group(1).strip()

        must_visit = self._extract_place_request(text)
        if must_visit:
            changed["must_visit_places"] = self._unique(list(current.get("must_visit_places") or []) + [must_visit])

        intent = self.intent(text, current)
        return {
            "extracted_slots": copy.deepcopy(changed),
            "changed_slots": copy.deepcopy(changed),
            "missing_slots": [],
            "user_intent": intent,
            "action": self.action_for(intent),
            "assistant_message": "",
        }

    def merge(self, state, changed):
        before = self.normalize(state)
        merged = self.normalize(before)
        for field, value in (changed or {}).items():
            if field not in STATE_FIELDS or field in ["conversation_stage", "itinerary_draft", "collected_place_ids"]:
                continue
            if field in ["preferences", "excluded_preferences", "must_visit_places"]:
                merged[field] = self._unique(list(merged.get(field) or []) + list(value or []))
            elif field in LIST_FIELDS:
                merged[field] = self._unique(value)
            elif field == "days":
                try:
                    merged[field] = max(1, min(int(value), 14))
                except Exception:
                    continue
            else:
                merged[field] = str(value or "").strip()

        excluded = set(merged.get("excluded_preferences") or [])
        merged["preferences"] = [item for item in merged.get("preferences") or [] if item not in excluded]
        route_changed = any(merged.get(key) != before.get(key) for key in [
            "region", "days", "start_date", "end_date", "transport", "preferences",
            "excluded_preferences", "must_visit_places", "arrival_time", "departure_time",
            "companions", "budget",
        ])
        if route_changed and before.get("itinerary_draft"):
            merged["conversation_stage"] = "revising"
        if merged.get("region") != before.get("region"):
            merged["collected_place_ids"] = []
            merged["itinerary_draft"] = {}
        return merged

    def apply_generation_defaults(self, state):
        result = self.normalize(state)
        if not result.get("transport"):
            result["transport"] = "대중교통"
        if not result.get("arrival_time"):
            result["arrival_time"] = "10:00"
        if not result.get("departure_time"):
            result["departure_time"] = "18:00"
        if not result.get("days") and result.get("start_date") and result.get("end_date"):
            result["days"] = self._date_days(result["start_date"], result["end_date"])
        return result

    def missing_slots(self, state):
        state = self.normalize(state)
        missing = []
        if not state.get("region"):
            missing.append("region")
        if not state.get("days") and not (state.get("start_date") and state.get("end_date")):
            missing.append("days")
        if not state.get("preferences"):
            missing.append("preferences")
        return missing

    def next_question(self, missing):
        questions = {
            "region": "어느 지역으로 여행할 예정인가요?",
            "days": "여행은 며칠 일정으로 생각하고 있나요?",
            "preferences": "바다, 자연, 맛집, 카페, 문화 중 어떤 취향을 가장 원하나요?",
        }
        return questions.get((missing or [""])[0], "이 조건으로 코스를 만들어볼까요?")

    def intent(self, text, state):
        has_draft = bool(state.get("itinerary_draft"))
        if any(token in text for token in ["빼줘", "빼 줘", "제외해", "삭제해", "없애줘"]):
            return "remove_place" if has_draft else "provide_information"
        if any(token in text for token in ["다른 곳", "교체", "바꿔줘", "바꿔 줘"]):
            if not has_draft:
                return "provide_information"
            if any(token in text for token in ["장소", "카페", "맛집", "관광지", "첫째", "둘째", "셋째"]):
                return "replace_place"
            return "change_schedule"
        if any(token in text for token in ["추가해", "넣어줘", "넣어 줘", "한 곳 더"]):
            return "add_place" if has_draft else "provide_information"
        if self._explicit_generate(text):
            return "generate_course"
        if has_draft and any(token in text for token in ["수정", "너무 많", "줄여", "늦춰", "당겨"]):
            return "revise_course"
        if has_draft and any(token in text for token in [
            "한식 말고", "양식으로", "사진 찍기 좋은", "사진 명소", "포토 스팟",
            "야경을 꼭", "비 오는 날", "비오는 날", "실내 위주", "실내 중심",
            "걷는 거 적게", "걷기 적게", "덜 걷", "예산",
        ]):
            return "revise_course"
        if "?" in text or any(text.endswith(token) for token in ["야", "나요", "까", "어때"]):
            return "general_question"
        return "provide_information"

    def action_for(self, intent):
        if intent == "generate_course":
            return "generate_itinerary"
        if intent in ["revise_course", "replace_place", "remove_place", "add_place", "change_schedule"]:
            return "revise_itinerary"
        if intent == "general_question":
            return "answer_only"
        return "ask_clarification"

    def _explicit_generate(self, text):
        target = r"(?:코스|일정|동선|여행\s*계획)"
        action = r"(?:만들|짜|계획해|구성해|추천해)"
        return bool(re.search(target + r".{0,18}" + action, text) or re.search(action + r".{0,18}" + target, text))

    def _extract_place_request(self, text):
        match = re.search(r"(?:(?:첫째|둘째|셋째)\s*날|\d+일차)?\s*([가-힣A-Za-z0-9 ]{2,24}?)(?:을|를)?\s*(?:넣어줘|넣어 줘|추가해줘|가고 싶)", text)
        if not match:
            return ""
        value = match.group(1).strip()
        return "" if value in ["장소", "카페", "맛집", "관광지"] else value

    def _time_near(self, text, anchors):
        for anchor in anchors:
            match = re.search(anchor + r"[^\d]{0,8}(오전|오후)?\s*(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분)?", text)
            if not match:
                continue
            hour = int(match.group(2))
            if match.group(1) == "오후" and hour < 12:
                hour += 12
            if match.group(1) == "오전" and hour == 12:
                hour = 0
            return f"{hour:02d}:{int(match.group(3) or 0):02d}"
        return ""

    def _date(self, year, month, day):
        try:
            return datetime.date(int(year), int(month), int(day)).isoformat()
        except Exception:
            return ""

    def _date_days(self, start, end):
        try:
            return max(1, (datetime.date.fromisoformat(end) - datetime.date.fromisoformat(start)).days + 1)
        except Exception:
            return None

    def _unique(self, values):
        rows = []
        for value in values if isinstance(values, list) else []:
            value = str(value or "").strip()
            if value and value not in rows:
                rows.append(value)
        return rows

    def _clean(self, value):
        return re.sub(r"\s+", " ", str(value or "")).strip()


Model = TravelStateMachine
