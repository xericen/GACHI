import math
import re


class Place:
    THEME_LIMIT_MAX = 80
    THEME_SAMPLE_LIMIT = 800
    SEARCH_FIELDS = ["name", "category", "description", "overview", "address", "area"]
    LOCATION_ALIASES = {
        "서울": ["서울", "성수", "종로", "익선동", "한강", "홍대"],
        "경기": ["경기", "수원", "가평", "양평", "파주", "용인", "고양"],
        "인천": ["인천", "송도", "월미도", "강화", "영종"],
        "강원": ["강원", "강릉", "속초", "춘천", "양양", "평창"],
        "충청": ["충청", "충남", "충북", "대전", "세종", "천안", "아산", "공주", "부여", "태안"],
        "전라": ["전라", "전북", "전남", "전주", "군산", "목포", "여수", "순천"],
        "경상": ["경상", "경북", "경남", "대구", "경주", "포항", "안동", "울산", "통영", "거제", "진주"],
        "부산": ["부산", "해운대", "광안리", "영도", "서면"],
        "제주": ["제주", "애월", "협재", "서귀포", "성산", "중문"],
    }

    CAFE_KEYWORDS = [
        "카페",
        "커피",
        "로스터리",
        "베이커리",
        "브런치",
        "디저트",
        "라떼",
    ]
    BEAUTY_KEYWORDS = [
        "미용",
        "뷰티",
        "헤어",
        "네일",
        "스파",
        "마사지",
        "올리브영",
        "코스메틱",
        "화장품",
    ]

    THEMES = [
        dict(
            key="sight",
            label="볼거리",
            keyword="명소",
            icon="fa-location-dot",
            tone="theme-blue",
            content_type_ids=["12", "14", "15", "25", "28"],
        ),
        dict(
            key="cafe",
            label="카페",
            keyword="카페",
            icon="fa-mug-saucer",
            tone="theme-rose",
            content_type_ids=["39"],
            include_keywords=CAFE_KEYWORDS,
        ),
        dict(
            key="beauty",
            label="미용",
            keyword="미용",
            icon="fa-spa",
            tone="theme-green",
            content_type_ids=["38"],
            include_keywords=BEAUTY_KEYWORDS,
        ),
        dict(
            key="stay",
            label="숙소",
            keyword="감성숙소",
            icon="fa-bed",
            tone="theme-sun",
            content_type_ids=["32"],
        ),
        dict(
            key="food",
            label="맛집",
            keyword="맛집",
            icon="fa-utensils",
            tone="theme-orange",
            content_type_ids=["39"],
            exclude_keywords=CAFE_KEYWORDS,
        ),
        dict(
            key="shopping",
            label="쇼핑",
            keyword="쇼핑",
            icon="fa-bag-shopping",
            tone="theme-slate",
            content_type_ids=["38"],
            exclude_keywords=BEAUTY_KEYWORDS,
        ),
    ]

    def __init__(self, core):
        self.core = core

    def db(self, name):
        return self.core.db(name)

    def _int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default

    def _float_or_none(self, value):
        if value in [None, ""]:
            return None
        try:
            return float(value)
        except Exception:
            return None

    def _distance_km(self, lat1, lng1, lat2, lng2):
        lat1 = self._float_or_none(lat1)
        lng1 = self._float_or_none(lng1)
        lat2 = self._float_or_none(lat2)
        lng2 = self._float_or_none(lng2)
        if None in [lat1, lng1, lat2, lng2]:
            return None
        radius = 6371
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlng / 2) ** 2
        )
        return radius * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

    def _clean(self, value, limit=120):
        text = re.sub(r"<[^>]*>", " ", str(value or ""))
        text = text.replace("&nbsp;", " ")
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > limit:
            return text[:limit].rstrip() + "..."
        return text

    def _keyword_condition(self, db, keywords, fields=None):
        condition = None
        fields = fields or self.SEARCH_FIELDS
        for field in fields:
            column = getattr(db, field)
            for keyword in keywords or []:
                part = column.is_null(False) & column.contains(keyword)
                condition = part if condition is None else condition | part
        return condition

    def _keyword_tokens(self, value):
        text = self._clean(value, 120)
        if not text:
            return []
        return [token for token in re.split(r"\s+", text) if token]

    def _location_keywords(self, location):
        value = self._clean(location, 80)
        if not value:
            return []
        if value in self.LOCATION_ALIASES:
            return [value]
        for region, aliases in self.LOCATION_ALIASES.items():
            if value in aliases:
                return [value]
        return [value]

    def _filter_condition(self, db, location="", search="", keyword=""):
        condition = None

        location_keywords = self._location_keywords(location)
        if location_keywords:
            location_condition = self._keyword_condition(
                db,
                location_keywords,
                fields=["area"]
            )
            condition = location_condition if condition is None else condition & location_condition

        search_keywords = self._keyword_tokens(search)
        keyword = self._clean(keyword, 80)
        if keyword and keyword not in ["여행", "데이트", "오늘", "이번주말"]:
            search_keywords.append(keyword)
        if search_keywords:
            search_condition = self._keyword_condition(db, search_keywords)
            condition = search_condition if condition is None else condition & search_condition

        return condition

    def _theme_condition(self, db, theme):
        condition = db.is_hidden == False
        content_type_ids = theme.get("content_type_ids") or []
        if content_type_ids:
            condition = condition & (db.content_type_id.in_(content_type_ids))

        include = self._keyword_condition(db, theme.get("include_keywords"))
        if include is not None:
            condition = condition & include

        exclude = self._keyword_condition(db, theme.get("exclude_keywords"))
        if exclude is not None:
            condition = condition & (~exclude)

        return condition

    def _summary(self, row):
        name = self._clean(row.get("name"), 80)
        for key in ["overview", "description"]:
            value = self._clean(row.get(key), 96)
            if value and value != name:
                return value
        address = self._clean(row.get("address"), 96)
        if address:
            return address
        return f"{row.get('area', '')} {row.get('category', '')}".strip()

    def _score(self, row):
        image = row.get("image") or row.get("first_image2")
        overview = self._clean(row.get("overview"), 80)
        name = self._clean(row.get("name"), 80)
        rating = self._float_or_none(row.get("google_rating")) or 0
        return (
            1 if image else 0,
            1 if overview and overview != name else 0,
            rating,
            self._int(row.get("google_user_ratings_total"), 0),
            str(row.get("updated", "")),
        )

    def _normalize(self, row, theme):
        rating = self._float_or_none(row.get("google_rating"))
        return dict(
            id=row.get("id", ""),
            tourapi_id=row.get("tourapi_id", ""),
            name=row.get("name", ""),
            title=row.get("name", ""),
            area=row.get("area", ""),
            category=row.get("category", ""),
            content_type_id=row.get("content_type_id", ""),
            address=row.get("address", ""),
            latitude=row.get("latitude", ""),
            longitude=row.get("longitude", ""),
            lat=row.get("latitude", ""),
            lng=row.get("longitude", ""),
            image=row.get("image") or row.get("first_image2", ""),
            summary=self._summary(row),
            rating=round(rating, 1) if rating is not None else None,
            user_ratings_total=self._int(row.get("google_user_ratings_total"), 0),
            usage_time=self._clean(row.get("usage_time"), 80),
            rest_date=self._clean(row.get("rest_date"), 80),
            theme_key=theme.get("key", ""),
            theme_label=theme.get("label", ""),
            theme_keyword=theme.get("keyword", theme.get("label", "")),
            theme_icon=theme.get("icon", ""),
            theme_tone=theme.get("tone", ""),
        )

    def _search_normalize(self, row, distance=None):
        rating = self._float_or_none(row.get("google_rating"))
        data = dict(
            id=row.get("id", ""),
            place_id=row.get("id", ""),
            name=row.get("name", ""),
            title=row.get("name", ""),
            area=row.get("area", ""),
            category=row.get("category", ""),
            address=row.get("address", ""),
            latitude=row.get("latitude", ""),
            longitude=row.get("longitude", ""),
            lat=row.get("latitude", ""),
            lng=row.get("longitude", ""),
            image=row.get("image") or row.get("first_image2", ""),
            summary=self._summary(row),
            rating=round(rating, 1) if rating is not None else None,
            user_ratings_total=self._int(row.get("google_user_ratings_total"), 0),
            distance_km=round(distance, 2) if distance is not None else None,
        )
        return data

    def nearby_search(self, lat="", lng="", keyword="", region="", limit=8):
        limit = max(1, min(self._int(limit, 8), 30))
        keyword = self._clean(keyword, 80)
        region = self._clean(region, 80)
        db = self.db("place").orm
        query = db.select().where(db.is_hidden == False)

        if keyword:
            condition = self._keyword_condition(db, [keyword], fields=["name", "address", "area", "category"])
            if condition is not None:
                query = query.where(condition)

        rows = []
        for row in query.order_by(db.updated.desc()).limit(200).dicts():
            row = dict(row)
            distance = self._distance_km(lat, lng, row.get("latitude"), row.get("longitude"))
            area = str(row.get("area", ""))
            same_region = 1 if region and (region in area or area in region) else 0
            name = str(row.get("name", ""))
            name_match = 1 if keyword and keyword in name else 0
            rows.append((row, distance, same_region, name_match))

        rows.sort(key=lambda item: (
            -item[3],
            -item[2],
            item[1] if item[1] is not None else 999999,
            -self._int(item[0].get("google_user_ratings_total"), 0),
            str(item[0].get("name", "")),
        ))
        return [self._search_normalize(row, distance) for row, distance, same_region, name_match in rows[:limit]]

    def themes(self, limit=6, location="", search="", keyword=""):
        limit = max(1, min(self._int(limit, 6), self.THEME_LIMIT_MAX))
        db = self.db("place").orm
        sections = []
        filter_condition = self._filter_condition(db, location, search, keyword)

        for theme in self.THEMES:
            condition = self._theme_condition(db, theme)
            if filter_condition is not None:
                condition = condition & filter_condition
            query = db.select().where(condition)
            count = query.count()
            rows = [
                dict(row)
                for row in query.order_by(
                    db.google_rating.desc(),
                    db.google_user_ratings_total.desc(),
                    db.updated.desc(),
                ).limit(self.THEME_SAMPLE_LIMIT).dicts()
            ]
            rows.sort(key=self._score, reverse=True)
            sections.append(dict(
                key=theme["key"],
                label=theme["label"],
                keyword=theme.get("keyword", theme["label"]),
                icon=theme["icon"],
                tone=theme["tone"],
                count=count,
                places=[self._normalize(row, theme) for row in rows[:limit]],
            ))

        return sections


Model = Place
