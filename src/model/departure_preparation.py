import datetime
import hashlib
import json
import re

SOURCE = "https://www.0404.go.kr/main/mainPage"
GROUPS = ["미리 확인할 때", "폰 켠 김에", "짐 쌀 때"]
FIELDS = ["country", "transit", "nationality", "passport", "communication", "payment", "insurance"]
DEPENDENCIES = {
    "entry": ["country", "transit", "nationality", "passport", "start", "end"],
    "arrival": ["country", "transit", "nationality", "start", "end"],
    "passport": ["passport", "end"],
    "esim": ["country", "communication", "start", "end"],
    "money": ["country", "payment"],
    "insurance": ["country", "insurance", "start", "end"],
    "customs": ["country", "transit"],
    "schedule": ["start", "end", "destination"],
}


def date_value(value):
    try:
        return datetime.date.fromisoformat(str(value or "")[:10]).isoformat()
    except ValueError:
        return ""


def trip_context(source):
    route = source.get("route") or {}
    if isinstance(route, str):
        route = {}
    days = route.get("days") or []
    places = source.get("places") or []
    dates = sorted(filter(None, [date_value(item.get("date")) for item in days + places if isinstance(item, dict)]))
    start = date_value(source.get("start_date") or route.get("start_date") or (dates[0] if dates else ""))
    end = date_value(source.get("end_date") or route.get("end_date") or (dates[-1] if dates else start))
    schedule = str(route.get("schedule") or source.get("date") or source.get("duration") or "")
    iso_dates = re.findall(r"\d{4}-\d{2}-\d{2}", schedule)
    if not start and iso_dates:
        start = date_value(iso_dates[0])
        end = date_value(iso_dates[-1])
    return dict(title=source.get("title") or "여행", destination=source.get("location") or source.get("region") or route.get("region") or "",
                start=start, end=end, country=source.get("country") or route.get("country") or "")


def normalize_profile(raw):
    if not isinstance(raw, dict):
        raise ValueError("개인 조건 형식을 확인해주세요.")
    data = {key: str(raw.get(key) or "").strip()[:80] for key in FIELDS}
    if not data["country"] or not data["nationality"]:
        raise ValueError("목적지 국가와 본인의 국적을 확인해주세요.")
    if not data["transit"]:
        raise ValueError("경유 국가 또는 '없음'을 입력해주세요.")
    options = {"passport": ["ready", "check"], "communication": ["esim", "roaming", "ready"],
               "payment": ["cash", "card", "ready"], "insurance": ["needed", "ready", "skip"]}
    for key, allowed in options.items():
        if data[key] not in allowed:
            raise ValueError("부족한 개인 준비 조건을 확인해주세요.")
    data["start"] = date_value(raw.get("start"))
    data["end"] = date_value(raw.get("end"))
    if not data["start"] or not data["end"] or data["end"] < data["start"]:
        raise ValueError("유효한 여행 시작일과 종료일을 확인해주세요.")
    data["share"] = raw.get("share") is True
    data["reminders"] = raw.get("reminders") is True
    return data


def generate(trip, profile, previous=None, today=None):
    today = today or datetime.date.today()
    conditions = dict(profile, destination=trip.get("destination", ""))
    old = previous or {}
    old_items = {item["id"]: item for item in old.get("items", [])}
    old_conditions = old.get("conditions") or {}
    country = profile["country"]
    overseas = country not in ["대한민국", "한국", "KR", "Korea", "South Korea"]
    specs = [("schedule", "공통", "여행 날짜와 이동 일정 확인", 1, 1, "동행과 출발 날짜·약속 장소를 확인하세요.", "저장된 여행 일정", "")]
    if overseas:
        specs += [
            ("entry", "개인", "비자·입국 조건 확인", 0, 30, f'{profile["nationality"]} 국적 · {country} 방문 · 경유 {profile["transit"]}. 목적지와 경유국 공식 기관에서 본인에게 적용되는 조건을 확인하세요.', "외교부 해외안전여행 · 목적지/경유국 공식 기관 확인 필요", SOURCE),
            ("arrival", "개인", "입국신고 대상·제출 시점 확인", 1, 3, f"{country}의 공식 입국 안내에서 신고 대상과 제출 가능 시점을 확인하세요.", "목적지 공식 입국 안내 확인 필요", SOURCE),
            ("passport", "개인", "여권 유효기간·원본 확인", 0, 30, "체류 종료일 기준 여권 조건을 확인하세요. 여권 번호는 수집하지 않습니다.", "목적지 공식 입국 안내 확인 필요", SOURCE),
            ("customs", "공통", "반입 금지·제한 품목 확인", 2, 1, f'{country} · 경유 {profile["transit"]}: 의약품·식품·배터리 등의 조건을 세관과 항공사에서 확인하세요.', "목적지/경유국 세관 · 이용 항공사 확인 필요", SOURCE),
        ]
        if profile["communication"] != "ready":
            specs.append(("esim", "개인", "eSIM 확인" if profile["communication"] == "esim" else "로밍 확인", 1, 7, "사용 기간·지원 기기·통신사 조건을 확인하고 개통 방법을 저장하세요.", "본인 통신 선택 · 통신사 안내", ""))
        if profile["payment"] != "ready":
            specs.append(("money", "개인", "환전 준비" if profile["payment"] == "cash" else "해외 결제 설정 확인", 1, 7, "수수료·결제 가능 여부와 필요한 현금을 확인하세요.", "본인 결제 선택 · 금융기관 안내", ""))
        if profile["insurance"] == "needed":
            specs.append(("insurance", "개인", "여행 보험 준비", 1, 7, "여행 기간·보장 범위와 연락처를 확인하세요.", "본인 보험 선택 · 보험사 약관", ""))
    items = []
    for key, scope, label, group, lead, reason, evidence, url in specs:
        fingerprint = hashlib.sha256(json.dumps({name: conditions.get(name) for name in DEPENDENCIES[key]}, sort_keys=True).encode()).hexdigest()
        prior = old_items.get(key, {})
        changed = bool(prior and prior.get("fingerprint") != fingerprint)
        done = bool(prior.get("done")) and not changed
        if key == "passport" and not prior and profile["passport"] == "ready":
            done = True
        items.append(dict(id=key, scope=scope, label=label, group=GROUPS[group], lead=lead,
                          due=(datetime.date.fromisoformat(profile["start"]) - datetime.timedelta(days=lead)).isoformat(),
                          reason=reason, evidence=evidence, url=url, done=done, recheck=changed or (bool(prior.get("recheck")) and not done), fingerprint=fingerprint))
    delta = (datetime.date.fromisoformat(profile["start"]) - today).days
    return dict(conditions=conditions, items=items, dday=f"D-{delta}" if delta > 0 else ("D-day" if delta == 0 else f"D+{-delta}"),
                changed=[item["id"] for item in items if item["recheck"]])


