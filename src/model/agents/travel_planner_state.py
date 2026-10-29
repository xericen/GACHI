import copy
import datetime
import json
import re


ConditionValidation = wiz.model("agents/travel_condition_validation")


NaturalLanguageUnderstanding = wiz.model("agents/travel_nlu")


STAGES = {
    "collecting", "ready_to_generate", "generating", "draft_ready",
    "revising", "completed", "error", "collecting_destination_preferences",
    "destination_candidates_ready", "destination_selected", "editing_conditions",
    "checking_feasibility",
}
INTENTS = {
    "provide_information", "generate_course", "revise_course", "replace_place",
    "remove_place", "add_place", "change_schedule", "general_question",
    "destination_recommendation", "select_destination",
}
ACTIONS = {
    "ask_clarification", "generate_itinerary", "revise_itinerary", "answer_only",
    "recommend_destinations", "select_destination",
}
STATE_FIELDS = [
    "region", "destination", "origin", "start_date", "end_date", "days", "arrival_time", "departure_time",
    "companions", "transport", "budget", "preferences", "excluded_preferences",
    "must_visit_places", "start_location", "accommodation_area", "collected_place_ids", "itinerary_draft",
    "conversation_stage", "generation_requested", "asked_slots", "intent", "pending_slot",
    "destination_candidates", "schedule_pace", "walking_tolerance", "rest_preference",
    "conditions_confirmed", "feasibility_status", "recovery_strategy",
    "state_version", "event_request", "event_candidates", "event_selection", "start_location_candidates", "available_minutes", "max_places", "start_location_id",
]
LIST_FIELDS = {
    "companions", "preferences", "excluded_preferences", "must_visit_places", "collected_place_ids", "asked_slots",
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
    "조용한 분위기": ["조용한 곳", "조용한곳", "조용한 분위기", "조용하게", "조용히"],
}
COMMON_CONDITION_TYPOS = {
    "대중교퉁": "대중교통", "대중교튱": "대중교통", "대중 교퉁": "대중교통",
    "도부": "도보", "렌트가": "렌트카", "렌터가": "렌터카",
    "카폐": "카페", "맛짐": "맛집", "박물관ㄴ": "박물관",
}
COMMON_REGION_TYPOS = {
    "서을": "서울", "부싼": "부산", "강능": "강릉", "경쥬": "경주",
    "대젼": "대전", "광쥬": "광주", "인쳔": "인천", "수언": "수원",
    "제주도오": "제주도",
}


