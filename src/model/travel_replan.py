import copy
import datetime
import math
import re


def coordinate(place):
    try:
        lat, lng = float(place.get("lat")), float(place.get("lng"))
        if math.isfinite(lat) and math.isfinite(lng) and -90 <= lat <= 90 and -180 <= lng <= 180:
            return lat, lng
    except (TypeError, ValueError):
        pass
    return None


def distance(left, right):
    a, b = coordinate(left), coordinate(right)
    if a is None or b is None:
        return float("inf")
    lat1, lat2 = math.radians(a[0]), math.radians(b[0])
    dlat, dlng = lat2 - lat1, math.radians(b[1] - a[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(min(1, max(0, h))))


def indoors(place):
    text = str(place.get("category", "")) + " " + str(place.get("name", ""))
    if any(word in text for word in ["야외", "거리", "해변", "공원", "광장"]):
        return False
    return any(word in text for word in ["박물관", "미술관", "전시관", "전시장", "카페", "음식점", "식당", "실내", "도서관"])


def closed_today(place, today):
    # Only unambiguous dates/weekdays are detected; unknown hours are never guessed.
    rest = str(place.get("rest_date") or "")
    weekday = ["월", "화", "수", "목", "금", "토", "일"][today.weekday()] + "요일"
    return today.isoformat() in rest or rest.strip() == weekday or bool(re.search(r"매주\s*" + weekday + r"(?!\s*제외)", rest))


def build_replan(execution, candidates, fixed_ids=(), closed_ids=(), rain=False, delay=0, now=None):
    now = now or datetime.datetime.now()
    places = copy.deepcopy(execution.get("places") or [])
    fixed, closed = set(fixed_ids), set(closed_ids)
    ids = {str(p.get("place_id")) for p in places}
    if not fixed <= ids or not closed <= ids:
        raise ValueError("현재 일정에 없는 장소가 포함되어 있습니다.")
    delay = max(0, min(240, int(delay)))
    changes, warnings, used = [], [], set(ids)
    pending = [p for p in places if not p.get("checked")]
    if not pending:
        return dict(execution=execution, changes=[], warnings=["모든 방문이 완료된 코스입니다."], detected=[])
    active_day = (pending[0].get("day", 1), pending[0].get("date", ""))
    active_date = str(pending[0].get("date") or "")
    if active_date and active_date != now.date().isoformat():
        rain = False
        delay = 0
        warnings.append("다음 일정이 오늘이 아니므로 오늘 날씨·지연은 적용하지 않았습니다.")
    detected = []
    if rain:
        detected.append("강수 예보")
    if delay:
        detected.append(f"일정 지연 {delay}분")
    for index, place in enumerate(places):
        pid = str(place.get("place_id"))
        same_day = (place.get("day", 1), place.get("date", "")) == active_day
        unavailable = pid in closed or (same_day and closed_today(place, now.date()))
        if unavailable:
            detected.append(place.get("name", "") + " 휴무")
        protected = place.get("checked") or pid in fixed or not same_day
        if protected:
            if unavailable and not place.get("checked"):
                warnings.append(place.get("name", "") + ": 고정 장소가 휴무입니다. 고정을 해제하거나 직접 확인해주세요.")
            continue
        rain_affected = rain and not indoors(place)
        if unavailable or rain_affected:
            anchor = places[index - 1] if index else place
            options = [p for p in candidates if str(p.get("place_id")) not in used
                       and not closed_today(p, now.date()) and indoors(p)
                       and coordinate(p) and distance(anchor, p) <= 5000]
            if options:
                replacement = copy.deepcopy(min(options, key=lambda p: (distance(anchor, p), str(p.get("place_id")))))
                replacement.update(order=place.get("order", index + 1), visit_time=place.get("visit_time", ""),
                                   day=place.get("day", 1), date=place.get("date", ""), checked=False)
                places[index] = replacement
                used.add(str(replacement.get("place_id")))
                changes.append(dict(from_id=pid, to_id=replacement["place_id"], before=place["name"],
                                    after=replacement["name"], reason="휴무" if unavailable else "강수 예보: 실내 대안"))
            else:
                warnings.append(place.get("name", "") + ": 5km 안에 확인 가능한 실내 대안이 없어 원래 장소를 유지했습니다.")
    # Keep fixed/visited slots and days in place, and reorder only free blocks for delays.
    if delay:
        block = []
        def flush():
            if len(block) < 2:
                return
            pool = [places[i] for i in block]
            anchor = places[block[0] - 1] if block[0] else pool[0]
            for slot in block:
                chosen = min(pool, key=lambda p: (distance(anchor, p), str(p.get("place_id"))))
                pool.remove(chosen)
                places[slot] = chosen
                anchor = chosen
        previous_day = None
        for index, place in enumerate(places):
            day = (place.get("day", 1), place.get("date", ""))
            if previous_day is not None and previous_day != day:
                flush()
                block = []
            previous_day = day
            if place.get("checked") or str(place.get("place_id")) in fixed or day != active_day:
                flush()
                block = []
            else:
                block.append(index)
        flush()
        for index, (before, after) in enumerate(zip(execution.get("places") or [], places)):
            if before.get("place_id") != after.get("place_id"):
                changes.append(dict(before=before["name"], after=after["name"], reason=f"지연 {delay}분: 이동 동선 조정"))
        warnings.append("지연 재계획은 좌표 기반 동선 제안입니다. 이동시간·영업시간은 적용 후 다시 확인해주세요.")
    if delay:
        original_places = execution.get("places") or []
        for index, place in enumerate(places):
            if place.get("checked") or str(place.get("place_id")) in fixed:
                continue
            if (place.get("day", 1), place.get("date", "")) != active_day:
                continue
            original_time = str(original_places[index].get("visit_time") or "")
            if not re.fullmatch(r"\d{2}:\d{2}", original_time):
                continue
            try:
                hour, minute = map(int, original_time.split(":"))
                scheduled = datetime.datetime.combine(now.date(), datetime.time(hour, minute))
                shifted = scheduled + datetime.timedelta(minutes=delay)
            except ValueError:
                continue
            next_fixed = next((p for p in places[index+1:] if str(p.get("place_id")) in fixed
                               and (p.get("day", 1), p.get("date", "")) == active_day), None)
            fixed_time = str((next_fixed or {}).get("visit_time") or "")
            if shifted.date() != now.date() or (re.fullmatch(r"\d{2}:\d{2}", fixed_time)
                                               and shifted.strftime("%H:%M") >= fixed_time):
                warnings.append(place["name"] + ": 지연을 반영하면 고정 일정 또는 하루 범위를 넘겨 시간이 유지됩니다. 장소 수를 줄이거나 직접 조정해주세요.")
                continue
            new_time = shifted.strftime("%H:%M")
            place["visit_time"] = new_time
            changes.append(dict(before=place["name"] + " " + original_time,
                                after=place["name"] + " " + new_time, reason=f"지연 {delay}분: 예정 시각 조정"))
    for index, place in enumerate(places):
        place["order"] = index + 1
    result = copy.deepcopy(execution)
    result["places"] = places
    result["progress"] = dict(total=len(places), checked=sum(bool(p.get("checked")) for p in places))
    return dict(execution=result, changes=changes, warnings=warnings, detected=list(dict.fromkeys(detected)))


Model = build_replan
