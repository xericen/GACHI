import datetime
import hashlib
import json
import math
import uuid


class Zenly:
    REGION_ALIASES = {
        "서울": ["서울", "성수", "종로", "익선동", "한강", "홍대"],
        "경기": ["경기", "수원", "가평", "양평", "파주"],
        "인천": ["인천", "송도", "월미도"],
        "강원": ["강원", "강릉", "속초", "춘천", "양양"],
        "충청": ["충청", "충남", "충북", "대전", "세종", "공주", "태안"],
        "전라": ["전라", "전북", "전남", "전주", "여수", "군산"],
        "경상": ["경상", "경북", "경남", "대구", "경주", "통영"],
        "부산": ["부산", "해운대", "광안리"],
        "제주": ["제주", "애월", "협재", "서귀포"],
    }
    SIGNAL_TAGS = ["조용히", "활발하게", "카페", "맛집", "사진", "산책", "전시", "야경"]
    SIGNAL_DURATIONS = [30, 60, 180]
    DAILY_SIGNAL_LIMIT = 5
    SIGNAL_REPORT_RESTRICT_COUNT = 3

    def __init__(self, core):
        self.core = core

    def db(self, name):
        db = self.core.db(name)
        try:
            db.orm.create_table(safe=True)
        except Exception:
            pass
        return db

    def now(self):
        return datetime.datetime.now()

    def _id(self):
        return uuid.uuid4().hex[:32]

    def _clean(self, value, limit=120):
        text = " ".join(str(value or "").strip().split())
        if len(text) > limit:
            return text[:limit].rstrip()
        return text

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default

    def _safe_float(self, value, default=None):
        try:
            if value in [None, ""]:
                return default
            return float(value)
        except Exception:
            return default

    def _json_loads(self, value, fallback):
        try:
            parsed = json.loads(value or "")
            return parsed if parsed is not None else fallback
        except Exception:
            return fallback

    def _json_dumps(self, value):
        return json.dumps(value, ensure_ascii=False)

    def _parse_datetime(self, value):
        if isinstance(value, datetime.datetime):
            return value
        try:
            return datetime.datetime.fromisoformat(str(value))
        except Exception:
            return None

    def _hour_bucket(self, value=None):
        value = value or self.now()
        return value.replace(minute=0, second=0, microsecond=0)

    def _distance_meters(self, lat1, lng1, lat2, lng2):
        lat1 = self._safe_float(lat1)
        lng1 = self._safe_float(lng1)
        lat2 = self._safe_float(lat2)
        lng2 = self._safe_float(lng2)
        if None in [lat1, lng1, lat2, lng2]:
            return None
        radius = 6371000
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlng / 2) ** 2
        )
        return radius * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

    def _region_keywords(self, region):
        region = self._clean(region, 80)
        if not region or region in ["국내", "전체"]:
            return []
        if region in self.REGION_ALIASES:
            return self.REGION_ALIASES[region]
        for parent, aliases in self.REGION_ALIASES.items():
            if region in aliases:
                return [region, parent]
        return [region]

    def _place_query(self, region="", limit=80):
        db = self.db("place").orm
        query = db.select().where(db.is_hidden == False)
        keywords = self._region_keywords(region)
        condition = None
        for keyword in keywords:
            part = db.area.contains(keyword) | db.address.contains(keyword) | db.name.contains(keyword)
            condition = part if condition is None else condition | part
        if condition is not None:
            query = query.where(condition)
        return [
            dict(row)
            for row in query.order_by(db.google_rating.desc(), db.google_user_ratings_total.desc(), db.updated.desc()).limit(limit).dicts()
        ]

    def _place_by_id(self, place_id):
        place_id = self._clean(place_id, 64)
        if not place_id:
            return None
        return self.db("place").get(id=place_id)

    def _place_region(self, place, fallback=""):
        if not place:
            return self._clean(fallback, 100)
        text = self._clean(place.get("area") or place.get("address") or fallback, 100)
        return text or self._clean(fallback, 100)

    def _find_nearest_place(self, lat, lng, region="", max_meters=180):
        best = None
        for place in self._place_query(region, limit=120):
            distance = self._distance_meters(lat, lng, place.get("latitude"), place.get("longitude"))
            if distance is None:
                continue
            if best is None or distance < best[0]:
                best = (distance, place)
        if best is None or best[0] > max_meters:
            return None
        return best[1]

    def record_presence(self, place_id, region="", amount=1):
        place = self._place_by_id(place_id)
        if place is None:
            return None
        db = self.db("place_presence_log")
        now = self.now()
        bucket = self._hour_bucket(now)
        amount = max(1, min(self._safe_int(amount, 1), 20))
        current = db.get(place_id=place.get("id"), hour_bucket=bucket)
        if current:
            db.update(dict(
                count=max(0, self._safe_int(current.get("count"), 0)) + amount,
                region=self._place_region(place, region),
                updated_at=now,
            ), id=current["id"])
            return db.get(id=current["id"])
        row_id = self._id()
        db.insert(dict(
            id=row_id,
            place_id=place.get("id"),
            region=self._place_region(place, region),
            hour_bucket=bucket,
            count=amount,
            created_at=now,
            updated_at=now,
        ))
        return db.get(id=row_id)

    def record_presence_nearby(self, lat, lng, region="", radius=180):
        place = self._find_nearest_place(lat, lng, region, max_meters=self._safe_int(radius, 180))
        if place is None:
            return None
        return self.record_presence(place.get("id"), region=region, amount=1)

    def _seed_presence_places(self, region):
        spots = [
            ("카페거리", "카페", 31, 36, 8),
            ("산책길", "산책", 58, 44, 14),
            ("맛집 골목", "맛집", 48, 68, 21),
            ("사진 포인트", "명소", 72, 34, 5),
        ]
        label = self._clean(region, 40) or "성수"
        return [
            dict(
                place_id=f"seed-{label}-{index}",
                name=f"{label} {name}",
                category=category,
                area=label,
                count=count,
                badge=f"🔥{count}",
                level=self._presence_level(count),
                x=x,
                y=y,
                source="seed",
            )
            for index, (name, category, x, y, count) in enumerate(spots, start=1)
        ]

    def _presence_level(self, count):
        count = self._safe_int(count, 0)
        if count >= 18:
            return "busy"
        if count >= 7:
            return "normal"
        return "quiet"

    def _hash_position(self, key, index=0):
        digest = hashlib.md5(str(key or index).encode("utf-8")).hexdigest()
        x = 16 + (int(digest[:4], 16) % 68)
        y = 18 + (int(digest[4:8], 16) % 62)
        return dict(x=x, y=y)

    def _presence_place_payload(self, place, count, index):
        position = self._hash_position(place.get("id"), index)
        count = self._safe_int(count, 0)
        return dict(
            place_id=place.get("id", ""),
            name=place.get("name", ""),
            category=place.get("category", ""),
            area=place.get("area", ""),
            count=count,
            badge=f"🔥{count}",
            level=self._presence_level(count),
            x=position["x"],
            y=position["y"],
            source="log",
        )

    def heatmap(self, region="", limit=12):
        limit = max(4, min(self._safe_int(limit, 12), 40))
        bucket = self._hour_bucket()
        log_db = self.db("place_presence_log").orm
        log_rows = [
            dict(row)
            for row in log_db.select().where(log_db.hour_bucket == bucket).dicts()
        ]
        count_map = {row.get("place_id"): self._safe_int(row.get("count"), 0) for row in log_rows}
        places = self._place_query(region, limit=limit)
        rows = []
        for index, place in enumerate(places, start=1):
            rows.append(self._presence_place_payload(place, count_map.get(place.get("id"), 0), index))
        rows.sort(key=lambda item: item.get("count", 0), reverse=True)
        rows = rows[:limit]
        if not rows:
            rows = self._seed_presence_places(region)
        total = sum(self._safe_int(row.get("count"), 0) for row in rows)
        return dict(
            region=self._clean(region, 80) or "국내",
            regionTotal=total,
            banner=f"지금 {self._clean(region, 80) or '이 지역'}에 {total}명이 있어요",
            hourBucket=bucket.strftime("%Y-%m-%d %H:%M:%S"),
            privacy="개인 식별자 없이 장소별 시간대 집계만 사용합니다.",
            places=rows,
        )

    def hourly(self, place_id, hours=12):
        hours = max(6, min(self._safe_int(hours, 12), 48))
        place = self._place_by_id(place_id)
        now_bucket = self._hour_bucket()
        start = now_bucket - datetime.timedelta(hours=hours - 1)
        db = self.db("place_presence_log").orm
        rows = [
            dict(row)
            for row in db.select().where((db.place_id == place_id) & (db.hour_bucket >= start)).dicts()
        ]
        count_map = {
            self._parse_datetime(row.get("hour_bucket")).strftime("%Y-%m-%d %H:%M:%S"): self._safe_int(row.get("count"), 0)
            for row in rows
            if self._parse_datetime(row.get("hour_bucket"))
        }
        buckets = []
        for offset in range(hours):
            bucket = start + datetime.timedelta(hours=offset)
            key = bucket.strftime("%Y-%m-%d %H:%M:%S")
            buckets.append(dict(
                hour=key,
                label=bucket.strftime("%H시"),
                count=count_map.get(key, 0),
            ))
        return dict(
            place=dict(
                id=place.get("id", place_id) if place else place_id,
                name=place.get("name", "장소") if place else "장소",
                area=place.get("area", "") if place else "",
            ),
            buckets=buckets,
        )

    def _is_verified_user(self, user):
        if not user or not user.get("id"):
            return False
        if str(user.get("role", "")) == "admin":
            return True
        return bool(user.get("email") or user.get("mobile") or user.get("verified"))

    def _daily_signal_count(self, user_id):
        start = self.now().replace(hour=0, minute=0, second=0, microsecond=0)
        rows = self.db("signal").rows(user_id=user_id, dump=200)
        count = 0
        for row in rows:
            created = self._parse_datetime(row.get("created_at"))
            if created and created >= start:
                count += 1
        return count

    def _report_restricted(self, user_id):
        since = self.now() - datetime.timedelta(days=14)
        rows = self.db("signal_report").rows(reported_user_id=user_id, dump=200)
        count = 0
        for row in rows:
            created = self._parse_datetime(row.get("created_at"))
            if created and created >= since:
                count += 1
        return count >= self.SIGNAL_REPORT_RESTRICT_COUNT

    def _tags(self, value):
        tags = value
        if isinstance(tags, str):
            parsed = self._json_loads(tags, None)
            if isinstance(parsed, list):
                tags = parsed
            else:
                tags = value.split(",")
        if not isinstance(tags, list):
            tags = []
        result = []
        for tag in tags:
            tag = self._clean(tag, 16)
            if tag and tag not in result:
                result.append(tag)
        return result[:6]

    def expire_signals(self):
        now = self.now()
        db = self.db("signal").orm
        query = db.update(status="expired", updated_at=now).where((db.status == "active") & (db.expires_at <= now))
        try:
            query.execute()
        except Exception:
            pass

    def _signal_distance_label(self, distance):
        if distance is None:
            return "근처"
        if distance <= 300:
            return "300m 이내"
        if distance <= 500:
            return "500m 이내"
        if distance <= 1000:
            return "1km 이내"
        return f"{max(1, round(distance / 1000))}km 이내"

    def _remaining_label(self, expires_at):
        expires_at = self._parse_datetime(expires_at)
        if not expires_at:
            return ""
        minutes = max(0, int((expires_at - self.now()).total_seconds() // 60))
        if minutes < 60:
            return f"{minutes}분 남음"
        hours = minutes // 60
        rest = minutes % 60
        return f"{hours}시간 {rest}분 남음" if rest else f"{hours}시간 남음"

    def _signal_payload(self, row, viewer_user_id="", viewer_lat=None, viewer_lng=None, include_responses=False):
        distance = self._distance_meters(viewer_lat, viewer_lng, row.get("lat"), row.get("lng"))
        tags = self._json_loads(row.get("mood_tags"), [])
        signal = dict(
            id=row.get("id", ""),
            placeId=row.get("place_id", ""),
            message=row.get("message", ""),
            moodTags=tags if isinstance(tags, list) else [],
            rangeLabel=self._signal_distance_label(distance),
            fuzzyRadiusMeters=500 if distance is None or distance <= 500 else 1000,
            displayPosition=self._hash_position(row.get("id", "")),
            status=row.get("status", "active"),
            owned=bool(viewer_user_id and viewer_user_id == row.get("user_id")),
            reportCount=self._safe_int(row.get("report_count"), 0),
            remainingLabel=self._remaining_label(row.get("expires_at")),
            createdAt=str(row.get("created_at", "")),
            expiresAt=str(row.get("expires_at", "")),
        )
        if include_responses:
            response_rows = self.db("signal_response").rows(signal_id=row.get("id", ""), dump=100)
            signal["responses"] = [
                dict(
                    id=response.get("id", ""),
                    status=response.get("status", ""),
                    responderUserId=response.get("responder_user_id", ""),
                    createdAt=str(response.get("created_at", "")),
                    chatThreadId=response.get("chat_thread_id", ""),
                )
                for response in response_rows
            ]
        if viewer_user_id:
            response = self.db("signal_response").get(signal_id=row.get("id", ""), responder_user_id=viewer_user_id)
            signal["responseStatus"] = response.get("status", "") if response else ""
        return signal

    def create_signal(self, user, payload):
        if not self._is_verified_user(user):
            return 403, dict(message="본인인증 완료 계정만 신호를 보낼 수 있습니다.")
        user_id = user.get("id")
        if self._report_restricted(user_id):
            return 403, dict(message="신고 누적으로 신호 기능이 일시 제한되었습니다.")
        if self._daily_signal_count(user_id) >= self.DAILY_SIGNAL_LIMIT:
            return 429, dict(message=f"하루 신호는 {self.DAILY_SIGNAL_LIMIT}건까지 보낼 수 있습니다.")

        place_id = self._clean(payload.get("place_id") or payload.get("placeId"), 64)
        place = self._place_by_id(place_id)
        lat = self._safe_float(payload.get("lat"))
        lng = self._safe_float(payload.get("lng"))
        if place is not None:
            lat = self._safe_float(place.get("latitude"), lat)
            lng = self._safe_float(place.get("longitude"), lng)
        if lat is None or lng is None:
            return 400, dict(message="현재 위치나 곧 갈 장소를 선택해주세요.")

        message = self._clean(payload.get("message") or "근처에서 같이 이동할 분 있어요?", 50)
        duration = self._safe_int(payload.get("duration_minutes") or payload.get("duration"), 60)
        if duration not in self.SIGNAL_DURATIONS:
            duration = 60
        now = self.now()
        row_id = self._id()
        self.db("signal").insert(dict(
            id=row_id,
            user_id=user_id,
            place_id=place_id,
            lat=lat,
            lng=lng,
            message=message,
            mood_tags=self._json_dumps(self._tags(payload.get("mood_tags") or payload.get("moodTags"))),
            duration_minutes=duration,
            expires_at=now + datetime.timedelta(minutes=duration),
            status="active",
            matched_response_id="",
            report_count=0,
            created_at=now,
            updated_at=now,
        ))
        row = self.db("signal").get(id=row_id)
        return 200, dict(signal=self._signal_payload(row, user_id), dailyCount=self._daily_signal_count(user_id))

    def nearby_signals(self, lat=None, lng=None, radius=1500, user_id=""):
        self.expire_signals()
        radius = max(300, min(self._safe_int(radius, 1500), 5000))
        now = self.now()
        db = self.db("signal").orm
        rows = [
            dict(row)
            for row in db.select().where((db.status == "active") & (db.expires_at > now)).order_by(db.created_at.desc()).limit(80).dicts()
        ]
        result = []
        for row in rows:
            distance = self._distance_meters(lat, lng, row.get("lat"), row.get("lng"))
            if distance is not None and distance > radius:
                continue
            result.append(self._signal_payload(row, user_id, lat, lng, include_responses=bool(user_id and user_id == row.get("user_id"))))
        return dict(signals=result, privacy="정확한 좌표는 응답하지 않고 거리 범위와 흐릿한 반경만 제공합니다.")

    def respond_signal(self, signal_id, user):
        user_id = user.get("id", "") if user else ""
        if not user_id:
            return 401, dict(message="로그인이 필요합니다.")
        self.expire_signals()
        signal = self.db("signal").get(id=self._clean(signal_id, 32))
        if signal is None or signal.get("status") != "active":
            return 404, dict(message="응답 가능한 신호가 없습니다.")
        if signal.get("user_id") == user_id:
            return 400, dict(message="내가 보낸 신호에는 관심 표시를 할 수 없습니다.")
        response_db = self.db("signal_response")
        existing = response_db.get(signal_id=signal.get("id"), responder_user_id=user_id)
        if existing is not None:
            return 200, dict(response=existing, signal=self._signal_payload(signal, user_id), already=True)
        now = self.now()
        response_id = self._id()
        response_db.insert(dict(
            id=response_id,
            signal_id=signal.get("id"),
            responder_user_id=user_id,
            status="pending",
            chat_thread_id="",
            created_at=now,
            updated_at=now,
        ))
        return 200, dict(
            response=response_db.get(id=response_id),
            signal=self._signal_payload(signal, user_id),
            notification="신호 게시자에게 관심 알림을 보냈습니다.",
        )

    def update_response(self, signal_id, response_id, status, user):
        user_id = user.get("id", "") if user else ""
        if not user_id:
            return 401, dict(message="로그인이 필요합니다.")
        status = self._clean(status, 16)
        if status not in ["accepted", "declined"]:
            return 400, dict(message="응답 상태가 올바르지 않습니다.")
        signal_db = self.db("signal")
        response_db = self.db("signal_response")
        signal = signal_db.get(id=self._clean(signal_id, 32))
        response = response_db.get(id=self._clean(response_id, 32), signal_id=self._clean(signal_id, 32))
        if signal is None or response is None:
            return 404, dict(message="신호 응답을 찾을 수 없습니다.")
        if signal.get("user_id") != user_id:
            return 403, dict(message="내가 보낸 신호만 수락할 수 있습니다.")
        if signal.get("status") != "active" and status == "accepted":
            return 409, dict(message="이미 처리된 신호입니다.")

        now = self.now()
        chat_thread_id = response.get("chat_thread_id", "")
        if status == "accepted":
            chat_thread_id = self._create_match_chat(signal, response, user)
            response_db.update(dict(status="accepted", chat_thread_id=chat_thread_id, updated_at=now), id=response["id"])
            signal_db.update(dict(status="matched", matched_response_id=response["id"], updated_at=now), id=signal["id"])
            self._decline_other_responses(signal["id"], response["id"])
        else:
            response_db.update(dict(status="declined", updated_at=now), id=response["id"])
        signal = signal_db.get(id=signal["id"])
        response = response_db.get(id=response["id"])
        return 200, dict(
            signal=self._signal_payload(signal, user_id, include_responses=True),
            response=response,
            chatThreadId=chat_thread_id,
            notification="매칭 채팅방을 만들었습니다." if status == "accepted" else "응답을 거절했습니다.",
        )

    def _decline_other_responses(self, signal_id, accepted_response_id):
        response_db = self.db("signal_response").orm
        try:
            response_db.update(status="declined", updated_at=self.now()).where(
                (response_db.signal_id == signal_id)
                & (response_db.id != accepted_response_id)
                & (response_db.status == "pending")
            ).execute()
        except Exception:
            pass

    def _create_match_chat(self, signal, response, owner):
        chat_db = self.db("chat_thread")
        now = self.now()
        title = self._clean(f"동행 매칭 · {signal.get('message', '')}", 120)
        message = self._json_dumps([
            dict(
                role="assistant",
                text="동행 신호가 수락됐어요. 서로 동의하면 시간제한 위치공유를 켜고 만남 장소를 조율하세요.",
                created=now.strftime("%Y-%m-%d %H:%M:%S"),
            )
        ])
        thread_id = self._id()
        chat_db.insert(dict(
            id=thread_id,
            user_id=owner.get("id", ""),
            title=title,
            messages=message,
            created=now,
            updated=now,
        ))
        try:
            chat_db.insert(dict(
                id=self._id(),
                user_id=response.get("responder_user_id", ""),
                title=title,
                messages=message,
                created=now,
                updated=now,
            ))
        except Exception:
            pass
        return thread_id

    def report_signal(self, signal_id, user, reason=""):
        reporter_id = user.get("id", "") if user else ""
        if not reporter_id:
            return 401, dict(message="로그인이 필요합니다.")
        signal_db = self.db("signal")
        report_db = self.db("signal_report")
        signal = signal_db.get(id=self._clean(signal_id, 32))
        if signal is None:
            return 404, dict(message="신호를 찾을 수 없습니다.")
        if signal.get("user_id") == reporter_id:
            return 400, dict(message="내 신호는 신고할 수 없습니다.")
        existing = report_db.get(signal_id=signal.get("id"), reporter_user_id=reporter_id)
        if existing is None:
            report_db.insert(dict(
                id=self._id(),
                signal_id=signal.get("id"),
                reporter_user_id=reporter_id,
                reported_user_id=signal.get("user_id", ""),
                reason=self._clean(reason or "부적절한 신호", 120),
                created_at=self.now(),
            ))
        reports = report_db.count(signal_id=signal.get("id")) or 0
        updates = dict(report_count=reports, updated_at=self.now())
        if reports >= self.SIGNAL_REPORT_RESTRICT_COUNT:
            updates["status"] = "expired"
        signal_db.update(updates, id=signal.get("id"))
        signal = signal_db.get(id=signal.get("id"))
        return 200, dict(signal=self._signal_payload(signal, reporter_id), reportCount=reports)

    def match_badge(self, user_id):
        rows = self.db("signal").rows(user_id=user_id, status="matched", dump=500)
        count = len(rows)
        if count >= 10:
            label = "동행 마스터"
        elif count >= 3:
            label = "동행 메이커"
        elif count >= 1:
            label = "첫 동행 성공"
        else:
            label = ""
        return dict(matchCount=count, badge=label)


Model = Zenly
