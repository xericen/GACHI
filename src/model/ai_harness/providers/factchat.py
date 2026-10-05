from dataclasses import dataclass
import copy
import json
import socket
import urllib.error
import urllib.request

Types = wiz.model("ai_harness/types")
BASE_URL = "https://factchat.mindlogic-kr-api.com/v1/gateway"


@dataclass
class FactChatProviderConfig:
    api_key: str
    model: str = "gpt-6-luna"
    timeout: int = 30
    max_output_tokens: int = 4096
    response_schema: dict = None


class FactChatProvider:
    def __init__(self, config):
        self.config = config
        self.model = config.model

    @staticmethod
    def _strict_schema(schema):
        # Strict output requires every property. Nullable optional slots mean
        # "unchanged"; the planner's existing type validation discards nulls.
        result = copy.deepcopy(schema)
        def normalize(node):
            if not isinstance(node, dict):
                return
            if node.get("type") == "object":
                properties = node.get("properties", {})
                required = set(node.get("required", []))
                node["additionalProperties"] = False
                for name, child in list(properties.items()):
                    normalize(child)
                    if name not in required:
                        properties[name] = {"anyOf": [child, {"type": "null"}]}
                node["required"] = list(properties)
            if isinstance(node.get("items"), dict):
                normalize(node["items"])
        normalize(result)
        return result

    def generate(self, messages, tools, system_prompt, stream=False):
        if stream or tools:
            raise Types.ProviderError("여행 채팅은 비스트리밍 조건 분석만 지원합니다.", status_code=400)
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}] + [
                {"role": message.role, "content": str(message.content or "")}
                for message in messages or [] if message.role in ["user", "assistant"]
            ],
            "stream": False,
            "store": False,
            "reasoning_effort": "low",
            "max_completion_tokens": self.config.max_output_tokens,
        }
        if self.config.response_schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "travel_planner",
                    "strict": True,
                    "schema": self._strict_schema(self.config.response_schema),
                },
            }
        request = urllib.request.Request(
            BASE_URL + "/chat/completions/",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-api-key": self.config.api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            status = int(error.code or 502)
            raise Types.ProviderError(
                "AI 인증 설정을 확인해주세요." if status in [401, 403] else "AI 응답 요청에 실패했습니다.",
                status_code=status, retryable=status == 429 or status >= 500,
            ) from None
        except (urllib.error.URLError, socket.timeout, TimeoutError):
            raise Types.ProviderError("AI 연결이 지연되고 있습니다.", status_code=502, retryable=True) from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise Types.ProviderError("AI 응답 형식이 올바르지 않습니다.", status_code=502) from None
        try:
            choice = data["choices"][0]
            content = choice["message"].get("content")
            if choice.get("finish_reason") != "stop" or not isinstance(content, str) or not content.strip():
                raise ValueError("incomplete response")
        except (KeyError, IndexError, TypeError, ValueError, AttributeError):
            raise Types.ProviderError("AI 응답이 완성되지 않았습니다.", status_code=502) from None
        return Types.ModelResponse(
            text=content.strip(), tool_calls=[], model=self.model,
            interaction_id=str(data.get("id") or ""), raw=data,
        )


class FactChat:
    Config = FactChatProviderConfig
    Provider = FactChatProvider


Model = FactChat