class Preparation:
    def __init__(self, core):
        self.core = core

    def context(self, source):
        return trip_context(source)

    def db(self):
        db = self.core.db("departure_preparation")
        db.orm.create_table(safe=True)
        return db

    def record_id(self, scope, user):
        return hashlib.sha256(f"{scope}:{user}".encode()).hexdigest()[:32]

    def load(self, scope, user):
        row = self.db().get(id=self.record_id(scope, user))
        return json.loads(row["data"]) if row else {}

    def save(self, scope, user, data):
        db = self.db()
        values = dict(scope=scope, user_id=user, data=json.dumps(data, ensure_ascii=False), updated=datetime.datetime.now())
        key = self.record_id(scope, user)
        with db.orm._meta.database.atomic():
            db.orm.insert(id=key, **values).on_conflict_ignore().execute()
            db.orm.update(**values).where(db.orm.id == key).execute()

    def plan(self, trip, old, profile=None):
        if profile is None and not old.get("profile"):
            return dict(trip=trip, profile={}, items=[], shared=[], reminders=[])
        profile = normalize_profile(profile if profile is not None else old["profile"])
        # Dates and country from the saved itinerary override cached conditions.
        for key in ["start", "end", "country"]:
            if trip.get(key):
                profile[key] = trip[key]
        if profile["end"] < profile["start"]:
            raise ValueError("저장된 일정의 종료일을 확인해주세요.")
        plan = generate(trip, profile, old)
        reminders = []
        read = old.get("read_reminders") or []
        for days in [30, 7, 1]:
            due = (datetime.date.fromisoformat(profile["start"]) - datetime.timedelta(days=days)).isoformat()
            key = f'{profile["start"]}:{days}'
            reminders.append(dict(id=key, due=due, label=f"D-{days} 출발 준비 확인", read=key in read,
                                  active=profile["reminders"] and due <= datetime.date.today().isoformat() <= profile["start"]))
        return dict(**plan, trip=trip, profile=profile, reminders=reminders, read_reminders=read)

    def refresh_course(self, course_id, source):
        scopes = ["course:" + course_id]
        posts = self.core.db("community_post").rows(kind="companion", place=course_id)
        contexts = {}
        for post in posts:
            scope = "room:" + str(post["id"])
            scopes.append(scope)
            details = json.loads(post.get("poll") or "{}")
            room_source = dict(source)
            if date_value(details.get("date")):
                room_source["start_date"] = details["date"]
                room_source["end_date"] = details.get("endDate") or details["date"]
            contexts[scope] = trip_context(room_source)
        table = self.db()
        for row in table.orm.select().where(table.orm.scope.in_(scopes)).dicts():
            old = json.loads(row["data"])
            if not old.get("profile"):
                continue
            plan = self.plan(contexts.get(row["scope"]) or trip_context(source), old)
            self.save(row["scope"], row["user_id"], plan)
            self.schedule(row["scope"], row["user_id"], plan)

    def schedule(self, scope, user, data):
        jobs = self.core.db("mobile_push_job")
        jobs.orm.create_table(safe=True)
        prefix = self.record_id(scope, user)
        # Cancel obsolete unsent jobs before reserving the current dates.
        jobs.orm.update(status="cancelled", updated_at=datetime.datetime.now()).where(
            (jobs.orm.user_id == user) & (jobs.orm.event_type == "departure") &
            (jobs.orm.payload.contains(prefix)) & (jobs.orm.status.in_(["queued", "retry"]))
        ).execute()
        if not data.get("profile", {}).get("reminders"):
            return
        devices = self.core.db("mobile_device").rows(user_id=user, enabled=True, platform="ios")
        for reminder in data.get("reminders", []):
            if reminder["due"] < datetime.date.today().isoformat():
                continue
            for device in devices:
                key = hashlib.sha256(f'{prefix}:{reminder["id"]}:{device["device_token"]}'.encode()).hexdigest()[:32]
                current = jobs.get(id=key)
                if current and current["status"] not in ["cancelled"]:
                    continue
                now = datetime.datetime.now()
                values = dict(user_id=user, device_token=device["device_token"], event_type="departure",
                    title="GACHI 출발준비", body=reminder["label"], deep_link="/access",
                    payload=json.dumps(dict(preparation=prefix, scope=scope)), status="queued", attempts=0,
                    available_at=datetime.datetime.combine(datetime.date.fromisoformat(reminder["due"]), datetime.time(9)),
                    last_error="", created_at=now, updated_at=now, sent_at=None)
                if current:
                    jobs.update(values, id=key)
                else:
                    jobs.insert(dict(id=key, **values))


Model = Preparation
