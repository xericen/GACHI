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
            for row in query.order_by(db.provider_rating.desc(), db.provider_user_ratings_total.desc(), db.updated.desc()).limit(limit).dicts()
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
        self.expire_meetings()

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

    def _datetime_epoch_ms(self, value):
        value = self._parse_datetime(value)
        if not value:
            return 0
        try:
            return int(value.timestamp() * 1000)
        except Exception:
            return 0

    def _user_name(self, user_id, fallback="여행자"):
        try:
            user = self.core.user.get(user_id)
        except Exception:
            user = None
        return self._clean(user.get("name") if user else fallback, 30) or fallback

    def _meeting_time_label(self, value):
        value = self._parse_datetime(value)
        if not value:
            return "방금"
        period = "오전" if value.hour < 12 else "오후"
        return f"{period} {value.hour % 12 or 12}:{value.minute:02d}"

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
                    responderName=self._user_name(response.get("responder_user_id", ""), "관심 보낸 여행자"),
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
        self.core.mobile.enqueue_push(
            [signal.get("user_id", "")],
            "companion_request",
            "새 동행 신청",
            f"{self._user_name(user_id, '여행자')}님이 동행 신호에 관심을 보냈어요.",
            f"https://travel.wizide.com/access?tab=map&mapMode=zenly&focus=signals&signal={signal.get('id', '')}",
            dict(signal_id=signal.get("id", ""), response_id=response_id),
        )
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
        meeting_id = response.get("chat_thread_id", "")
        if status == "accepted":
            meeting = self._create_meeting(signal, response)
            meeting_id = meeting.get("id", "") if meeting else ""
            response_db.update(dict(status="accepted", chat_thread_id=meeting_id, updated_at=now), id=response["id"])
            signal_db.update(dict(status="matched", matched_response_id=response["id"], updated_at=now), id=signal["id"])
            self._decline_other_responses(signal["id"], response["id"])
            self.core.mobile.enqueue_push(
                [response.get("responder_user_id", "")],
                "companion_accepted",
                "동행 신청 수락",
                f"{self._user_name(user_id, '여행자')}님이 동행 신청을 수락했어요. 약속 채팅을 확인해보세요.",
                "https://travel.wizide.com/access?tab=map&mapMode=zenly&focus=meeting",
                dict(signal_id=signal.get("id", ""), meeting_id=meeting_id),
            )
        else:
            response_db.update(dict(status="declined", updated_at=now), id=response["id"])
        signal = signal_db.get(id=signal["id"])
        response = response_db.get(id=response["id"])
        meeting = self.db("signal_meeting").get(id=meeting_id) if meeting_id else None
        return 200, dict(
            signal=self._signal_payload(signal, user_id, include_responses=True),
            response=response,
            meeting=self._meeting_payload(meeting, user_id) if meeting else None,
            messages=self._meeting_messages_payload(meeting, user_id) if meeting else [],
            meetingId=meeting_id,
            notification="약속과 약속 채팅을 만들었습니다." if status == "accepted" else "응답을 거절했습니다.",
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

    def _create_meeting(self, signal, response):
        meeting_db = self.db("signal_meeting")
        message_db = self.db("signal_meeting_message")
        now = self.now()
        duration = self._safe_int(signal.get("duration_minutes"), 60)
        if duration not in self.SIGNAL_DURATIONS:
            duration = 60
        ends_at = now + datetime.timedelta(minutes=duration)
        place = self._place_by_id(signal.get("place_id", ""))
        location_label = self._clean(place.get("name") if place else "서로 정한 약속 장소", 100)
        title = self._clean(signal.get("message") or "주변 즉석 만남", 100)
        existing = meeting_db.get(signal_id=signal.get("id", ""))
        data = dict(
            signal_id=signal.get("id", ""),
            owner_user_id=signal.get("user_id", ""),
            responder_user_id=response.get("responder_user_id", ""),
            title=title,
            location_label=location_label,
            status="active",
            ends_at=ends_at,
            updated_at=now,
        )
        if existing is None:
            meeting_id = self._id()
            meeting_db.insert(dict(id=meeting_id, created_at=now, **data))
        else:
            meeting_id = existing.get("id", "")
            meeting_db.update(data, id=meeting_id)
            try:
                message_db.delete(meeting_id=meeting_id)
            except Exception:
                pass
        message_db.insert(dict(
            id=self._id(),
            meeting_id=meeting_id,
            sender_user_id="",
            message="약속 채팅이 열렸어요. 이 대화는 약속이 끝나면 자동으로 사라져요.",
            created_at=now,
        ))
        return meeting_db.get(id=meeting_id)

    def expire_meetings(self):
        now = self.now()
        meeting_db = self.db("signal_meeting")
        db = meeting_db.orm
        try:
            expired = [
                dict(row)
                for row in db.select().where((db.status == "active") & (db.ends_at <= now)).dicts()
            ]
        except Exception:
            expired = []
        for meeting in expired:
            meeting_db.update(dict(status="expired", updated_at=now), id=meeting.get("id", ""))
            try:
                self.db("signal").update(
                    dict(status="expired", updated_at=now),
                    id=meeting.get("signal_id", ""),
                    status="matched",
                )
            except Exception:
                pass
            try:
                self.db("signal_meeting_message").delete(meeting_id=meeting.get("id", ""))
                self.db("signal_meeting_message_receipt").delete(meeting_id=meeting.get("id", ""))
                self.db("together_location_state").delete(meeting_id=meeting.get("id", ""))
                self.db("together_location_consent").update(
                    dict(status="expired", updated_at=now),
                    meeting_id=meeting.get("id", ""),
                )
            except Exception:
                pass
        return len(expired)

    def _meeting_for_user(self, user_id, meeting_id=""):
        user_id = self._clean(user_id, 32)
        meeting_id = self._clean(meeting_id, 32)
        if not user_id:
            return None
        self.expire_meetings()
        db = self.db("signal_meeting").orm
        condition = (
            (db.status == "active")
            & (db.ends_at > self.now())
            & ((db.owner_user_id == user_id) | (db.responder_user_id == user_id))
        )
        if meeting_id:
            condition = condition & (db.id == meeting_id)
        try:
            row = db.select().where(condition).order_by(db.created_at.desc()).dicts().first()
            return dict(row) if row else None
        except Exception:
            return None

    def _meeting_payload(self, meeting, viewer_user_id):
        if not meeting:
            return None
        owner_id = meeting.get("owner_user_id", "")
        responder_id = meeting.get("responder_user_id", "")
        peer_id = responder_id if viewer_user_id == owner_id else owner_id
        return dict(
            id=meeting.get("id", ""),
            signalId=meeting.get("signal_id", ""),
            title=meeting.get("title", "주변 즉석 만남"),
            locationLabel=meeting.get("location_label", "서로 정한 약속 장소"),
            status=meeting.get("status", "active"),
            endsAt=str(meeting.get("ends_at", "")),
            endsAtEpoch=self._datetime_epoch_ms(meeting.get("ends_at")),
            remainingLabel=self._remaining_label(meeting.get("ends_at")),
            peerName=self._user_name(peer_id),
            peerUserKey=peer_id,
            ownRole="owner" if viewer_user_id == owner_id else "responder",
        )

    def _meeting_messages_payload(self, meeting, viewer_user_id):
        if not meeting:
            return []
        rows = self.db("signal_meeting_message").rows(
            meeting_id=meeting.get("id", ""),
            orderby="created_at",
            order="ASC",
            dump=200,
        )
        receipts = self.db("signal_meeting_message_receipt").rows(
            meeting_id=meeting.get("id", ""),
            dump=500,
        )
        receipt_by_message = {
            str(receipt.get("message_id") or ""): receipt
            for receipt in receipts
            if str(receipt.get("user_id") or "") != viewer_user_id
        }
        result = []
        for row in rows:
            sender_id = row.get("sender_user_id", "")
            role = "system" if not sender_id else "me" if sender_id == viewer_user_id else "other"
            receipt = receipt_by_message.get(str(row.get("id") or "")) if role == "me" else None
            result.append(dict(
                id=row.get("id", ""),
                role=role,
                senderName="안내" if role == "system" else "나" if role == "me" else self._user_name(sender_id),
                text=row.get("message", ""),
                timeLabel=self._meeting_time_label(row.get("created_at")),
                createdAt=str(row.get("created_at", "")),
                createdAtEpoch=self._datetime_epoch_ms(row.get("created_at")),
                read=bool(receipt),
                readAt=str(receipt.get("read_at") or "") if receipt else "",
            ))
        return result

    def _publish_meeting_realtime_event(self, meeting, event_type, payload):
        if not meeting:
            return None
        participants = [
            self._clean(meeting.get("owner_user_id", ""), 32),
            self._clean(meeting.get("responder_user_id", ""), 32),
        ]
        participants = [user_id for user_id in dict.fromkeys(participants) if user_id]
        event_payload = dict(payload or {})
        event_payload["meetingId"] = meeting.get("id", "")
        event_payload["participantKeys"] = participants
        event_db = self.db("companion_chat_event")
        event_db.insert(dict(
            event_type=self._clean(event_type, 32),
            post_id=self._clean(meeting.get("id", ""), 64),
            actor_user_id=self._clean(event_payload.get("senderKey", ""), 32),
            payload_json=json.dumps(event_payload, ensure_ascii=False, separators=(",", ":")),
            created=self.now(),
        ))
        return dict(
            event=event_type,
            participants=participants,
            payload={key: value for key, value in event_payload.items() if key != "participantKeys"},
        )

    def ensure_companion_meeting(self, application, post, user, duration_minutes=180, requested_ends_at=None):
        user_id = user.get("id", "") if user else ""
        if not user_id:
            return 401, dict(message="로그인이 필요합니다.")
        if not application or not post:
            return 404, dict(message="확정된 동행 여행을 찾을 수 없습니다.")
        owner_user_id = self._clean(application.get("owner_user_id", ""), 32)
        responder_user_id = self._clean(application.get("applicant_user_id", ""), 32)
        if user_id not in [owner_user_id, responder_user_id]:
            return 403, dict(message="확정된 동행자만 약속 채팅을 열 수 있습니다.")
        post_id = self._clean(application.get("post_id") or post.get("id"), 64)
        if not post_id:
            return 400, dict(message="동행 여행 정보를 확인할 수 없습니다.")

        meeting_db = self.db("signal_meeting")
        message_db = self.db("signal_meeting_message")
        signal_id = hashlib.sha256("companion:{}".format(post_id).encode("utf-8")).hexdigest()[:32]
        meeting = meeting_db.get(signal_id=signal_id)
        now = self.now()
        duration_minutes = max(30, min(self._safe_int(duration_minutes, 180), 4320))
        requested_ends_at = self._parse_datetime(requested_ends_at)
        maximum_ends_at = now + datetime.timedelta(days=30)
        if requested_ends_at and now + datetime.timedelta(minutes=30) <= requested_ends_at <= maximum_ends_at:
            meeting_ends_at_value = requested_ends_at
        else:
            meeting_ends_at_value = now + datetime.timedelta(minutes=duration_minutes)
        meeting_ends_at = self._parse_datetime(meeting.get("ends_at")) if meeting else None
        data = dict(
            signal_id=signal_id,
            owner_user_id=owner_user_id,
            responder_user_id=responder_user_id,
            title=self._clean(post.get("title") or post.get("destination") or "동행 여행", 100),
            location_label=self._clean(post.get("destination") or "준비방에서 정한 약속 장소", 100),
            status="active",
            ends_at=meeting_ends_at_value,
            updated_at=now,
        )
        should_seed = (
            meeting is None
            or meeting.get("status") != "active"
            or meeting_ends_at is None
            or meeting_ends_at <= now
        )
        if meeting is None:
            meeting_id = self._id()
            meeting_db.insert(dict(id=meeting_id, created_at=now, **data))
        else:
            meeting_id = meeting.get("id", "")
            if should_seed:
                message_db.delete(meeting_id=meeting_id)
            meeting_db.update(data, id=meeting_id)
        meeting = meeting_db.get(id=meeting_id)
        if should_seed:
            message_db.insert(dict(
                id=self._id(),
                meeting_id=meeting_id,
                sender_user_id="",
                message="약속 채팅이 열렸어요. 메시지는 동행자에게 실시간으로 전달돼요.",
                created_at=now,
            ))
        return 200, dict(
            meeting=self._meeting_payload(meeting, user_id),
            messages=self._meeting_messages_payload(meeting, user_id),
        )

    def _meeting_participant_ids(self, meeting):
        if not meeting:
            return []
        return [
            user_id for user_id in dict.fromkeys([
                self._clean(meeting.get("owner_user_id", ""), 32),
                self._clean(meeting.get("responder_user_id", ""), 32),
            ]) if user_id
        ]

    def _meeting_peer_user_id(self, meeting, user_id):
        participants = self._meeting_participant_ids(meeting)
        return next((value for value in participants if value != user_id), "")

    def _location_consent_id(self, meeting_id, user_id):
        return hashlib.sha256("{}:{}".format(meeting_id, user_id).encode("utf-8")).hexdigest()[:32]

    def _location_state_id(self, meeting_id, user_id):
        return hashlib.sha256("state:{}:{}".format(meeting_id, user_id).encode("utf-8")).hexdigest()[:32]

    def _expire_location_consents(self, meeting_id=""):
        now = self.now()
        consent_db = self.db("together_location_consent")
        state_db = self.db("together_location_state")
        rows = consent_db.rows(meeting_id=meeting_id, dump=20) if meeting_id else consent_db.rows(dump=500)
        for row in rows:
            expires_at = self._parse_datetime(row.get("expires_at"))
            if row.get("status") == "active" and (expires_at is None or expires_at <= now):
                consent_db.update(dict(status="expired", updated_at=now), id=row.get("id", ""))
                try:
                    state_db.delete(meeting_id=row.get("meeting_id", ""), user_id=row.get("user_id", ""))
                except Exception:
                    pass

    def _active_location_consent(self, meeting_id, user_id):
        self._expire_location_consents(meeting_id)
        row = self.db("together_location_consent").get(meeting_id=meeting_id, user_id=user_id)
        if not row or row.get("status") != "active":
            return None
        expires_at = self._parse_datetime(row.get("expires_at"))
        return row if expires_at and expires_at > self.now() else None

    def _location_consent_payload(self, consent):
        if not consent:
            return dict(active=False, duration="", expiresAt="", expiresAtEpoch=0, homeEnabled=True, stayEnabled=True)
        expires_at = self._parse_datetime(consent.get("expires_at"))
        return dict(
            active=consent.get("status") == "active" and bool(expires_at and expires_at > self.now()),
            duration=str(consent.get("share_duration") or ""),
            expiresAt=str(consent.get("expires_at") or ""),
            expiresAtEpoch=self._datetime_epoch_ms(consent.get("expires_at")),
            homeEnabled=bool(consent.get("home_enabled")),
            stayEnabled=bool(consent.get("stay_enabled")),
            homeConfigured=consent.get("home_lat") is not None and consent.get("home_lng") is not None,
            stayConfigured=consent.get("stay_lat") is not None and consent.get("stay_lng") is not None,
        )

    def _is_together_blocked(self, first_user_id, second_user_id):
        if not first_user_id or not second_user_id:
            return False
        db = self.db("together_user_block")
        return bool(
            db.get(blocker_user_id=first_user_id, blocked_user_id=second_user_id)
            or db.get(blocker_user_id=second_user_id, blocked_user_id=first_user_id)
        )

    def _inside_private_zone(self, consent, lat, lng):
        if not consent:
            return False
        zones = [
            ("home", bool(consent.get("home_enabled")), consent.get("home_lat"), consent.get("home_lng")),
            ("stay", bool(consent.get("stay_enabled")), consent.get("stay_lat"), consent.get("stay_lng")),
        ]
        for _, enabled, zone_lat, zone_lng in zones:
            if not enabled:
                continue
            if zone_lat is None or zone_lng is None:
                return True
            distance = self._distance_meters(lat, lng, zone_lat, zone_lng)
            if distance is not None and distance <= 300:
                return True
        return False

    def _masked_location(self, meeting_id, user_id, lat, lng):
        digest = hashlib.sha256("{}:{}:{}".format(meeting_id, user_id, self._hour_bucket()).encode("utf-8")).digest()
        lat_offset = ((digest[0] / 255.0) - 0.5) * 0.006
        lng_offset = ((digest[1] / 255.0) - 0.5) * 0.008
        return (
            max(-90, min(90, round(float(lat), 2) + lat_offset)),
            max(-180, min(180, round(float(lng), 2) + lng_offset)),
        )

    def _location_updated_label(self, value):
        value = self._parse_datetime(value)
        if not value:
            return "위치 확인 중"
        seconds = max(0, int((self.now() - value).total_seconds()))
        if seconds < 15:
            return "방금"
        if seconds < 60:
            return "{}초 전".format(seconds)
        return "{}분 전".format(max(1, seconds // 60))

    def location_snapshot(self, meeting_id, user):
        user_id = user.get("id", "") if user else ""
        if not user_id:
            return 401, dict(message="로그인이 필요합니다.")
        meeting = self._meeting_for_user(user_id, meeting_id)
        if meeting is None:
            return 410, dict(message="여행이 끝나 위치 공유도 종료됐습니다.", positions=[])
        meeting_id = meeting.get("id", "")
        self._expire_location_consents(meeting_id)
        consent_db = self.db("together_location_consent")
        state_db = self.db("together_location_state")
        viewer_consent = self._active_location_consent(meeting_id, user_id)
        positions = []
        for participant_id in self._meeting_participant_ids(meeting):
            if participant_id == user_id or self._is_together_blocked(user_id, participant_id):
                continue
            consent = self._active_location_consent(meeting_id, participant_id)
            state = state_db.get(meeting_id=meeting_id, user_id=participant_id)
            if not consent or not state:
                continue
            lat = self._safe_float(state.get("lat"))
            lng = self._safe_float(state.get("lng"))
            if lat is None or lng is None:
                continue
            private_zone = self._inside_private_zone(consent, lat, lng)
            precise = bool(viewer_consent and consent and not private_zone)
            display_lat, display_lng = (lat, lng) if precise else self._masked_location(meeting_id, participant_id, lat, lng)
            positions.append(dict(
                userKey=participant_id,
                name=self._user_name(participant_id, "동행자"),
                lat=display_lat,
                lng=display_lng,
                precise=precise,
                privateZone=private_zone,
                rangeMeters=0 if precise else 500,
                rangeLabel="실시간 위치 · 상호 동의" if precise else "약 500m 범위 · 보호됨",
                updatedAt=str(state.get("updated_at") or ""),
                updatedLabel=self._location_updated_label(state.get("updated_at")),
            ))
        return 200, dict(
            meeting=self._meeting_payload(meeting, user_id),
            consent=self._location_consent_payload(consent_db.get(meeting_id=meeting_id, user_id=user_id)),
            positions=positions,
        )

    def start_location_share(self, meeting_id, duration, home_enabled, stay_enabled, user):
        user_id = user.get("id", "") if user else ""
        if not user_id:
            return 401, dict(message="로그인이 필요합니다.")
        meeting = self._meeting_for_user(user_id, meeting_id)
        if meeting is None:
            return 410, dict(message="진행 중인 동행 여행이 없습니다.")
        duration = str(duration or "60")
        if duration not in ["30", "60", "trip"]:
            return 400, dict(message="위치 공개 시간이 올바르지 않습니다.")
        now = self.now()
        meeting_ends_at = self._parse_datetime(meeting.get("ends_at")) or now
        duration_ends_at = meeting_ends_at if duration == "trip" else now + datetime.timedelta(minutes=int(duration))
        expires_at = min(meeting_ends_at, duration_ends_at)
        if expires_at <= now:
            return 410, dict(message="여행이 끝나 위치를 공개할 수 없습니다.")
        db = self.db("together_location_consent")
        row = db.get(meeting_id=meeting.get("id", ""), user_id=user_id)
        data = dict(
            meeting_id=meeting.get("id", ""),
            user_id=user_id,
            status="active",
            share_duration=duration,
            expires_at=expires_at,
            home_enabled=bool(home_enabled),
            stay_enabled=bool(stay_enabled),
            updated_at=now,
        )
        if row is None:
            consent_id = self._location_consent_id(meeting.get("id", ""), user_id)
            db.insert(dict(id=consent_id, created_at=now, **data))
        else:
            db.update(data, id=row.get("id", ""))
        realtime = self._publish_meeting_realtime_event(
            meeting,
            "together_location_consent",
            dict(updatedUserKey=user_id, active=True),
        )
        status, payload = self.location_snapshot(meeting.get("id", ""), user)
        payload["_realtime"] = realtime
        return status, payload

    def stop_location_share(self, meeting_id, user):
        user_id = user.get("id", "") if user else ""
        if not user_id:
            return 401, dict(message="로그인이 필요합니다.")
        meeting = self._meeting_for_user(user_id, meeting_id)
        if meeting is None:
            return 404, dict(message="진행 중인 동행 여행이 없습니다.")
        now = self.now()
        db = self.db("together_location_consent")
        row = db.get(meeting_id=meeting.get("id", ""), user_id=user_id)
        if row:
            db.update(dict(status="ended", updated_at=now), id=row.get("id", ""))
        try:
            self.db("together_location_state").delete(meeting_id=meeting.get("id", ""), user_id=user_id)
        except Exception:
            pass
        realtime = self._publish_meeting_realtime_event(
            meeting,
            "together_location_consent",
            dict(updatedUserKey=user_id, active=False),
        )
        return 200, dict(stopped=True, consent=self._location_consent_payload(None), positions=[], _realtime=realtime)

    def update_location(self, meeting_id, lat, lng, accuracy, user):
        user_id = user.get("id", "") if user else ""
        if not user_id:
            return 401, dict(message="로그인이 필요합니다.")
        meeting = self._meeting_for_user(user_id, meeting_id)
        if meeting is None:
            return 410, dict(message="여행이 끝나 위치 공유도 종료됐습니다.")
        consent = self._active_location_consent(meeting.get("id", ""), user_id)
        if not consent:
            return 403, dict(message="위치 공개 동의가 만료되었거나 꺼져 있습니다.")
        lat = self._safe_float(lat)
        lng = self._safe_float(lng)
        accuracy = max(0, min(self._safe_float(accuracy, 0), 5000))
        if lat is None or lng is None or not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return 400, dict(message="위치 좌표가 올바르지 않습니다.")
        now = self.now()
        db = self.db("together_location_state")
        row = db.get(meeting_id=meeting.get("id", ""), user_id=user_id)
        data = dict(
            meeting_id=meeting.get("id", ""),
            user_id=user_id,
            lat=lat,
            lng=lng,
            accuracy=accuracy,
            updated_at=now,
        )
        if row is None:
            db.insert(dict(id=self._location_state_id(meeting.get("id", ""), user_id), created_at=now, **data))
        else:
            db.update(data, id=row.get("id", ""))
        realtime = self._publish_meeting_realtime_event(
            meeting,
            "together_location_update",
            dict(updatedUserKey=user_id, updatedAt=now.isoformat(timespec="seconds")),
        )
        status, payload = self.location_snapshot(meeting.get("id", ""), user)
        payload["_realtime"] = realtime
        return status, payload

    def set_private_zone(self, meeting_id, zone, enabled, lat, lng, user):
        user_id = user.get("id", "") if user else ""
        if not user_id:
            return 401, dict(message="로그인이 필요합니다.")
        meeting = self._meeting_for_user(user_id, meeting_id)
        if meeting is None:
            return 404, dict(message="진행 중인 동행 여행이 없습니다.")
        zone = self._clean(zone, 8)
        if zone not in ["home", "stay"]:
            return 400, dict(message="비공개 구역 종류가 올바르지 않습니다.")
        db = self.db("together_location_consent")
        row = db.get(meeting_id=meeting.get("id", ""), user_id=user_id)
        now = self.now()
        if row is None:
            row_id = self._location_consent_id(meeting.get("id", ""), user_id)
            db.insert(dict(
                id=row_id,
                meeting_id=meeting.get("id", ""),
                user_id=user_id,
                status="inactive",
                share_duration="60",
                expires_at=meeting.get("ends_at"),
                home_enabled=True,
                stay_enabled=True,
                created_at=now,
                updated_at=now,
            ))
            row = db.get(id=row_id)
        data = {"{}_enabled".format(zone): bool(enabled), "updated_at": now}
        lat = self._safe_float(lat)
        lng = self._safe_float(lng)
        if enabled and lat is not None and lng is not None and -90 <= lat <= 90 and -180 <= lng <= 180:
            data["{}_lat".format(zone)] = lat
            data["{}_lng".format(zone)] = lng
        db.update(data, id=row.get("id", ""))
        updated = db.get(id=row.get("id", ""))
        realtime = self._publish_meeting_realtime_event(
            meeting,
            "together_location_consent",
            dict(updatedUserKey=user_id, active=updated.get("status") == "active"),
        )
        return 200, dict(consent=self._location_consent_payload(updated), _realtime=realtime)

    def block_together_user(self, meeting_id, blocked_user_id, user):
        user_id = user.get("id", "") if user else ""
        meeting = self._meeting_for_user(user_id, meeting_id) if user_id else None
        blocked_user_id = self._clean(blocked_user_id, 32)
        if not user_id or meeting is None or blocked_user_id != self._meeting_peer_user_id(meeting, user_id):
            return 403, dict(message="동행 참가자만 차단할 수 있습니다.")
        db = self.db("together_user_block")
        if db.get(blocker_user_id=user_id, blocked_user_id=blocked_user_id) is None:
            db.insert(dict(
                id=hashlib.sha256("block:{}:{}".format(user_id, blocked_user_id).encode("utf-8")).hexdigest()[:32],
                blocker_user_id=user_id,
                blocked_user_id=blocked_user_id,
                created_at=self.now(),
            ))
        self.stop_location_share(meeting.get("id", ""), user)
        realtime = self._publish_meeting_realtime_event(
            meeting,
            "together_participant_blocked",
            dict(blockerUserKey=user_id, blockedUserKey=blocked_user_id),
        )
        return 200, dict(blocked=True, blockedUserKey=blocked_user_id, _realtime=realtime)

    def report_together_user(self, meeting_id, reported_user_id, reason, user):
        user_id = user.get("id", "") if user else ""
        meeting = self._meeting_for_user(user_id, meeting_id) if user_id else None
        reported_user_id = self._clean(reported_user_id, 32)
        if not user_id or meeting is None or reported_user_id != self._meeting_peer_user_id(meeting, user_id):
            return 403, dict(message="동행 참가자만 신고할 수 있습니다.")
        db = self.db("together_user_report")
        existing = db.get(
            meeting_id=meeting.get("id", ""),
            reporter_user_id=user_id,
            reported_user_id=reported_user_id,
        )
        if existing is None:
            db.insert(dict(
                id=self._id(),
                meeting_id=meeting.get("id", ""),
                reporter_user_id=user_id,
                reported_user_id=reported_user_id,
                reason=self._clean(reason or "같이 지도 안전 신고", 200),
                created_at=self.now(),
            ))
        return 200, dict(reported=True, reportedUserKey=reported_user_id)

    def active_meeting(self, user):
        user_id = user.get("id", "") if user else ""
        if not user_id:
            return 401, dict(message="로그인이 필요합니다.")
        meeting = self._meeting_for_user(user_id)
        return 200, dict(
            meeting=self._meeting_payload(meeting, user_id),
            messages=self._meeting_messages_payload(meeting, user_id),
        )

    def meeting_messages(self, meeting_id, user):
        user_id = user.get("id", "") if user else ""
        if not user_id:
            return 401, dict(message="로그인이 필요합니다.")
        meeting = self._meeting_for_user(user_id, meeting_id)
        if meeting is None:
            return 404, dict(message="진행 중인 약속 채팅이 없습니다.", meeting=None, messages=[])
        return 200, dict(
            meeting=self._meeting_payload(meeting, user_id),
            messages=self._meeting_messages_payload(meeting, user_id),
        )

    def send_meeting_message(self, meeting_id, message, user):
        user_id = user.get("id", "") if user else ""
        if not user_id:
            return 401, dict(message="로그인이 필요합니다.")
        meeting = self._meeting_for_user(user_id, meeting_id)
        if meeting is None:
            return 410, dict(message="약속이 끝나 채팅도 닫혔습니다.", meeting=None, messages=[])
        message = self._clean(message, 80)
        if not message:
            return 400, dict(message="메시지를 입력해주세요.")
        now = self.now()
        message_id = self._id()
        self.db("signal_meeting_message").insert(dict(
            id=message_id,
            meeting_id=meeting.get("id", ""),
            sender_user_id=user_id,
            message=message,
            created_at=now,
        ))
        peer_user_id = (
            meeting.get("responder_user_id", "")
            if user_id == meeting.get("owner_user_id", "")
            else meeting.get("owner_user_id", "")
        )
        self.core.mobile.enqueue_push(
            [peer_user_id],
            "meeting_message",
            self._user_name(user_id, "동행자"),
            message,
            "https://travel.wizide.com/access?tab=map&mapMode=zenly&focus=meeting",
            dict(meeting_id=meeting.get("id", ""), signal_id=meeting.get("signal_id", "")),
        )
        realtime = self._publish_meeting_realtime_event(
            meeting,
            "together_meeting_message",
            dict(
                id=message_id,
                senderKey=user_id,
                senderName=self._user_name(user_id, "동행자"),
                text=message,
                timeLabel=self._meeting_time_label(now),
                createdAt=now.isoformat(timespec="seconds"),
                createdAtEpoch=self._datetime_epoch_ms(now),
            ),
        )
        return 200, dict(
            meeting=self._meeting_payload(meeting, user_id),
            messages=self._meeting_messages_payload(meeting, user_id),
            _realtime=realtime,
        )

    def mark_meeting_messages_read(self, meeting_id, user):
        user_id = user.get("id", "") if user else ""
        if not user_id:
            return 401, dict(message="로그인이 필요합니다.")
        meeting = self._meeting_for_user(user_id, meeting_id)
        if meeting is None:
            return 404, dict(message="진행 중인 약속 채팅이 없습니다.")
        message_db = self.db("signal_meeting_message")
        receipt_db = self.db("signal_meeting_message_receipt")
        rows = message_db.rows(meeting_id=meeting.get("id", ""), orderby="created_at", order="ASC", dump=200)
        now = self.now()
        message_ids = []
        for row in rows:
            message_id = str(row.get("id") or "")
            sender_id = str(row.get("sender_user_id") or "")
            if not message_id or not sender_id or sender_id == user_id:
                continue
            receipt_id = hashlib.sha256("{}:{}".format(message_id, user_id).encode("utf-8")).hexdigest()
            if receipt_db.get(id=receipt_id) is not None:
                continue
            receipt_db.insert(dict(
                id=receipt_id,
                meeting_id=meeting.get("id", ""),
                message_id=message_id,
                user_id=user_id,
                read_at=now,
            ))
            message_ids.append(message_id)
        realtime = None
        if message_ids:
            realtime = self._publish_meeting_realtime_event(
                meeting,
                "together_meeting_read",
                dict(readerKey=user_id, messageIds=message_ids, readAt=now.isoformat(timespec="seconds")),
            )
        return 200, dict(messageIds=message_ids, readAt=now.isoformat(timespec="seconds"), _realtime=realtime)

    def meeting_typing(self, meeting_id, typing, user):
        user_id = user.get("id", "") if user else ""
        if not user_id:
            return 401, dict(message="로그인이 필요합니다.")
        meeting = self._meeting_for_user(user_id, meeting_id)
        if meeting is None:
            return 404, dict(message="진행 중인 약속 채팅이 없습니다.")
        realtime = self._publish_meeting_realtime_event(
            meeting,
            "together_meeting_typing",
            dict(userKey=user_id, typing=bool(typing)),
        )
        return 200, dict(typing=bool(typing), _realtime=realtime)

    def end_meeting(self, meeting_id, user):
        user_id = user.get("id", "") if user else ""
        if not user_id:
            return 401, dict(message="로그인이 필요합니다.")
        meeting = self._meeting_for_user(user_id, meeting_id)
        if meeting is None:
            return 404, dict(message="진행 중인 약속이 없습니다.")
        now = self.now()
        realtime = self._publish_meeting_realtime_event(
            meeting,
            "together_meeting_ended",
            dict(endedBy=user_id),
        )
        self.db("signal_meeting").update(dict(status="ended", updated_at=now), id=meeting.get("id", ""))
        try:
            self.db("signal").update(
                dict(status="expired", updated_at=now),
                id=meeting.get("signal_id", ""),
                status="matched",
            )
        except Exception:
            pass
        self.db("signal_meeting_message").delete(meeting_id=meeting.get("id", ""))
        try:
            self.db("signal_meeting_message_receipt").delete(meeting_id=meeting.get("id", ""))
            self.db("together_location_state").delete(meeting_id=meeting.get("id", ""))
            self.db("together_location_consent").update(
                dict(status="ended", updated_at=now),
                meeting_id=meeting.get("id", ""),
            )
        except Exception:
            pass
        return 200, dict(
            ended=True,
            meetingId=meeting.get("id", ""),
            messages=[],
            _realtime=realtime,
        )

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