def default_state():
    return {
        "region": "",
        "destination": None,
        "origin": "",
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
        "start_location": "",
        "accommodation_area": "",
        "schedule_pace": "",
        "walking_tolerance": "",
        "rest_preference": "",
        "collected_place_ids": [],
        "itinerary_draft": {},
        "conversation_stage": "collecting",
        "generation_requested": False,
        "asked_slots": [],
        "intent": "",
        "pending_slot": "",
        "destination_candidates": [],
        "conditions_confirmed": False,
        "feasibility_status": "conditions_incomplete",
        "recovery_strategy": "",
        "state_version": 0,
        "event_request": {},
        "event_candidates": [],
        "event_selection": {},
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
        return {
            "changed_slots": value.get("changed_slots") if isinstance(value.get("changed_slots"), dict) else {},
            "user_intent": intent if intent in INTENTS else "provide_information",
            "assistant_message": str(value.get("assistant_message") or fallback_text or "").strip(),
        }


class TravelStateMachine:
    def __init__(self, today_provider=None):
        self.nlu = NaturalLanguageUnderstanding(today_provider=today_provider)

    @staticmethod
    def valid_location(value):
        return ConditionValidation.is_location(value)

    def normalize(self, raw):
        state = default_state()
        if isinstance(raw, dict):
            for field in STATE_FIELDS:
                if field in raw:
                    state[field] = copy.deepcopy(raw[field])
            # Backward compatibility for conversations saved before start and
            # lodging locations became separate conditions.
            if "start_location" not in raw and raw.get("accommodation_area"):
                state["start_location"] = str(raw.get("accommodation_area") or "").strip()
        for field in ["region", "destination", "origin", "start_location", "accommodation_area"]:
            if not ConditionValidation.is_location(state.get(field)):
                state[field] = None if field == "destination" else ""
        region = state.get("region") or state.get("destination") or ""
        state["region"] = region
        state["destination"] = region or None
        # Old conversations may have an automatically copied region as start.
        # A whole travel region is not a specific routing anchor.
        if state.get("start_location") == region:
            state["start_location"] = ""
        for field in ["arrival_time", "departure_time"]:
            if not ConditionValidation.is_time(state.get(field)):
                state[field] = ""
        for field in LIST_FIELDS:
            state[field] = self._unique(state.get(field))
        state["must_visit_places"] = self.filter_place_names(state["must_visit_places"])
        try:
            state["days"] = int(state["days"]) if state.get("days") not in [None, ""] else None
        except Exception:
            state["days"] = None
        if state["days"] is not None:
            state["days"] = max(1, min(state["days"], 14))
        try:
            state["state_version"] = max(0, int(state.get("state_version") or 0))
        except Exception:
            state["state_version"] = 0
        for key, maximum in [("available_minutes", 1440), ("max_places", 12)]:
            value = state.get(key)
            state[key] = value if type(value) is int and 1 <= value <= maximum else None
        if not isinstance(state.get("itinerary_draft"), dict):
            state["itinerary_draft"] = {}
        for field in ["event_request", "event_selection"]:
            if not isinstance(state.get(field), dict):
                state[field] = {}
        state["start_location_candidates"] = [
            {"name": str(row["name"])[:120], "address": str(row.get("address") or "")[:180], "place_id": str(row.get("place_id") or "")[:96]}
            for row in (state.get("start_location_candidates") or [])[:3]
            if isinstance(row, dict) and isinstance(row.get("name"), str) and ConditionValidation.is_location(row["name"])
        ] if isinstance(state.get("start_location_candidates"), list) else []
        if not isinstance(state.get("event_candidates"), list):
            state["event_candidates"] = []
        if not isinstance(state.get("destination_candidates"), list):
            state["destination_candidates"] = []
        if state.get("conversation_stage") not in STAGES:
            state["conversation_stage"] = "collecting"
        state["generation_requested"] = bool(state.get("generation_requested"))
        state["conditions_confirmed"] = bool(state.get("conditions_confirmed"))
        if state.get("feasibility_status") not in {
            "conditions_incomplete", "conditions_complete", "checking", "available", "unavailable",
        }:
            state["feasibility_status"] = "conditions_incomplete"
        return state

    def extract(self, prompt, state=None):
        current = self.normalize(state)
        text = self._correct_condition_typos(self._clean(prompt), current)
        changed = {}
        intent = self.intent(text, current)

        duration_match = re.search(r"(\d{1,2})\s*시간(?:\s*(\d{1,2})\s*분)?(?:\s*(?:정도|동안|가량|쯤|짜리))?", text)
        if duration_match and not any(token in text for token in ["걷는", "이동시간", "도보 시간"]):
            minutes = int(duration_match[1]) * 60 + int(duration_match[2] or 0)
            if 40 <= minutes <= 1440:
                changed["available_minutes"] = minutes
        count_match = re.search(r"(?:장소|방문지)\s*(\d+|한|하나|두|둘|세|셋|네|넷)\s*(?:개|곳)(?:만)?\s*(?:남|줄|유지)", text)
        if count_match:
            count = {"한": 1, "하나": 1, "두": 2, "둘": 2, "세": 3, "셋": 3, "네": 4, "넷": 4}.get(count_match[1])
            count = count if count is not None else int(count_match[1])
            if 1 <= count <= 12:
                changed["max_places"] = count

        regions = [(text.rfind(region), region) for region in REGIONS if region in text]
        if regions:
            selected_region = max(regions, key=lambda item: item[0])[1]
            selected_region = "제주" if selected_region == "제주도" else selected_region
            is_origin_answer = (
                current.get("intent") == "destination_recommendation"
                and current.get("pending_slot") == "origin"
            )
            is_recommendation_origin = (
                intent == "destination_recommendation"
                and bool(re.search(re.escape(selected_region) + r"(?:에서|출발)", text))
            )
            if is_origin_answer or is_recommendation_origin:
                changed["origin"] = selected_region
            else:
                changed["region"] = selected_region
                changed["destination"] = selected_region

        stay = re.search(r"(\d+)\s*박\s*(\d+)\s*일", text)
        if stay:
            changed["days"] = max(1, min(int(stay.group(2)), 14))
        else:
            day_match = re.search(r"(?<!박)(\d{1,2})\s*일(?:간|동안|짜리)?(?:로|으로|\s|$)", text)
            if day_match and re.match(
                r"\s*(?:오전|오후|새벽|아침|점심|저녁|밤|까지)",
                text[day_match.end():],
            ):
                day_match = None
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

        range_arrival, range_departure = self._date_range_times(text)
        arrival = range_arrival or self._time_near(text, ["도착", "시작"])
        departure = range_departure or self._time_near(text, ["출발", "돌아", "복귀", "끝"])
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
        elif any(token in text for token in ["교통은 미정", "교통수단 미정", "아직 모르", "이동수단 미정"]):
            changed["transport"] = "미정"

        pending_slot = str(current.get("pending_slot") or "")
        if pending_slot == "time_window" or re.search(r"(?:부터|까지|~)", text):
            changed.update(ConditionValidation.extract_window(text))
        if pending_slot == "rest_preference":
            if any(token in text for token in ["자주", "충분히", "쉬엄쉬엄"]):
                changed["rest_preference"] = "자주 쉬기"
            elif any(token in text for token in ["최소", "적게", "거의 없이"]):
                changed["rest_preference"] = "휴식 최소"
            elif "보통" in text:
                changed["rest_preference"] = "보통"
        else:
            if any(token in text for token in ["여유롭게", "천천히", "쉬엄쉬엄", "장소 수 줄"]):
                changed["schedule_pace"] = "여유롭게"
            elif any(token in text for token in ["알차게", "빡빡하게", "많이 둘러"]):
                changed["schedule_pace"] = "알차게"
            elif any(token in text for token in ["보통 속도", "적당한 속도", "적당히 둘러"]):
                changed["schedule_pace"] = "보통"
            elif pending_slot == "schedule_pace" and any(token in text for token in ["보통", "적당히"]):
                changed["schedule_pace"] = "보통"

        low_walking_tokens = [
            "걷기 최소", "거의 안 걷", "덜 걷", "걷는 거 적게", "걷는 것 적게",
            "많이 못 걸", "걷기 힘들", "걷는 거 싫", "걷는 것 싫", "이동 적게",
            "도보 적게", "짧게 걷", "저보행", "걷는 시간이 너무 길", "걷는 시간 줄",
        ]
        if (
            pending_slot == "walking_tolerance"
            or any(token in text for token in ["걷기", "걷는", "걸어도", "도보로", "도보 적게", "저보행"])
            or any(token in text for token in low_walking_tokens)
        ):
            walking_minutes = re.search(r"(10|15|20|30)\s*분", text)
            if walking_minutes:
                changed["walking_tolerance"] = f"{walking_minutes.group(1)}분 이내"
            elif any(token in text for token in low_walking_tokens):
                changed["walking_tolerance"] = "10분 이내"
            elif any(token in text for token in ["걷기 괜찮", "많이 걸어도", "걷는 건 상관없", "도보 상관없"]):
                changed["walking_tolerance"] = "걷기 괜찮음"

        companions = []
        companion_map = {
            "혼자": "혼자", "친구": "친구", "연인": "연인", "데이트": "연인", "커플": "연인",
            "가족": "가족", "부모님": "부모님", "엄마": "부모님", "어머니": "부모님",
            "아빠": "부모님", "아버지": "부모님", "아이": "아이 동반",
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

        accommodation = re.search(r"(?:숙소|호텔)(?:는|은|가|이)?\s*([가-힣A-Za-z0-9· ]{2,30}?)(?:에|쪽|근처|이야|입니다|로)", text)
        if accommodation:
            changed["accommodation_area"] = accommodation.group(1).strip()
        start_location = re.search(
            r"([가-힣A-Za-z0-9· ]{2,30}?(?:공항|역|터미널|숙소|호텔|리조트))"
            r"(?:에서|부터|근처|로)(?:\s*시작)?",
            text,
        )
        standalone_start_location = re.fullmatch(
            r"\s*([가-힣A-Za-z0-9· ]{2,30}?(?:공항|역|터미널|숙소|호텔|리조트))(?:이요|요)?\s*",
            text,
        )
        if start_location:
            location_name = re.split(r"(?:에서|부터|선택하고|그리고)\s*", start_location.group(1))[-1].strip()
            changed["start_location"] = re.sub(
                r"^(?:(?:이 조건으로|오늘|내일|모레)(?:은|는|부터)?\s+)+", "", location_name,
            ).strip()
        elif (standalone_start_location
              and current.get("region")
              and not current.get("start_location")):
            # Restored clients can lose pending_slot while retaining the
            # already collected region. A standalone, explicit transport hub
            # is still an unambiguous answer to the missing start question.
            changed["start_location"] = standalone_start_location.group(1).strip()
        elif current.get("pending_slot") == "start_location" and 1 < len(text) <= 40:
            pending_location = re.sub(
                r"(?:에서|부터)?\s*(?:시작(?:할게|해|이야)?|출발(?:할게|해|이야)?)$",
                "",
                text,
            ).strip()
            pending_location = re.sub(r"\s*(?:근처|주변)$", "", pending_location).strip()
            if (ConditionValidation.is_location(pending_location)
                    and not any(key in changed for key in ["start_date", "days", "transport", "arrival_time", "departure_time"])):
                changed["start_location"] = pending_location
        elif current.get("pending_slot") == "accommodation_area" and 1 < len(text) <= 40:
            pending_accommodation = re.sub(
                r"^(?:숙소|호텔)(?:는|은|가|이)?\s*", "", text,
            ).strip()
            pending_accommodation = re.sub(
                r"\s*(?:근처|주변|에 있어|이야|입니다)$", "", pending_accommodation,
            ).strip()
            if pending_accommodation:
                changed["accommodation_area"] = pending_accommodation

        if pending_slot == "region" and not changed and len(text) <= 25 and ConditionValidation.is_location(text):
            place_answer = re.sub(r"(?:에서|으로|로|이요|요)$", "", text).strip()
            if ConditionValidation.is_location(place_answer):
                changed["region"] = place_answer
                changed["destination"] = place_answer

        must_visit = self._extract_place_request(text)
        if must_visit:
            changed["must_visit_places"] = self._unique(list(current.get("must_visit_places") or []) + [must_visit])

        nlu_state = copy.deepcopy(current)
        for field in ["start_date", "end_date", "days", "companions", "transport"]:
            if field in changed:
                nlu_state[field] = copy.deepcopy(changed[field])
        nlu_state["preferences"] = self._unique(
            list(current.get("preferences") or []) + list(changed.get("preferences") or [])
        )
        nlu_state["excluded_preferences"] = self._unique(
            list(current.get("excluded_preferences") or []) + list(changed.get("excluded_preferences") or [])
        )
        changed.update(self.nlu.extract(text, nlu_state))
        if must_visit:
            # Deterministic extraction is narrower than the generic NLU.  Keep
            # it authoritative for explicit "꼭 넣어줘" requests so the
            # preceding sentence (for example "대중교통 코스를 만들고") is
            # not added as a second landmark.
            changed["must_visit_places"] = self._unique(
                list(current.get("must_visit_places") or []) + [must_visit]
            )

        available = changed.get("available_minutes") or current.get("available_minutes")
        if available and not (changed.get("departure_time") or current.get("departure_time")):
            clock = changed.get("arrival_time") or current.get("arrival_time")
            if not clock and current.get("pending_slot") == "time_window":
                match = re.search(r"(오전|오후)?\s*(\d{1,2})(?::([0-5]\d)|\s*시(?!간))", text)
                if match:
                    hour = int(match[2])
                    if match[1] == "오후" and hour < 12:
                        hour += 12
                    if match[1] == "오전" and hour == 12:
                        hour = 0
                    if hour < 24:
                        clock = f"{hour:02d}:{int(match[3] or 0):02d}"
                        changed["arrival_time"] = clock
            if clock:
                finish = int(clock[:2]) * 60 + int(clock[3:]) + int(available)
                if finish < 1440:
                    changed["departure_time"] = f"{finish // 60:02d}:{finish % 60:02d}"

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
            if field not in STATE_FIELDS or field in [
                "conversation_stage", "itinerary_draft", "collected_place_ids",
                "generation_requested", "asked_slots", "intent", "pending_slot",
                "destination_candidates", "conditions_confirmed", "feasibility_status",
                "state_version",
            ]:
                continue
            if field in ["region", "destination", "origin", "start_location", "accommodation_area"] and not ConditionValidation.is_location(value):
                continue
            if field in ["preferences", "excluded_preferences", "must_visit_places"]:
                merged[field] = self._unique(list(merged.get(field) or []) + list(value or []))
            elif field in LIST_FIELDS:
                merged[field] = self._unique(value)
            elif field in {"available_minutes", "max_places"}:
                if type(value) is int:
                    merged[field] = value
            elif field == "days":
                try:
                    merged[field] = max(1, min(int(value), 14))
                except Exception:
                    continue
            elif field == "destination":
                merged[field] = str(value or "").strip() or None
                if merged[field]:
                    merged["region"] = merged[field]
            elif field == "region":
                merged[field] = str(value or "").strip()
                merged["destination"] = merged[field] or None
            else:
                merged[field] = str(value or "").strip()

        merged["must_visit_places"] = self.filter_place_names(merged["must_visit_places"])
        excluded = set(merged.get("excluded_preferences") or [])
        merged["preferences"] = [item for item in merged.get("preferences") or [] if item not in excluded]
        route_changed = any(merged.get(key) != before.get(key) for key in [
            "region", "days", "start_date", "end_date", "transport", "preferences",
            "excluded_preferences", "must_visit_places", "arrival_time", "departure_time",
            "companions", "budget", "start_location", "accommodation_area",
            "schedule_pace", "walking_tolerance", "rest_preference", "recovery_strategy",
        ])
        if route_changed:
            merged["conditions_confirmed"] = False
            merged["feasibility_status"] = "conditions_incomplete"
        if route_changed and before.get("itinerary_draft"):
            merged["conversation_stage"] = "revising"
        if merged.get("region") != before.get("region"):
            merged["collected_place_ids"] = []
            merged["itinerary_draft"] = {}
        return merged

    def apply_generation_defaults(self, state):
        result = self.normalize(state)
        result["schedule_pace"] = result.get("schedule_pace") or "보통"
        result["rest_preference"] = result.get("rest_preference") or "보통"
        region = result.get("region") or result.get("destination") or ""
        result["accommodation_area"] = result.get("accommodation_area") or region
        if int(result.get("days") or 1) > 1:
            result["arrival_time"] = result.get("arrival_time") or "10:00"
            result["departure_time"] = result.get("departure_time") or "21:30"
        if not result.get("days") and result.get("start_date") and result.get("end_date"):
            result["days"] = self._date_days(result["start_date"], result["end_date"])
        if not result.get("preferences"):
            companions = set(result.get("companions") or [])
            if "연인" in companions:
                result["preferences"] = ["감성카페", "맛집", "사진 명소"]
            elif companions.intersection({"가족", "아이 동반", "부모님"}):
                result["preferences"] = ["자연", "맛집", "문화"]
            elif "친구" in companions:
                result["preferences"] = ["맛집", "카페", "체험"]
            elif "혼자" in companions:
                result["preferences"] = ["자연", "문화"]
            else:
                result["preferences"] = ["맛집", "문화"]
        return result

    def missing_slots(self, state):
        state = self.normalize(state)
        missing = []
        if not (state.get("region") or state.get("destination")):
            missing.append("region")
        if not state.get("days") and not (state.get("start_date") and state.get("end_date")):
            missing.append("days")
        if not state.get("start_location"):
            missing.append("start_location")
        if state.get("transport") not in {"도보", "자동차", "대중교통"}:
            missing.append("transport")
        if int(state.get("days") or 1) == 1 and not ConditionValidation.valid_window(state.get("arrival_time"), state.get("departure_time")):
            missing.append("time_window")
        return missing

    def destination_missing_slots(self, state):
        state = self.normalize(state)
        missing = []
        if not state.get("origin"):
            missing.append("origin")
        if not state.get("companions"):
            missing.append("companions")
        if not state.get("transport"):
            missing.append("transport")
        if not state.get("days"):
            missing.append("days")
        return missing

    def destination_next_question(self, state, meaningful_answer=False):
        state = self.normalize(state)
        missing = self.destination_missing_slots(state)
        asked = set(state.get("asked_slots") or [])
        candidates = [slot for slot in missing if slot not in asked] if meaningful_answer else list(missing)
        slot = (candidates or missing or [""])[0]
        questions = {
            "origin": "좋아요. 어디에서 출발하시나요?",
            "companions": "누구와 함께 여행하시나요? 혼자, 연인, 친구, 가족 중에서 알려주세요.",
            "transport": "주로 어떤 교통수단을 이용하실 예정인가요?",
            "days": "며칠 일정으로 여행하고 싶으신가요?",
        }
        return slot, questions.get(slot, "여행지 후보를 준비해볼게요.")

    def next_question(self, missing, asked_slots=None, meaningful_answer=False, state=None):
        questions = {
            "region": "어느 지역으로 여행할 예정인가요?",
            "start_location": "여행지에서 어디를 시작점으로 할까요? 공항, 역, 터미널이나 첫 출발 장소를 알려주세요.",
            "accommodation_area": "여러 날 머무를 숙소는 어느 지역인가요? 호텔명이나 숙소 권역을 알려주세요.",
            "transport": "여행지에서는 걸어서, 자동차로, 대중교통으로 이동할 예정인가요?",
            "schedule_pace": "일정은 여유롭게, 보통, 알차게 중 어떤 속도로 둘러볼까요?",
            "walking_tolerance": "한 번에 어느 정도까지 걸을 수 있나요? 10분, 20분 이내 또는 걷기 괜찮음 중에서 알려주세요.",
            "rest_preference": "중간 휴식은 자주 쉬기, 보통, 휴식 최소 중 어떤 방식이 좋을까요?",
            "days": "여행은 며칠 일정으로 생각하고 있나요?",
            "time_window": "몇 시부터 몇 시까지 둘러볼까요? 예를 들어 오후 2시부터 6시처럼 알려주세요.",
            "preferences": "바다, 자연, 맛집, 카페, 문화 중 어떤 취향을 가장 원하나요?",
        }
        candidates = list(missing or [])
        asked = set(asked_slots or [])
        if meaningful_answer:
            candidates = [slot for slot in candidates if slot not in asked] or candidates
        slot = (candidates or [""])[0]
        if slot == "time_window" and state and state.get("available_minutes") and not state.get("arrival_time"):
            return f"{state['available_minutes']}분 일정은 몇 시에 시작할까요?"
        if slot == "preferences":
            current = self.normalize(state)
            region = str(current.get("region") or current.get("destination") or "여행지").strip()
            companions = list(current.get("companions") or [])
            companion_labels = {
                "혼자": "혼자 ",
                "친구": "친구와 ",
                "연인": "연인과 ",
                "가족": "가족과 ",
                "부모님": "부모님과 ",
                "아이 동반": "아이와 ",
            }
            companion = companion_labels.get(companions[0], f"{companions[0]}와 ") if companions else ""
            return (
                f"{region}에서 {companion}어떤 곳을 가장 가고 싶으세요? "
                "바다, 자연, 맛집, 카페, 문화 중에서 골라주세요."
            )
        return questions.get(slot, "이 조건으로 코스를 만들어볼까요?")

    def next_question_slot(self, missing, asked_slots=None, meaningful_answer=False):
        candidates = list(missing or [])
        asked = set(asked_slots or [])
        if meaningful_answer:
            candidates = [slot for slot in candidates if slot not in asked] or candidates
        return (candidates or [""])[0]

    def intent(self, text, state):
        has_draft = bool(state.get("itinerary_draft"))
        if has_draft and any(token in text for token in ["남겨", "빡빡", "여유롭게", "걷는 시간이", "출발하는 걸로", "출발로 변경", "마지막은", "마지막에", "시작점 변경"]):
            return "revise_course"
        if self._destination_recommendation(text):
            return "destination_recommendation"
        if state.get("intent") == "destination_recommendation":
            has_region = any(region in text for region in REGIONS)
            if has_region and state.get("pending_slot") != "origin":
                return "select_destination"
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
        if has_draft and "날" in text and any(token in text for token in ["다시 만들어", "새로 만들어", "다시 짜"]):
            return "revise_course"
        if self._explicit_generate(text):
            return "generate_course"
        if has_draft and any(token in text for token in ["수정", "너무 많", "줄여", "장소 줄", "늦춰", "당겨"]):
            return "revise_course"
        if has_draft and any(token in text for token in [
            "한식 말고", "양식으로", "사진 찍기 좋은", "사진 명소", "포토 스팟",
            "야경을 꼭", "비 오는 날", "비오는 날", "실내 위주", "실내 중심",
            "걷는 거 적게", "걷기 적게", "덜 걷", "예산",
        ]):
            return "revise_course"
        if "?" in text or any(text.endswith(token) for token in ["나요", "까", "어때"]):
            return "general_question"
        return "provide_information"

    def action_for(self, intent):
        if intent == "destination_recommendation":
            return "recommend_destinations"
        if intent == "select_destination":
            return "select_destination"
        if intent == "generate_course":
            return "generate_itinerary"
        if intent in ["revise_course", "replace_place", "remove_place", "add_place", "change_schedule"]:
            return "revise_itinerary"
        if intent == "general_question":
            return "answer_only"
        return "ask_clarification"

    def _destination_recommendation(self, text):
        patterns = [
            r"여행지.{0,12}(?:추천|알려|골라)",
            r"어디로.{0,18}(?:가|여행).{0,10}(?:좋|추천)",
            r"어디(?:가|로).{0,12}(?:좋|갈까|가면)",
            r"국내\s*여행.{0,12}(?:갈\s*만한\s*곳|추천|알려)",
            r"주말.{0,12}갈\s*곳.{0,10}추천",
            r"커플\s*여행지.{0,10}(?:골라|추천)",
            r"갈\s*만한\s*여행지.{0,10}(?:추천|알려)",
        ]
        return any(re.search(pattern, text) for pattern in patterns)

    def _explicit_generate(self, text):
        target = r"(?:코스|일정|동선|여행\s*계획)"
        action = r"(?:만들|짜|계획해|구성해|추천해)"
        if re.search(target + r".{0,18}" + action, text) or re.search(action + r".{0,18}" + target, text):
            return True
        recommendation = bool(re.search(r"(?:카페|맛집|장소|가볼\s*곳|데이트).{0,12}(?:추천해|추천해줘|추천해 줘)", text))
        travel_context = any(region in text for region in REGIONS) and any(token in text for token in [
            "오늘", "내일", "모레", "주말", "당일", "여행", "데이트", "가려고", "갈 거",
        ])
        return recommendation and travel_context

    def _extract_place_request(self, text):
        scoped_text = str(text or "")
        clauses = re.split(r"(?:만들고|그리고)\s+", scoped_text)
        if len(clauses) > 1 and re.search(r"(?:넣어|추가해|가고 싶)", clauses[-1]):
            scoped_text = clauses[-1]
        match = re.search(
            r"(?:^|[,.!?])"
            r"(?:(?:첫째|둘째|셋째)\s*날|\d+일차)?\s*"
            r"([가-힣A-Za-z0-9· ]{2,30}?)(?:을|를)?\s*"
            r"(?:(?:꼭|반드시)\s*)?(?:넣어줘|넣어 줘|추가해줘|가고 싶)",
            scoped_text,
        )
        if not match:
            return ""
        value = match.group(1).strip()
        # Date and travel mode prefixes describe the visit, not the landmark.
        value = re.sub(
            r"^(?:(?:오늘|내일|모레|이번 주말|다음 주말)(?:은|는)?\s+"
            r"|(?:도보로|걸어서|대중교통으로|자동차로)\s+)+",
            "", value,
        ).strip()
        places = self.filter_place_names([value])
        return places[0] if places else ""

    def filter_place_names(self, values):
        """Reject condition-only values from extraction, model slots and saved state."""
        condition = (
            r"(?:오늘|내일|모레|당일(?:치기)?|이번\s*주말|다음\s*주말"
            r"|(?:월|화|수|목|금|토|일)요일"
            r"|도보|걸어서|걷기|대중교통|자동차|자차|렌터카|렌트카|미정"
            r"|혼자|친구|연인|가족|부모님|아이\s*동반"
            r"|여유롭게|보통|알차게|한\s*곳|추천"
            r"|\d+\s*(?:박|일|일차|분|시간|만원|원)"
            r"|20\d{2}[-./]\d{1,2}[-./]\d{1,2}"
            r"|\d{1,2}월\s*\d{1,2}일|(?:오전|오후)?\s*\d{1,2}(?::\d{2}|시))"
        )
        suffix = r"(?:으로|로|은|는|을|를|에|만|위주|중심|이내)?"
        return [
            value for value in self._unique(values)
            if value not in {"장소", "카페", "맛집", "관광지", "바다", "자연", "야경", "쇼핑", "실내", "산책"}
            and not re.fullmatch(r"(?:" + condition + suffix + r"[\s,·/]*?)+", value)
        ]

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

    def _date_range_times(self, text):
        if not re.search(r"\d{1,2}\s*월\s*\d{1,2}.*부터.*\d{1,2}\s*일.*까지", text):
            return "", ""
        matches = list(re.finditer(
            r"(오전|오후)?\s*(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분)?",
            text,
        ))
        if len(matches) < 2:
            return "", ""
        return self._normalized_time(matches[0]), self._normalized_time(matches[-1])

    def _normalized_time(self, match):
        hour = int(match.group(2))
        if match.group(1) == "오후" and hour < 12:
            hour += 12
        if match.group(1) == "오전" and hour == 12:
            hour = 0
        return f"{hour:02d}:{int(match.group(3) or 0):02d}"

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

    def _correct_condition_typos(self, text, state):
        """Correct only high-confidence condition typos before extraction.

        Free-form place names are not fuzzy-matched here. The itinerary engine
        still resolves those against verified search results and coordinates.
        """
        corrected = str(text or "")
        for typo, canonical in COMMON_CONDITION_TYPOS.items():
            corrected = corrected.replace(typo, canonical)

        pending_slot = str((state or {}).get("pending_slot") or "")
        region_context = pending_slot == "region" or not (state or {}).get("region")
        if region_context:
            for typo, canonical in COMMON_REGION_TYPOS.items():
                corrected = re.sub(
                    rf"(?<![가-힣A-Za-z0-9]){re.escape(typo)}(?=(?:에서|으로|로|이요|요)?(?:\s|$))",
                    canonical,
                    corrected,
                )

        start_context = pending_slot == "start_location" or bool(
            (state or {}).get("region") and not (state or {}).get("start_location")
        )
        if start_context:
            corrected = re.sub(
                r"([가-힣A-Za-z0-9· ]{2,30}?)(?:녁|억)(?=(?:에서|부터|근처|으로|로|이요|요)?(?:\s|$))",
                r"\1역",
                corrected,
            )
            corrected = re.sub(r"터미날(?=(?:에서|부터|근처|으로|로|이요|요)?(?:\s|$))", "터미널", corrected)
        return corrected


Model = TravelStateMachine
