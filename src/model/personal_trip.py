import datetime
import hashlib


def date_value(value):
    try:
        return datetime.date.fromisoformat(str(value or "")[:10]).isoformat()
    except ValueError:
        return ""


class PersonalTrip:
    def __init__(self, core):
        self.core = core

    def db(self):
        db = self.core.db("personal_trip")
        db.orm.create_table(safe=True)
        return db

    def record_id(self, user_id, course_id):
        return hashlib.sha256(f"{user_id}:{course_id}".encode()).hexdigest()[:32]

    def get(self, user_id, trip_id=""):
        if not user_id:
            return None
        if trip_id:
            return self.db().get(id=trip_id, user_id=user_id)
        rows = self.db().rows(user_id=user_id, orderby="updated", order="DESC", dump=20)
        return next((row for row in rows if row.get("status") in ["planned", "active"]), rows[0] if rows else None)

    def save(self, user_id, course, start_date="", end_date="", source="mine"):
        if not user_id or not course or not course.get("id"):
            raise ValueError("여행할 코스를 선택해주세요.")
        start = date_value(start_date)
        end = date_value(end_date)
        if (start_date or end_date) and (not start or not end or end < start):
            raise ValueError("유효한 여행 시작일과 종료일을 선택해주세요.")
        course_id = str(course["id"])
        trip_id = self.record_id(user_id, course_id)
        db = self.db()
        current = db.get(id=trip_id)
        now = datetime.datetime.now()
        values = dict(
            user_id=user_id,
            course_id=course_id,
            course_source=source if source in ["mine", "saved", "companion"] else "mine",
            title=str(course.get("title") or "내 여행")[:200],
            location=str(course.get("location") or course.get("region") or "")[:100],
            start_date=start or (current or {}).get("start_date", ""),
            end_date=end or (current or {}).get("end_date", ""),
            status="active" if current and current.get("status") == "active" else "planned",
            updated=now,
        )
        if current:
            db.update(values, id=trip_id)
        else:
            db.insert(dict(id=trip_id, created=now, **values))
        return db.get(id=trip_id)

    def set_status(self, user_id, trip_id, status):
        if status not in ["planned", "active", "completed"]:
            raise ValueError("지원하지 않는 여행 상태입니다.")
        row = self.get(user_id, trip_id)
        if row is None:
            raise ValueError("내 여행을 찾지 못했습니다.")
        self.db().update(dict(status=status, updated=datetime.datetime.now()), id=row["id"])
        return self.db().get(id=row["id"])


Model = PersonalTrip
