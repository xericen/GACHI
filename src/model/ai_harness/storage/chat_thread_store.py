import datetime
import json

Types = wiz.model("ai_harness/types")


class ChatThreadStore:
    def __init__(self, db, clock=None):
        self.db = db
        self.clock = clock or datetime.datetime.now

    def append_turn(
        self, thread_id, user_id, prompt, reply, seed_history=None, travel_state=None,
        user_message_id="", response_message_id="", client_message_id="", request_id="",
    ):
        if not user_id:
            return None
        now = self._now()
        row = self.db.get(id=thread_id, user_id=user_id) if thread_id else None
        messages = self._parse_messages(row.get("messages", "[]")) if row else self._seed_messages(seed_history)
        if client_message_id and any(
            str(message.get("client_message_id") or "") == str(client_message_id)
            for message in messages
        ):
            return Types.StoreAppendResult(
                thread_id=str(row.get("id") or ""),
                title=str(row.get("title") or self._title(prompt)),
                is_new=False,
            )
        messages.append({
            "id": str(user_message_id or ""),
            "client_message_id": str(client_message_id or ""),
            "request_id": str(request_id or ""),
            "role": "user",
            "text": self._trim(prompt, 2000),
            "created": now,
        })
        messages.append({
            "id": str(response_message_id or ""),
            "client_message_id": str(client_message_id or ""),
            "request_id": str(request_id or ""),
            "role": "assistant",
            "text": self._trim(reply, 2000),
            "created": now,
        })
        messages = messages[-80:]

        title = row.get("title", "") if row else self._title(prompt)
        data = {
            "user_id": user_id,
            "title": title,
            "messages": json.dumps(messages, ensure_ascii=False),
            "travel_state": json.dumps(travel_state or self._parse_state(row.get("travel_state", "{}") if row else "{}"), ensure_ascii=False),
            "updated": now,
        }
        if row:
            self.db.update(data, id=row["id"], user_id=user_id)
            saved_id = row["id"]
            is_new = False
        else:
            data["created"] = now
            saved_id = self.db.insert(data)
            is_new = True
        return Types.StoreAppendResult(thread_id=str(saved_id or ""), title=title, is_new=is_new)

    def list(self, user_id, limit=30):
        if not user_id:
            return []
        rows = self.db.rows(
            user_id=user_id,
            orderby="updated",
            order="DESC",
            page=1,
            dump=max(1, int(limit or 30)),
        )
        return [self._summary(row) for row in rows]

    def get(self, thread_id, user_id):
        if not user_id or not thread_id:
            return None
        row = self.db.get(id=thread_id, user_id=user_id)
        if row is None:
            return None
        return {
            "id": row.get("id", ""),
            "title": row.get("title", ""),
            "messages": self._parse_messages(row.get("messages", "[]")),
            "travel_state": self._parse_state(row.get("travel_state", "{}")),
            "itinerary_draft": self._parse_state(row.get("travel_state", "{}")).get("itinerary_draft", {}),
            "created": str(row.get("created", "")),
            "updated": str(row.get("updated", "")),
        }

    def get_state(self, thread_id, user_id):
        if not user_id or not thread_id:
            return None
        row = self.db.get(id=thread_id, user_id=user_id)
        if row is None:
            return None
        return self._parse_state(row.get("travel_state", "{}"))

    def _summary(self, row):
        messages = self._parse_messages(row.get("messages", "[]"))
        preview = messages[-1].get("text", "") if messages else ""
        if len(preview) > 52:
            preview = preview[:52].rstrip() + "..."
        return {
            "id": row.get("id", ""),
            "title": row.get("title", "") or "새 여행 상담",
            "preview": preview,
            "message_count": len(messages),
            "created": str(row.get("created", "")),
            "updated": str(row.get("updated", "")),
        }

    def _seed_messages(self, history):
        rows = []
        for item in list(history or []):
            role = str(getattr(item, "role", "") or "").strip()
            text = self._trim(getattr(item, "content", ""), 2000)
            if role in ["user", "assistant"] and text:
                rows.append({"role": role, "text": text, "created": ""})
        return rows[-80:]

    def _parse_messages(self, raw):
        try:
            rows = json.loads(raw or "[]") if isinstance(raw, str) else raw
        except Exception:
            return []
        if not isinstance(rows, list):
            return []
        messages = []
        for row in rows[-80:]:
            if not isinstance(row, dict):
                continue
            role = str(row.get("role", "") or "").strip()
            text = self._trim(row.get("text", ""), 2000)
            if role not in ["user", "assistant"] or not text:
                continue
            messages.append({
                "id": str(row.get("id", "")),
                "client_message_id": str(row.get("client_message_id", "")),
                "request_id": str(row.get("request_id", "")),
                "role": role,
                "text": text,
                "created": str(row.get("created", "")),
            })
        return messages

    def _parse_state(self, raw):
        try:
            value = json.loads(raw or "{}") if isinstance(raw, str) else raw
        except Exception:
            return {}
        return value if isinstance(value, dict) else {}

    def _title(self, prompt):
        title = " ".join(str(prompt or "").strip().split())
        if len(title) > 36:
            title = title[:36].rstrip() + "..."
        return title or "새 여행 상담"

    def _trim(self, value, limit):
        value = str(value or "").strip()
        return value[:limit].rstrip() if len(value) > limit else value

    def _now(self):
        return self.clock().strftime("%Y-%m-%d %H:%M:%S")


Model = ChatThreadStore
