import datetime
import re


print("[travel_nlu] travel_nlu loaded; NLU enabled")


KOREA_TIMEZONE = datetime.timezone(datetime.timedelta(hours=9))


def korea_today():
    return datetime.datetime.now(KOREA_TIMEZONE).date()


class TravelNaturalLanguageUnderstanding:
    """서버에서 상대 날짜와 여행 구어체를 결정론적으로 정규화한다."""

    COMPANION_ALIASES = {
        "연인": ["데이트", "애인", "남친", "여친", "남자친구", "여자친구"],
        "친구": ["친구들", "친구랑", "친구와", "친구끼리"],
        "가족": ["가족끼리", "가족이랑", "가족과"],
        "부모님": ["부모님", "엄마", "어머니", "아빠", "아버지"],
    }
    PREFERENCE_ALIASES = {
        "감성카페": ["감성"],
        "자연": ["힐링"],
        "사진 명소": ["사진 많이", "사진 찍", "사진을 찍", "사진명소"],
        "맛집": ["먹방"],
    }
    WEEKDAYS = {"월요일": 0, "화요일": 1, "수요일": 2, "목요일": 3, "금요일": 4, "토요일": 5, "일요일": 6}

    def __init__(self, today_provider=None):
        self.today_provider = today_provider or korea_today

    def extract(self, prompt, state=None):
        text = re.sub(r"\s+", " ", str(prompt or "")).strip()
        current = state if isinstance(state, dict) else {}
        changed = {}
        duration_explicit = self._duration(text)
        if duration_explicit:
            changed["days"] = duration_explicit

        absolute = self._absolute_date(text, current, duration_explicit)
        changed.update(absolute or self._relative_date(text, current, duration_explicit))

        companions = self._companions(text)
        if companions:
            changed["companions"] = companions

        transport = self._transport(text)
        if transport:
            changed["transport"] = transport

        preferences, excluded = self._preferences(text, current)
        if preferences:
            changed["preferences"] = preferences
        if excluded != list(current.get("excluded_preferences") or []):
            changed["excluded_preferences"] = excluded
        return changed

    def _duration(self, text):
        stay = re.search(r"(\d+)\s*박\s*(\d+)\s*일", text)
        if stay:
            return self._bounded_days(stay.group(2))
        if any(token in text for token in ["오늘만", "당일치기"]):
            return 1
        if re.search(r"(?:^|\s)오늘(?:\s|만|$)", text):
            return 1
        if "이번 주말" in text or "이번주말" in text:
            return 2
        return None

    def _relative_date(self, text, current, explicit_days):
        today = self.today_provider()
        start = None
        days = explicit_days

        if any(token in text for token in ["오늘", "오늘만", "당일치기", "이번 휴가", "이번휴가"]):
            start = today
            days = 1 if explicit_days is None else explicit_days
        elif "모레" in text:
            start = today + datetime.timedelta(days=2)
            days = days or (int(current.get("days")) if current.get("days") else 1)
        elif "내일" in text:
            start = today + datetime.timedelta(days=1)
            days = days or (int(current.get("days")) if current.get("days") else 1)
        elif "이번 주말" in text or "이번주말" in text:
            start = self._next_weekday(today, 5)
            days = 2
        elif "다음 주" in text or "다음주" in text:
            start = today + datetime.timedelta(days=(7 - today.weekday()))
            days = days or 7
        elif "다음 달" in text or "다음달" in text:
            start = self._first_day_next_month(today)
            days = days or (int(current.get("days")) if current.get("days") else 1)
        else:
            for label, weekday in self.WEEKDAYS.items():
                if label in text:
                    start = self._next_weekday(today, weekday)
                    days = days or (int(current.get("days")) if current.get("days") else 1)
                    break

        if start is None:
            current_start = self._iso_date(current.get("start_date"))
            if explicit_days and current_start:
                return {
                    "days": explicit_days,
                    "end_date": (current_start + datetime.timedelta(days=explicit_days - 1)).isoformat(),
                }
            return {}

        days = self._bounded_days(days or 1)
        return {
            "start_date": start.isoformat(),
            "end_date": (start + datetime.timedelta(days=days - 1)).isoformat(),
            "days": days,
        }

    def _absolute_date(self, text, current, explicit_days):
        today = self.today_provider()
        range_match = re.search(
            r"(?:(\d{4})년\s*)?(\d{1,2})월\s*(\d{1,2})일?\s*"
            r"(?:부터|에서|~|〜|-)\s*"
            r"(?:(\d{4})년\s*)?(\d{1,2})월\s*(\d{1,2})일?",
            text,
        )
        if range_match:
            start = self._calendar_date(
                range_match.group(1), range_match.group(2), range_match.group(3), today,
            )
            if start is None:
                return {}
            end_year = int(range_match.group(4)) if range_match.group(4) else start.year
            try:
                end = datetime.date(end_year, int(range_match.group(5)), int(range_match.group(6)))
                if not range_match.group(4) and end < start:
                    end = datetime.date(end_year + 1, end.month, end.day)
            except Exception:
                return {}
            days = self._bounded_days((end - start).days + 1)
            return {
                "start_date": start.isoformat(),
                "end_date": (start + datetime.timedelta(days=days - 1)).isoformat(),
                "days": days,
            }

        shorthand_range = re.search(
            r"(?:(\d{4})년\s*)?(\d{1,2})월\s*(\d{1,2})(?:일)?"
            r"(?:(?!\d{1,2}\s*월).){0,48}?(?:부터|에서|~|〜)\s*,?\s*"
            r"(\d{1,2})\s*일(?=.{0,48}?(?:까지|$))",
            text,
        )
        if shorthand_range:
            start = self._calendar_date(
                shorthand_range.group(1),
                shorthand_range.group(2),
                shorthand_range.group(3),
                today,
            )
            if start is None:
                return {}
            end = self._same_or_next_month_date(start, shorthand_range.group(4))
            if end is None:
                return {}
            days = self._bounded_days((end - start).days + 1)
            return {
                "start_date": start.isoformat(),
                "end_date": (start + datetime.timedelta(days=days - 1)).isoformat(),
                "days": days,
            }

        single = re.search(r"(?:(\d{4})년\s*)?(\d{1,2})월\s*(\d{1,2})일", text)
        if not single:
            return {}
        start = self._calendar_date(single.group(1), single.group(2), single.group(3), today)
        if start is None:
            return {}
        days = self._bounded_days(
            explicit_days or (int(current.get("days")) if current.get("days") else 1)
        )
        return {
            "start_date": start.isoformat(),
            "end_date": (start + datetime.timedelta(days=days - 1)).isoformat(),
            "days": days,
        }

    def _calendar_date(self, year, month, day, today):
        try:
            explicit_year = int(year) if year else None
            candidate = datetime.date(explicit_year or today.year, int(month), int(day))
            if explicit_year is None and candidate < today:
                candidate = datetime.date(today.year + 1, candidate.month, candidate.day)
            return candidate
        except Exception:
            return None

    def _same_or_next_month_date(self, start, day):
        try:
            end = datetime.date(start.year, start.month, int(day))
            if end >= start:
                return end
            if start.month == 12:
                return datetime.date(start.year + 1, 1, int(day))
            return datetime.date(start.year, start.month + 1, int(day))
        except Exception:
            return None

    def _companions(self, text):
        for label, aliases in self.COMPANION_ALIASES.items():
            if any(alias in text for alias in aliases):
                return [label]
        return []

    def _transport(self, text):
        if any(token in text for token in ["차 없이", "차없이", "걸어다닐래", "걸어 다닐래"]):
            return "대중교통"
        if any(token in text for token in ["렌트할 거야", "렌트할거야", "렌트할래", "렌터카", "렌트카"]):
            return "자동차"
        return ""

    def _preferences(self, text, current):
        preferences = list(current.get("preferences") or [])
        excluded = list(current.get("excluded_preferences") or [])
        for label, aliases in self.PREFERENCE_ALIASES.items():
            for alias in aliases:
                index = text.find(alias)
                if index < 0:
                    continue
                around = text[max(0, index - 8):index + len(alias) + 10]
                target = excluded if any(token in around for token in ["빼", "제외", "싫", "말고"]) else preferences
                if label not in target:
                    target.append(label)
                break
        excluded_set = set(excluded)
        return self._unique([item for item in preferences if item not in excluded_set]), self._unique(excluded)

    def _next_weekday(self, today, weekday):
        return today + datetime.timedelta(days=(weekday - today.weekday()) % 7)

    def _first_day_next_month(self, today):
        if today.month == 12:
            return datetime.date(today.year + 1, 1, 1)
        return datetime.date(today.year, today.month + 1, 1)

    def _iso_date(self, value):
        try:
            return datetime.date.fromisoformat(str(value or ""))
        except Exception:
            return None

    def _bounded_days(self, value):
        try:
            return max(1, min(int(value), 14))
        except Exception:
            return 1

    def _unique(self, values):
        rows = []
        for value in values:
            value = str(value or "").strip()
            if value and value not in rows:
                rows.append(value)
        return rows


Model = TravelNaturalLanguageUnderstanding
