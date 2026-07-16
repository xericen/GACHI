from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class Message:
    role: str
    content: str = ""
    call_id: str = ""
    name: str = ""
    raw: dict = field(default_factory=dict)

    @staticmethod
    def provider_step(step):
        return Message(role="provider_step", raw=dict(step or {}))

    @staticmethod
    def function_result(call, result):
        return Message(
            role="function_result",
            call_id=call.id,
            name=call.name,
            content=result.as_json(),
        )


@dataclass
class NormalizedInput:
    prompt: str
    history: List[Message]


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict = field(default_factory=dict)


@dataclass
class ModelResponse:
    text: str
    tool_calls: List[ToolCall]
    model: str
    interaction_id: str = ""
    raw: dict = field(default_factory=dict)

    def provider_messages(self):
        return [Message.provider_step(step) for step in (self.raw.get("steps") or [])]


@dataclass
class ToolResult:
    status: str
    data: dict = field(default_factory=dict)
    retryable: bool = False

    def as_json(self):
        import json
        return json.dumps(self.data or {}, ensure_ascii=False)


@dataclass
class ToolLog:
    call: ToolCall
    result: ToolResult
    iteration: int
    duration_ms: int
    retry_count: int = 0
    phase: str = "primary"

    def to_legacy(self):
        return {
            "functionCall": {
                "id": self.call.id,
                "name": self.call.name,
                "arguments": dict(self.call.arguments or {}),
            },
            "functionResponse": dict(self.result.data or {}),
        }


@dataclass
class ValidationResult:
    ok: bool
    code: str = ""
    correction_instruction: str = ""
    details: dict = field(default_factory=dict)


@dataclass
class HarnessResult:
    reply: str
    model: str
    interaction_id: str
    tool_logs: List[ToolLog]
    iterations: int
    validation_retries: int
    normalized_input: NormalizedInput
    metadata: dict = field(default_factory=dict)


@dataclass
class HarnessConfig:
    system_prompt: str
    tools: list
    model_provider: Any
    validators: list
    max_tool_iterations: int = 5
    max_validation_retries: int = 1
    max_validation_tool_iterations: int = 2
    history_window: int = 12
    max_prompt_chars: int = 2000
    max_history_message_chars: int = 900
    message_builder: Any = None


@dataclass
class StoreAppendResult:
    thread_id: str
    title: str
    is_new: bool = False


class HarnessError(Exception):
    code = "harness_error"
    retryable = False

    def __init__(self, message="", **details):
        super().__init__(message or self.code)
        self.message = message or self.code
        self.details = details


class InvalidInput(HarnessError):
    code = "invalid_input"


class ToolBudgetExceeded(HarnessError):
    code = "tool_budget_exceeded"


class ValidationFailed(HarnessError):
    code = "validation_failed"


class ProviderError(HarnessError):
    code = "provider_error"

    def __init__(self, message="", status_code=502, retryable=False, **details):
        super().__init__(message, **details)
        self.status_code = int(status_code or 502)
        self.retryable = bool(retryable)


class Types:
    Message = Message
    NormalizedInput = NormalizedInput
    ToolCall = ToolCall
    ModelResponse = ModelResponse
    ToolResult = ToolResult
    ToolLog = ToolLog
    ValidationResult = ValidationResult
    HarnessResult = HarnessResult
    HarnessConfig = HarnessConfig
    StoreAppendResult = StoreAppendResult
    HarnessError = HarnessError
    InvalidInput = InvalidInput
    ToolBudgetExceeded = ToolBudgetExceeded
    ValidationFailed = ValidationFailed
    ProviderError = ProviderError


Model = Types
