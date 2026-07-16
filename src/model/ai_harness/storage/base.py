class ConversationStore:
    def append_turn(self, thread_id, user_id, prompt, reply, seed_history):
        raise NotImplementedError

    def list(self, user_id, limit=30):
        raise NotImplementedError

    def get(self, thread_id, user_id):
        raise NotImplementedError


Model = ConversationStore
