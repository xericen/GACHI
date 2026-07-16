Types = wiz.model("ai_harness/types")


class InputNormalizer:
    def normalize(self, prompt, history, config):
        prompt = self._trim(prompt, config.max_prompt_chars)
        if not prompt:
            raise Types.InvalidInput("질문을 입력해주세요.")

        rows = list(history or [])[-max(0, int(config.history_window)):]
        normalized = []
        for row in rows:
            role = str(getattr(row, "role", "") or "").strip()
            if role not in ["user", "assistant"]:
                continue
            content = self._trim(getattr(row, "content", ""), config.max_history_message_chars)
            if not content:
                continue
            normalized.append(Types.Message(role=role, content=content))
        return Types.NormalizedInput(prompt=prompt, history=normalized)

    def _trim(self, value, limit):
        value = str(value or "").strip()
        limit = max(0, int(limit or 0))
        if limit and len(value) > limit:
            return value[:limit].rstrip()
        return value


Model = InputNormalizer
