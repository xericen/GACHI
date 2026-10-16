import copy
import datetime
import re

Sources = wiz.model("agents/travel_event_sources")


class TravelEvents:
    def __init__(self, env_value=None, today_provider=None):
        self.sources = Sources(env_value or (lambda name: ""))
        self.today = today_provider or (lambda: datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))).date())

    def handle(self, prompt, state):
        text = str(prompt or "").strip().replace("콘서르", "콘서트")
        request = state.get("event_request") or {}
        candidates = state.get("event_candidates") or []
        if state.get("pending_slot") == "event_selection" and candidates:
            selected = next((item for item in candidates if text == self.label(item)), None)
            index = re.fullmatch(r"([1-5])(?:번)?", text)
            if index and int(index[1]) <= len(candidates):
                selected = candidates[int(index[1]) - 1]
            if selected:
                return self.select(state, selected)
        if state.get("pending_slot") == "event_time":
            match = re.search(r"(오전|오후)?\s*(\d{1,2})(?::(\d{2})|시(?:\s*(\d{1,2})분)?)", text)
            date = state.get("start_date") or ""
            if match and re.fullmatch(r"20\d{2}-\d{2}-\d{2}", date):
                hour = int(match[2])
                hour = hour + 12 if match[1] == "오후" and hour < 12 else 0 if match[1] == "오전" and hour == 12 else hour
                minute = int(match[3] or match[4] or 0)
                if hour < 24 and minute < 60:
                    request.update({"date": date, "time": f"{hour:02d}:{minute:02d}"})
                    state["pending_slot"] = "event_venue"
                    return {"message": "공연장이나 경기장 이름을 알려주세요.", "replies": []}
            return {"message": "예매한 날짜와 시작 시간을 함께 알려주세요.", "replies": []}
        if state.get("pending_slot") == "event_venue":
            return self.select(state, {
                "kind": request.get("kind"), "name": request.get("keyword") or request.get("kind"),
                "date": request["date"], "time": request["time"], "venue": text,
                "source_url": "", "duration_minutes": None, "source": "user",
            })
        kind = next((kind for kind in ["야구", "축구", "콘서트", "연극", "공연", "뮤지컬"] if kind in text), "")
        if not kind and state.get("pending_slot") != "event_name":
            return None
        keyword = text if not kind else text.split(kind)[0]
        keyword = re.sub(
            r"(?:이번\s*주(?:에는|에)?|다음\s*주(?:에는|에)?|오늘|내일|모레|엄마랑|엄마와|부모님과|친구랑|가족과|나는|저는|어떤)", " ", keyword,
        )
        keyword = re.sub(r"\d+월\s*\d+일", " ", keyword).strip(" ,.")
        keyword = re.sub(r"^.*?(?:에서|열리는|하는)\s*", "", keyword).strip()
        keyword = re.sub(r"의$", "", keyword).strip()
        keyword = re.sub(r"FC", "", keyword, flags=re.I).strip()
        keyword = re.sub(r"\s+", " ", keyword).strip()
        if state.get("pending_slot") == "event_name" and not kind:
            kind = request.get("kind") or "공연"
        if not kind:
            return None
        today = self.today()
        start = today
        end = today + datetime.timedelta(days=6 - today.weekday())
        if re.search(r"다음\s*주", text):
            start = end + datetime.timedelta(days=1)
            end = start + datetime.timedelta(days=6)
        elif any(word in text for word in ["오늘", "내일", "모레"]):
            offset = 2 if "모레" in text else 1 if "내일" in text else 0
            start = end = today + datetime.timedelta(days=offset)
        elif re.fullmatch(r"20\d{2}-\d{2}-\d{2}", str(state.get("start_date") or "")):
            start = datetime.date.fromisoformat(state["start_date"])
            end = datetime.date.fromisoformat(state.get("end_date") or state["start_date"])
        if request and state.get("pending_slot") == "event_name":
            start = datetime.date.fromisoformat(request["start"])
            end = datetime.date.fromisoformat(request["end"])
        end = min(end, start + datetime.timedelta(days=13))
        state["event_request"] = {"kind": kind, "keyword": keyword, "start": start.isoformat(), "end": end.isoformat()}
        state["event_selection"] = {}
        state["event_candidates"] = []
        state["pending_slot"] = "event_name"
        if not keyword:
            return {"message": "어느 팀 경기를 보시나요?" if kind in ["야구", "축구"] else "공연명이나 가수명을 알려주세요.", "replies": []}
        rows = self.sources.lookup(kind, keyword, start, end)
        # Match named events/teams before exposing candidate dates; never choose
        # an unrelated result merely because it is the first official entry.
        compact = re.sub(r"\s+", "", keyword).lower()
        rows = [row for row in rows if compact in re.sub(
            r"\s+", "", str(row.get("name") or "") + str(row.get("venue") or "")).lower()]
        rows = sorted(rows, key=lambda row: (row["date"], row["time"]))[:5]
        state["event_candidates"] = rows
        if len(rows) == 1:
            return self.select(state, rows[0])
        if rows:
            state["pending_slot"] = "event_selection"
            return {
                "message": "해당 기간의 공식 일정이에요. 방문할 회차를 골라주세요.\n"
                    + "\n".join(f"{index + 1}. {self.label(row)} · {row['venue']}" for index, row in enumerate(rows)),
                "replies": [{"label": self.label(row), "prompt": self.label(row)} for row in rows],
            }
        state["pending_slot"] = "event_time"
        return {
            "message": "예매한 날짜와 시작 시간을 알려주시면 그 일정에 맞춰 주변 코스를 구성할게요.",
            "replies": [],
        }

    def label(self, row):
        return f"{row['date']} {row['time']} {row['name']}"

    def select(self, state, row):
        state["event_selection"] = copy.deepcopy(row)
        state["event_candidates"] = []
        state["pending_slot"] = ""
        if not (int(state.get("days") or 1) > 1
                and str(state.get("start_date") or "") <= row["date"] <= str(state.get("end_date") or "")):
            state["start_date"] = row["date"]
            state["end_date"] = row["date"]
            state["days"] = 1
        if not state.get("arrival_time"):
            hour, minute = map(int, row["time"].split(":"))
            start = max(0, min(600, hour * 60 + minute - 60))
            state["arrival_time"] = f"{start // 60:02d}:{start % 60:02d}"
        venue = row["venue"]
        # Venue search is authoritative for geography. Only infer familiar city
        # names from the verified venue, otherwise retain the user's region.
        geography = str(row.get("region") or "") + " " + venue
        city = next((city for city in ["서울", "부산", "대전", "인천", "광주", "대구", "울산", "수원", "전주", "제주", "창원", "강릉", "포항"] if city in geography), "")
        if not city and any(word in venue for word in ["잠실", "고척", "올림픽", "대학로"]):
            city = "서울"
        if city:
            state["region"] = city
            state["destination"] = city
        request = state.get("event_request") or {}
        event_labels = {
            str(row.get("name") or "").replace(" ", ""),
            str(request.get("keyword") or "").replace(" ", ""),
            str(request.get("keyword") or "").replace(" ", "") + str(request.get("kind") or ""),
        }
        landmarks = [name for name in state.get("must_visit_places") or []
                     if str(name).replace(" ", "") not in event_labels]
        state["must_visit_places"] = list(dict.fromkeys(landmarks + [venue]))
        state["generation_requested"] = True
        source_note = f"공식 일정: {row['source_url']}\n" if row.get("source_url") else "말씀해주신 예매 정보를 반영했어요.\n"
        return {
            "message": f"{row['name']}은 {row['date']} {row['time']}, {venue} 일정이에요.\n"
                + source_note + "이 시간을 고정해 주변 코스를 준비할게요.",
            "replies": [],
        }


Model = TravelEvents
