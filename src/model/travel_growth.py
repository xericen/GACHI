import datetime
import hashlib
import json


class TravelGrowth:
    def __init__(self, core):
        self.core = core

    def db(self, name):
        db = self.core.db(name)
        if name in ["course_travel_review", "user_activity_event"]:
            db.orm.create_table(safe=True)
        return db

    def event_id(self, user_id, kind, course_id):
        return hashlib.sha256(f"{user_id}:{kind}:{course_id}".encode()).hexdigest()[:64]

    def event(self, user_id, kind, course_id):
        return self.db("user_activity_event").get(id=self.event_id(user_id, kind, course_id))

    def save_event(self, user_id, kind, course_id, meta):
        db = self.db("user_activity_event")
        eid = self.event_id(user_id, kind, course_id)
        data = dict(id=eid, user_id=user_id, event_type=kind, target_type="course", target_id=course_id,
                    title="", meta_json=json.dumps(meta, ensure_ascii=False), created=datetime.datetime.now())
        if db.get(id=eid):
            db.update(data, id=eid)
        else:
            db.insert(data)

    def accessible(self, user_id, course_id):
        course = self.core.course.get(course_id, include_places=False)
        if course:
            if str(course.get("user_id")) == user_id:
                return True
            if bool(course.get("is_hidden")):
                return False
            if bool(course.get("is_public")):
                return True
            return any(user_id in [str(a.get("owner_user_id")), str(a.get("applicant_user_id"))]
                       for a in self.db("companion_application").rows(course_id=course_id, status="accepted", dump=100))
        return bool(self.db("saved_course").get(user_id=user_id, course_id=course_id))

    def source_signature(self, execution):
        places = [{key: value for key, value in p.items()
                   if key not in ["checked", "checked_at", "checkin_method"]}
                  for p in execution.get("places") or []]
        return hashlib.sha256(json.dumps(places, sort_keys=True, default=str).encode()).hexdigest()

    def execution(self, user_id, course_id):
        if not user_id or not self.accessible(user_id, course_id):
            raise PermissionError("이 코스에 접근할 수 없습니다.")
        execution = self.core.course.execution(course_id, user_id)
        if not execution or not execution.get("places"):
            raise ValueError("방문할 장소가 없는 코스입니다.")
        plan = self.event(user_id, "travel_replan", course_id)
        if plan:
            try:
                stored = json.loads(plan["meta_json"])
                # A course edit invalidates an older replan.
                original_ids = [str(p.get("place_id")) for p in execution["places"]]
                if stored.get("original_ids") == original_ids and stored.get("source_signature") == self.source_signature(execution):
                    checks = self.core.course._execution_checkin_map(course_id, user_id)
                    execution["places"] = stored["places"]
                    for p in execution["places"]:
                        check = checks.get(p["place_id"], {})
                        p.update(checked=bool(check), checked_at=str(check.get("checked_at", "")),
                                 checkin_method=check.get("method", ""))
                    execution["progress"] = dict(total=len(execution["places"]),
                        checked=sum(bool(p.get("checked")) for p in execution["places"]))
            except (ValueError, KeyError, TypeError):
                pass
        for place in execution["places"]:
            row = self.db("place").get(id=place["place_id"]) or {}
            place.update(phone=str(row.get("phone") or row.get("infocenter") or place.get("phone") or ""),
                         rest_date=str(row.get("rest_date") or place.get("rest_date") or ""), day=place.get("day", 1),
                         date=place.get("date", ""))
        return execution

    def candidates(self, execution):
        region = str(execution["course"].get("region") or "").split()[0:1]
        rows = self.db("place").rows(is_hidden=False, dump=5000)
        result = []
        for row in rows:
            address = str(row.get("address") or row.get("area") or "")
            if region and region[0] not in address and region[0] not in str(row.get("area") or ""):
                continue
            place = self.core.course._execution_place_from_db(row, 1, {})
            place.update(phone=row.get("phone", ""), rest_date=row.get("rest_date", ""))
            result.append(place)
        return result

    def persist_replan(self, user_id, course_id, proposal):
        original = self.core.course.execution(course_id, user_id)
        self.save_event(user_id, "travel_replan", course_id, dict(
            original_ids=[str(p.get("place_id")) for p in original["places"]],
            source_signature=self.source_signature(original),
            places=proposal["execution"]["places"], changes=proposal["changes"]))

    def enabled(self, user_id):
        if not user_id:
            return False
        row = self.db("user_setting").get(user_id=user_id) or {}
        try:
            account = json.loads(row.get("account_json") or "{}")
        except (ValueError, TypeError):
            account = {}
        return account.get("personalizedRecommendations", True) is not False

    def signals(self, user_id):
        if not self.enabled(user_id):
            return dict(enabled=False, followed_authors=[], executed_courses=[], terms=[], reasons=[])
        follows = self.db("user_content_state").rows(user_id=user_id, content_type="author_follow",
                                                    state="active", dump=500)
        saved = self.db("saved_course").rows(user_id=user_id, orderby="created", order="DESC", dump=100)
        events = self.db("user_activity_event").rows(user_id=user_id, event_type="course_execute",
                                                   orderby="created", order="DESC", dump=100)
        visits = self.db("course_checkin").rows(user_id=user_id, orderby="checked_at", order="DESC", dump=500)
        executed = list(dict.fromkeys([r["target_id"] for r in events] + [r["course_id"] for r in visits]))[:100]
        terms = []
        for row in saved:
            terms.extend([row.get("location", ""), row.get("title", "")])
            try:
                route = json.loads(row.get("route_json") or "{}")
                terms.extend(route.get("tags") or [])
                terms.append(route.get("category", ""))
            except (ValueError, TypeError, AttributeError):
                pass
        for course_id in executed:
            course = self.core.course.get(course_id, include_places=False) or {}
            terms.extend([course.get("region", ""), course.get("category", "")])
            terms.extend(course.get("tags", []) if isinstance(course.get("tags"), list) else [])
        # Followed creators contribute category/tag affinities, not merely their own feed cards.
        for row in follows[:30]:
            for course in self.db("course").rows(user_id=row["content_id"], is_public=True,
                                                is_hidden=False, dump=10):
                terms.extend([course.get("region", ""), course.get("category", "")])
                try:
                    terms.extend(json.loads(course.get("tags") or "[]"))
                except (ValueError, TypeError):
                    pass
        terms = list(dict.fromkeys(str(t).strip()[:100] for t in terms if str(t or "").strip()))[:50]
        return dict(enabled=True, followed_authors=[r["content_id"] for r in follows],
                    executed_courses=executed, terms=terms,
                    reasons=["저장한 코스", "팔로우한 작성자", "시작한 여행 코스"])

    def completion(self, user_id, course_id):
        execution = self.execution(user_id, course_id)
        places = execution["places"]
        complete = bool(places) and all(p.get("checked") for p in places)
        return dict(complete=complete, total=len(places), checked=sum(bool(p.get("checked")) for p in places),
                    automatic=sum(p.get("checkin_method") == "auto" for p in places),
                    place_ids=[p["place_id"] for p in places])

    def review_targets(self, user_id, course_id):
        # Only accepted companions with completion records on both sides can review each other.
        own = self.completion(user_id, course_id)
        targets = []
        for application in self.db("companion_application").rows(course_id=course_id, status="accepted", dump=100):
            owner, applicant = str(application.get("owner_user_id") or ""), str(application.get("applicant_user_id") or "")
            target = applicant if user_id == owner else owner if user_id == applicant else ""
            if not target or target == user_id:
                continue
            try:
                finished = self.completion(target, course_id)["complete"]
            except (PermissionError, ValueError):
                finished = False
            user = self.core.user.get(target) or {}
            if finished and own["complete"]:
                targets.append(dict(id=target, name=user.get("name") or "동행자"))
        return list({t["id"]: t for t in targets}.values()), own

    def reviews(self, user_id, course_id):
        targets, completion = self.review_targets(user_id, course_id)
        rows = self.db("course_travel_review").rows(course_id=course_id, orderby="created", order="DESC", dump=100)
        reviews = []
        for row in rows:
            evidence = json.loads(row.get("evidence_json") or "{}")
            reviews.append(dict(id=row["id"], rating=row["rating"], comment=row["comment"],
                                reviewer_name=(self.core.user.get(row["reviewer_id"]) or {}).get("name") or "여행자",
                                target_name=(self.core.user.get(row["target_id"]) or {}).get("name") or "동행자",
                                automatic=evidence.get("automatic", 0), total=evidence.get("total", 0),
                                created=str(row["created"])))
        return dict(targets=targets, completion=completion, reviews=reviews,
                    average=round(sum(r["rating"] for r in rows) / len(rows), 1) if rows else None,
                    count=len(rows), evidence_label="양쪽 여행 완료·확정 동행 기록 확인 (수동 방문 포함)")

    def submit_review(self, user_id, course_id, target_id, rating, comment):
        targets, evidence = self.review_targets(user_id, course_id)
        if target_id not in {t["id"] for t in targets}:
            raise PermissionError("양쪽 모두 코스를 완료한 확정 동행자에게만 후기를 남길 수 있습니다.")
        rating = int(rating)
        comment = str(comment or "").strip()
        if not 1 <= rating <= 5 or not 1 <= len(comment) <= 1000:
            raise ValueError("별점 1~5점과 1~1000자 후기를 입력해주세요.")
        db = self.db("course_travel_review")
        rid = hashlib.sha256(f"{user_id}:{course_id}:{target_id}".encode()).hexdigest()
        data = dict(id=rid, reviewer_id=user_id, course_id=course_id, target_id=target_id,
                    rating=rating, comment=comment, evidence_json=json.dumps(evidence),
                    created=datetime.datetime.now())
        if db.get(id=rid):
            raise ValueError("이 여행의 해당 동행자에게 이미 후기를 남겼습니다.")
        db.insert(data)

    def trust(self, user_id):
        rows = self.db("course_travel_review").rows(target_id=user_id, dump=500)
        return dict(count=len(rows), average=round(sum(r["rating"] for r in rows) / len(rows), 1) if rows else None,
                    reviewers=len({r["reviewer_id"] for r in rows}),
                    evidence="양쪽 여행 완료·확정 동행 확인, 수동 방문 기록 포함",
                    warning="후기와 방문 기록은 안전을 보증하지 않습니다.")


Model = TravelGrowth
