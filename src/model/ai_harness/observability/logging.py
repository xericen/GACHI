import json
import uuid


class StructuredLogger:
    def __init__(self, sink=None):
        self.sink = sink

    def new_run_id(self):
        return uuid.uuid4().hex

    def emit(self, event, **fields):
        payload = {"event": str(event or "")}
        payload.update(fields)
        line = "[ai_harness] " + json.dumps(payload, ensure_ascii=False, default=str)
        try:
            if self.sink:
                self.sink(line)
            else:
                print(line)
        except Exception:
            pass


Model = StructuredLogger
