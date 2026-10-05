import json
import time
import urllib.error
import urllib.request


class ExternalApiClient:
    """Small provider-neutral HTTP boundary with a stable result contract."""

    def __init__(self, opener=None):
        self.opener = opener or urllib.request.urlopen

    def get_json(self, provider, url, headers=None, timeout=8, max_bytes=4 * 1024 * 1024):
        return self._get(provider, url, headers, timeout, max_bytes, "json")

    def get_bytes(self, provider, url, headers=None, timeout=8, max_bytes=8 * 1024 * 1024):
        return self._get(provider, url, headers, timeout, max_bytes, "bytes")

    def _get(self, provider, url, headers, timeout, max_bytes, response_type):
        started = time.monotonic()
        request = urllib.request.Request(url, headers=dict(headers or {}), method="GET")
        try:
            with self.opener(request, timeout=max(1, min(int(timeout), 30))) as response:
                raw = response.read(max(1, int(max_bytes)) + 1)
                if len(raw) > max_bytes:
                    return self._result(provider, False, 502, None, "response_too_large", False, started)
                data = json.loads(raw.decode("utf-8")) if response_type == "json" else raw
                return self._result(provider, True, int(getattr(response, "status", 200) or 200), data, "", False, started)
        except urllib.error.HTTPError as error:
            retryable = int(error.code or 0) in [408, 425, 429, 500, 502, 503, 504]
            return self._result(provider, False, int(error.code or 502), None, f"http_{error.code}", retryable, started)
        except (urllib.error.URLError, TimeoutError):
            return self._result(provider, False, 502, None, "network_or_timeout", True, started)
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            return self._result(provider, False, 502, None, "invalid_response", False, started)

    def _result(self, provider, ok, status, data, error_code, retryable, started):
        return {
            "provider": str(provider or "unknown")[:40],
            "ok": bool(ok),
            "status": int(status or 0),
            "data": data,
            "error_code": str(error_code or "")[:80],
            "retryable": bool(retryable),
            "elapsed_ms": int((time.monotonic() - started) * 1000),
        }


Model = ExternalApiClient
