import re


class TravelConditionValidation:
    """Validate travel inputs before either exposing readiness or querying places."""

    @staticmethod
    def is_location(value):
        if not isinstance(value, str):
            return False
        text = value.strip()
        if not text or text in {
            "미정", "모름", "모르겠어", "아직 모르겠어", "없음", "없어요", "어디든", "아무데나",
            "추천", "추천해줘", "도보", "자동차", "대중교통", "걸어서", "오늘", "내일", "모레",
            "당일", "당일치기", "하루", "오전", "오후",
        }:
            return False
        if re.fullmatch(r"(?:오늘|내일|모레)(?:만|은|는|이요|요|로)?(?:\s*(?:코스|일정))?(?:\s*(?:만들어\s*줘|짜\s*줘|해줘))?", text):
            return False
        if re.fullmatch(r"(?:(?:이번|다음)\s*(?:주|달|주말)|[월화수목금토일]요일)", text):
            return False
        if re.fullmatch(r"\d{4}[-./]\d{1,2}[-./]\d{1,2}(?:[T\s]+\d{1,2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})?)?", text):
            return False
        # Numeric dates, clock times and durations are conditions, never regions.
        if re.fullmatch(r"(?:오전|오후)?[\d\s./:~\-년월일박시분]+(?:동안|일정)?", text):
            return False
        return True

    @staticmethod
    def is_time(value):
        return bool(re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", str(value or "")))

    @classmethod
    def valid_window(cls, start, end):
        return cls.is_time(start) and cls.is_time(end) and start < end

    @staticmethod
    def extract_window(text):
        matches = list(re.finditer(
            r"(오전|오후|아침|저녁|밤)?\s*(\d{1,2})(?::([0-5]\d)|\s*시(?!간)(?:\s*([0-5]?\d)\s*분)?)",
            str(text or ""),
        ))
        if len(matches) != 2:
            return {}
        values = []
        period = ""
        for match in matches:
            period = match[1] or period
            hour = int(match[2])
            minute = int(match[3] or match[4] or 0)
            if hour > 23 or minute > 59:
                return {}
            if period in {"오후", "저녁", "밤"} and hour < 12:
                hour += 12
            elif period in {"오전", "아침"} and hour == 12:
                hour = 0
            values.append(f"{hour:02d}:{minute:02d}")
        return dict(zip(["arrival_time", "departure_time"], values))


Model = TravelConditionValidation
