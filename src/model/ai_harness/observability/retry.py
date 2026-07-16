import random
import time


class RetryPolicy:
    def __init__(self, max_retries=2, base_delay=0.5, max_delay=4.0, jitter=0.15, sleep_fn=None, random_fn=None):
        self.max_retries = max(0, int(max_retries or 0))
        self.base_delay = max(0.0, float(base_delay or 0))
        self.max_delay = max(self.base_delay, float(max_delay or self.base_delay))
        self.jitter = max(0.0, float(jitter or 0))
        self.sleep_fn = sleep_fn or time.sleep
        self.random_fn = random_fn or random.random

    def run(self, operation, should_retry=None, on_retry=None):
        attempt = 0
        while True:
            try:
                return operation(attempt)
            except Exception as error:
                retryable = should_retry(error) if should_retry else bool(getattr(error, "retryable", False))
                if not retryable or attempt >= self.max_retries:
                    raise
                delay = min(self.max_delay, self.base_delay * (2 ** attempt))
                if self.jitter:
                    delay += self.random_fn() * self.jitter
                attempt += 1
                if on_retry:
                    on_retry(error, attempt, delay)
                self.sleep_fn(delay)


Model = RetryPolicy
