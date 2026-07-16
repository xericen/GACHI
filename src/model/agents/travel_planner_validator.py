import re

Types = wiz.model("ai_harness/types")


class ItineraryPlaceValidator:
    def check(self, reply, tool_logs):
        unknown = self._unknown_place_mentions(reply, tool_logs)
        if not unknown:
            return Types.ValidationResult(ok=True)
        return Types.ValidationResult(
            ok=False,
            code="unverified_place",
            correction_instruction=(
                "검증 실패: 방금 응답에 place_search 결과에 없는 장소명이 포함되었거나 "
                "장소 추천 전 place_search가 호출되지 않았습니다. "
                f"문제 항목: {', '.join(unknown)}. "
                "실제 tool_result에 있는 장소만 사용해서 다시 답하세요. "
                "tool_result가 없다면 찾지 못했다고 답하세요."
            ),
            details={"unknown_mentions": unknown},
        )

    def _unknown_place_mentions(self, reply, tool_logs):
        if not reply:
            return []
        used_search = any(log.call.name == "place_search" for log in tool_logs or [])
        looks_like = any(token in reply for token in ["[일정 제안]", "동선:", "장소 상세:", "맛집", "카페", "관광지"])
        if looks_like and not used_search:
            return ["place_search_missing"]

        allowed = self._allowed_names(tool_logs)
        if not allowed:
            return []
        candidates = [match.strip() for match in re.findall(r"\[([^\]|]{2,50})(?:\||\])", reply)]
        for line in reply.splitlines():
            match = re.match(r"\s*\d+\.\s*([^-|()]{2,50})", line)
            if match:
                candidates.append(match.group(1).strip())
        unknown = []
        for name in candidates:
            if name in ["일정 제안", "내 일정으로 가져오기"]:
                continue
            if not self._matches(name, allowed):
                unknown.append(name)
        return list(dict.fromkeys(unknown))

    def _allowed_names(self, tool_logs):
        names = []
        for log in tool_logs or []:
            if log.call.name != "place_search":
                continue
            for row in (log.result.data or {}).get("results", []) or []:
                name = str(row.get("name") or "").strip()
                if name:
                    names.append(name)
        return names

    def _matches(self, name, allowed):
        normalized = self._normalize(name)
        for item in allowed:
            target = self._normalize(item)
            if normalized == target or normalized in target or target in normalized:
                return True
        return False

    def _normalize(self, value):
        return re.sub(r"\s+", "", str(value or "").lower())


Model = ItineraryPlaceValidator
