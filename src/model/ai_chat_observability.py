from collections import deque
import json
import threading
import time
import uuid


class ChatStabilizationMonitor:
    WINDOW_SECONDS = 15 * 60
    MIN_REQUESTS = 20
    RELATIVE_502_MULTIPLIER = 2.5
    ABSOLUTE_502_RATE = 0.10
    VALIDATION_502_RATE = 0.10
    VALIDATION_REASONS = {"validation_failed", "tool_budget_exceeded"}

    def __init__(self, sink=None, clock=None):
        self.sink = sink
        self.clock = clock or time.time
        self.samples = deque()
        self.lock = threading.Lock()
        self.alerting = False

    def record(self, executor, status_code, fallback_reason="", duration_ms=0):
        now = float(self.clock())
        sample = {
            "timestamp": now,
            "executor": str(executor or "unknown"),
            "status_code": int(status_code or 0),
            "fallback_reason": str(fallback_reason or "none"),
        }
        with self.lock:
            self.samples.append(sample)
            self._trim(now)
            snapshot = self._snapshot()
            should_alert = bool(snapshot["alert_reasons"])
            emit_alert = should_alert and not self.alerting
            self.alerting = should_alert

        self._emit({
            "event": "chat_request_finished",
            "request_id": uuid.uuid4().hex,
            "executor": sample["executor"],
            "status_code": sample["status_code"],
            "is_502": sample["status_code"] == 502,
            "fallback_reason": sample["fallback_reason"],
            "duration_ms": max(0, int(duration_ms or 0)),
            **snapshot,
        })
        if emit_alert:
            self._emit({"event": "chat_stabilization_alert", **snapshot})
        return snapshot

    def _trim(self, now):
        cutoff = now - self.WINDOW_SECONDS
        while self.samples and self.samples[0]["timestamp"] < cutoff:
            self.samples.popleft()

    def _snapshot(self):
        grouped = {"harness": [], "legacy": []}
        for sample in self.samples:
            grouped.setdefault(sample["executor"], []).append(sample)

        harness = grouped.get("harness", [])
        legacy = grouped.get("legacy", [])
        harness_502 = [row for row in harness if row["status_code"] == 502]
        legacy_502 = [row for row in legacy if row["status_code"] == 502]
        validation_502 = [
            row for row in harness_502
            if row["fallback_reason"] in self.VALIDATION_REASONS
        ]
        harness_rate = self._rate(len(harness_502), len(harness))
        legacy_rate = self._rate(len(legacy_502), len(legacy))
        validation_rate = self._rate(len(validation_502), len(harness))
        ratio = None if legacy_rate == 0 else round(harness_rate / legacy_rate, 4)

        reasons = []
        if len(harness) >= self.MIN_REQUESTS and harness_rate >= self.ABSOLUTE_502_RATE:
            reasons.append("harness_502_absolute_rate")
        if len(harness) >= self.MIN_REQUESTS and validation_rate >= self.VALIDATION_502_RATE:
            reasons.append("harness_validation_502_rate")
        if len(harness) >= self.MIN_REQUESTS and len(legacy) >= self.MIN_REQUESTS:
            relative_exceeded = (
                harness_rate >= self.ABSOLUTE_502_RATE
                if legacy_rate == 0
                else harness_rate >= legacy_rate * self.RELATIVE_502_MULTIPLIER
            )
            if relative_exceeded:
                reasons.append("harness_502_vs_legacy")

        return {
            "window_seconds": self.WINDOW_SECONDS,
            "minimum_requests": self.MIN_REQUESTS,
            "relative_502_multiplier": self.RELATIVE_502_MULTIPLIER,
            "absolute_502_rate_threshold": self.ABSOLUTE_502_RATE,
            "validation_502_rate_threshold": self.VALIDATION_502_RATE,
            "harness_requests": len(harness),
            "harness_502_count": len(harness_502),
            "harness_502_rate": harness_rate,
            "harness_validation_502_count": len(validation_502),
            "harness_validation_502_rate": validation_rate,
            "legacy_requests": len(legacy),
            "legacy_502_count": len(legacy_502),
            "legacy_502_rate": legacy_rate,
            "harness_to_legacy_502_ratio": ratio,
            "alert_reasons": reasons,
        }

    def _rate(self, numerator, denominator):
        return round(float(numerator) / denominator, 4) if denominator else 0.0

    def _emit(self, payload):
        line = "[ai_chat] " + json.dumps(payload, ensure_ascii=False, default=str)
        try:
            if self.sink:
                self.sink(line)
            else:
                print(line)
        except Exception:
            pass


Model = ChatStabilizationMonitor
