"""Compatibility entry point for the server-owned FactChat travel planner."""

TravelPlannerAgent = wiz.model("agents/travel_planner")


class AiChat:
    def __init__(self):
        self.agent = TravelPlannerAgent(wiz)

    def send(self, prompt, history_raw="[]", user_id="", thread_id=""):
        return self.agent.send(prompt, history_raw, user_id, thread_id)

    def admin_settings(self):
        return self.agent.admin_settings()

    def update_admin_settings(self, data):
        return self.agent.update_admin_settings(data)

    def threads(self, user_id, limit=30):
        return self.agent.threads(user_id, limit)

    def thread(self, user_id, thread_id):
        return self.agent.thread(user_id, thread_id)

    def delete_thread(self, user_id, thread_id):
        return self.agent.delete_thread(user_id, thread_id)

    def _save_thread(self, user_id, thread_id, prompt, reply, history_raw):
        saved = self.agent.store.append_turn(
            thread_id, user_id, prompt, reply, self.agent.history_decoder.decode(history_raw),
        )
        return {"thread_id": saved.thread_id, "title": saved.title, "is_new": saved.is_new}


Model = AiChat
