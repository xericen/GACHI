from dataclasses import dataclass
import json
import socket
import urllib.error
import urllib.request

Types = wiz.model("ai_harness/types")


@dataclass
class GeminiProviderConfig:
    api_key: str
    model: str
    endpoint: str = "https://generativelanguage.googleapis.com/v1beta/interactions"
    timeout: int = 30
    temperature: float = 0.45
    max_output_tokens: int = 900


class GeminiProvider:
    def __init__(self, config):
        self.config = config
        self.model = config.model

    def generate(self, messages, tools, system_prompt, stream=False):
        if stream:
            raise Types.ProviderError("스트리밍은 아직 지원하지 않습니다.", status_code=400)
        payload = {
            "model": self.config.model,
            "store": False,
            "input": self._serialize_messages(messages),
            "tools": list(tools or []),
            "system_instruction": system_prompt,
            "generation_config": {
                "temperature": self.config.temperature,
                "max_output_tokens": self.config.max_output_tokens,
            },
        }
        request = urllib.request.Request(
            self.config.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.config.api_key,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            status = int(error.code or 502)
            raise Types.ProviderError(
                self._http_error_message(error),
                status_code=status,
                retryable=status == 429 or status >= 500,
            )
        except (urllib.error.URLError, socket.timeout, TimeoutError) as error:
            raise Types.ProviderError(
                "Gemini API 연결에 실패했습니다.",
                status_code=502,
                retryable=True,
                reason=str(error),
            )
        except json.JSONDecodeError as error:
            raise Types.ProviderError(
                "Gemini API 응답 형식이 올바르지 않습니다.",
                status_code=502,
                retryable=False,
                reason=str(error),
            )
        return Types.ModelResponse(
            text=self._extract_reply(data),
            tool_calls=self._extract_function_calls(data),
            model=self.config.model,
            interaction_id=str(data.get("id") or ""),
            raw=data,
        )

    def _serialize_messages(self, messages):
        steps = []
        for message in messages or []:
            role = str(getattr(message, "role", "") or "")
            if role == "provider_step":
                raw = dict(getattr(message, "raw", {}) or {})
                if raw:
                    steps.append(raw)
            elif role == "function_result":
                steps.append({
                    "type": "function_result",
                    "name": str(getattr(message, "name", "") or ""),
                    "call_id": str(getattr(message, "call_id", "") or ""),
                    "result": [{"type": "text", "text": str(getattr(message, "content", "") or "{}")}],
                })
            else:
                content = str(getattr(message, "content", "") or "")
                if role == "assistant":
                    content = "AI: " + content
                steps.append({"type": "user_input", "content": content})
        return steps

    def _extract_function_calls(self, data):
        calls = []
        for step in data.get("steps", []) or []:
            if step.get("type") != "function_call":
                continue
            name = str(step.get("name") or "").strip()
            if not name:
                continue
            calls.append(Types.ToolCall(
                id=str(step.get("id") or step.get("call_id") or "").strip(),
                name=name,
                arguments=self._parse_arguments(step.get("arguments", {})),
            ))
        return calls

    def _parse_arguments(self, value):
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, dict) else {}
            except Exception:
                return {}
        return {}

    def _extract_reply(self, data):
        parts = []
        for step in data.get("steps", []) or []:
            if step.get("type") in ["thought", "function_call"]:
                continue
            content = step.get("content")
            if isinstance(content, str) and content.strip():
                parts.append(content.strip())
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
                        parts.append(str(item.get("text")).strip())
            text = step.get("text")
            if text:
                parts.append(str(text).strip())
        if parts:
            return "\n\n".join(parts).strip()
        output = data.get("output_text") or data.get("outputText")
        return str(output).strip() if output else ""

    def _http_error_message(self, error):
        try:
            raw = error.read().decode("utf-8")
            data = json.loads(raw)
            message = data.get("error", {}).get("message") or data.get("message")
            if message:
                return str(message)
        except Exception:
            pass
        return "Gemini API 호출에 실패했습니다."


class Gemini:
    Config = GeminiProviderConfig
    Provider = GeminiProvider


Model = Gemini
