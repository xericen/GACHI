import pathlib
import unittest
import datetime
import json
from types import SimpleNamespace


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL_ROOT = PROJECT_ROOT / "src" / "model"


class ModelLoader:
    def model(self, namespace):
        path = MODEL_ROOT / f"{namespace}.py"
        scope = {
            "__file__": str(path),
            "__name__": str(path),
            "wiz": self,
        }
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), scope)
        return scope["Model"]


class IntegrationModelLoader(ModelLoader):
    def __init__(self):
        self.databases = {
            "chat_thread": MemoryThreadDb(),
            "app_setting": MemoryThreadDb(),
        }
        self.orm = MemoryOrmService(self.databases)
        self.ai_tools = FixtureAiTools()

    def model(self, namespace):
        if namespace == "portal/season/orm":
            return self.orm
        if namespace == "ai_tools":
            return self.ai_tools
        return super().model(namespace)

    def config(self, namespace):
        if namespace != "ai":
            raise KeyError(namespace)
        return SimpleNamespace(gemini=SimpleNamespace(
            api_key="dummy-fixture-key",
            model="gemini-2.5-flash",
            timeout=30,
        ))


class SequenceProvider:
    def __init__(self, types, responses):
        self.types = types
        self.responses = list(responses)
        self.calls = 0

    def generate(self, messages, tools, system_prompt, stream=False):
        response = self.responses[self.calls]
        self.calls += 1
        return response


class EchoTool:
    name = "echo"
    schema = {"type": "function", "name": "echo", "parameters": {"type": "object"}}

    def __init__(self, types):
        self.types = types

    def execute(self, arguments):
        return self.types.ToolResult(status="ok", data={"status": "ok", "echo": arguments})


class ExactReplyValidator:
    def __init__(self, types, expected):
        self.types = types
        self.expected = expected

    def check(self, reply, tool_logs):
        if reply == self.expected:
            return self.types.ValidationResult(ok=True)
        return self.types.ValidationResult(
            ok=False,
            code="invalid_reply",
            correction_instruction="검증 가능한 답변으로 다시 작성하세요.",
        )


class ImmediateRetryPolicy:
    def run(self, operation, should_retry=None, on_retry=None):
        return operation(0)


class CapturingLogger:
    def __init__(self):
        self.events = []

    def new_run_id(self):
        return "test-run"

    def emit(self, event, **fields):
        self.events.append((event, fields))


class MemoryThreadDb:
    def __init__(self):
        self.data = {}
        self.sequence = 0
        self.orm = self

    def create_table(self, safe=True):
        return None

    def get(self, **where):
        for row in self.data.values():
            if all(row.get(key) == value for key, value in where.items()):
                return dict(row)
        return None

    def rows(self, **query):
        user_id = query.get("user_id")
        rows = [dict(row) for row in self.data.values() if row.get("user_id") == user_id]
        rows.sort(key=lambda row: row.get("updated", ""), reverse=True)
        return rows[:query.get("dump", 30)]

    def insert(self, data):
        self.sequence += 1
        item = dict(data)
        item["id"] = f"thread-{self.sequence}"
        self.data[item["id"]] = item
        return item["id"]

    def update(self, data, **where):
        row = self.get(**where)
        if row:
            self.data[row["id"]].update(data)


class MemoryOrmService:
    def __init__(self, databases):
        self.databases = databases

    def use(self, name):
        return self.databases[name]


class FixtureAiTools:
    def __init__(self):
        self.fail_search = False
        self.fail_directions = False
        self.search_calls = []
        self.direction_calls = []

    def function_declarations(self):
        return [
            {"type": "function", "name": "place_search", "parameters": {"type": "object"}},
            {"type": "function", "name": "directions_lookup", "parameters": {"type": "object"}},
        ]

    def execute_place_search(self, arguments):
        self.search_calls.append(dict(arguments or {}))
        if self.fail_search:
            return {"status": "not_found", "results": []}
        category = arguments.get("category") or "관광지"
        region = arguments.get("region") or "서울"
        excludes = set(arguments.get("exclude_place_ids") or [])
        rows = []
        for index in range(1, 9):
            place_id = f"{region}-{category}-{index}"
            if place_id in excludes:
                continue
            rows.append({
                "place_id": place_id,
                "name": "서울숲" if category == "관광지" and index == 1 else f"{region} {category} {index}",
                "category": category,
                "address": f"{region} 테스트구 {index}",
                "lat": 37.50 + index * 0.002,
                "lng": 127.00 + index * 0.002,
                "thumbnail": "",
                "usage_time": "09:00~22:00",
            })
        return {"status": "ok", "relaxation": "", "results": rows[:int(arguments.get("limit") or 5)]}

    def execute_directions_lookup(self, arguments):
        self.direction_calls.append(dict(arguments or {}))
        if self.fail_directions:
            return {"status": "not_available", "duration_minutes": None, "distance_meters": None}
        return {"status": "ok", "source": "fixture", "duration_minutes": 10, "distance_meters": 1000}


class MarkerExecutor:
    def __init__(self, marker, status=200, fallback_reason=""):
        self.marker = marker
        self.status = status
        self.fallback_reason = fallback_reason

    def send(self, *args):
        payload = {"executor": self.marker}
        if self.fallback_reason:
            payload["_fallback_reason"] = self.fallback_reason
        return self.status, payload

    def threads(self, *args):
        return [{"executor": self.marker}]

    def thread(self, *args):
        return {"executor": self.marker}


class AgentHarnessTest(unittest.TestCase):
    def setUp(self):
        self.loader = ModelLoader()
        self.types = self.loader.model("ai_harness/types")
        self.Harness = self.loader.model("ai_harness/harness")

    def response(self, text="", calls=None):
        return self.types.ModelResponse(
            text=text,
            tool_calls=calls or [],
            model="fixture-model",
            interaction_id="fixture-interaction",
        )

    def call(self, index):
        return self.types.ToolCall(id=f"call-{index}", name="echo", arguments={"index": index})

    def harness(self, responses, validators=None, logger=None):
        provider = SequenceProvider(self.types, responses)
        config = self.types.HarnessConfig(
            system_prompt="test",
            tools=[EchoTool(self.types)],
            model_provider=provider,
            validators=validators or [],
            max_tool_iterations=5,
            max_validation_retries=1,
            max_validation_tool_iterations=2,
            history_window=12,
            max_prompt_chars=2000,
            max_history_message_chars=900,
        )
        harness = self.Harness(
            config=config,
            retry_policy=ImmediateRetryPolicy(),
            logger=logger or CapturingLogger(),
        )
        return harness, provider

    def test_input_limits_are_applied_once_by_harness(self):
        harness, _ = self.harness([self.response(text="ok")])
        history = [
            self.types.Message(role="user" if index % 2 == 0 else "assistant", content=f"{index}:" + "x" * 1000)
            for index in range(13)
        ]

        result = harness.run("  " + "p" * 2001 + "  ", history)

        self.assertEqual(2000, len(result.normalized_input.prompt))
        self.assertEqual(12, len(result.normalized_input.history))
        self.assertTrue(result.normalized_input.history[0].content.startswith("1:"))
        self.assertTrue(all(len(message.content) == 900 for message in result.normalized_input.history))

    def test_validation_repair_has_separate_tool_budget(self):
        logger = CapturingLogger()
        primary_tools = [self.response(calls=[self.call(index)]) for index in range(5)]
        repair_tools = [self.response(calls=[self.call(index)]) for index in range(5, 7)]
        responses = primary_tools + [self.response(text="invalid")] + repair_tools + [self.response(text="valid")]
        validator = ExactReplyValidator(self.types, "valid")
        harness, provider = self.harness(responses, validators=[validator], logger=logger)

        result = harness.run("prompt", [])

        self.assertEqual("valid", result.reply)
        self.assertEqual(9, provider.calls)
        self.assertEqual(1, result.validation_retries)
        tool_events = [fields for event, fields in logger.events if event == "tool_execution"]
        self.assertEqual(7, len(tool_events))
        self.assertEqual(5, len([event for event in tool_events if event["phase"] == "primary"]))
        self.assertEqual(2, len([event for event in tool_events if event["phase"] == "validation_repair"]))
        self.assertTrue(all(event["has_response"] for event in tool_events))

    def test_unvalidated_reply_is_not_returned_when_repair_budget_is_exhausted(self):
        primary_tools = [self.response(calls=[self.call(index)]) for index in range(5)]
        repair_tools = [self.response(calls=[self.call(index)]) for index in range(5, 8)]
        responses = primary_tools + [self.response(text="invalid")] + repair_tools
        validator = ExactReplyValidator(self.types, "valid")
        harness, provider = self.harness(responses, validators=[validator])

        with self.assertRaises(Exception) as context:
            harness.run("prompt", [])

        self.assertEqual("tool_budget_exceeded", getattr(context.exception, "code", ""))
        self.assertEqual(9, provider.calls)
        finished = [fields for event, fields in harness.logger.events if event == "agent_run_finished"][-1]
        self.assertEqual("harness", finished["executor"])
        self.assertEqual("tool_budget_exceeded", finished["fallback_reason"])


class ChatThreadStoreTest(unittest.TestCase):
    def setUp(self):
        self.loader = ModelLoader()
        self.types = self.loader.model("ai_harness/types")
        Store = self.loader.model("ai_harness/storage/chat_thread_store")
        self.db = MemoryThreadDb()
        self.store = Store(
            self.db,
            clock=lambda: datetime.datetime(2026, 7, 16, 2, 0, 0),
        )

    def test_store_is_shared_and_keeps_80_messages_with_user_ownership(self):
        seed = [
            self.types.Message(role="user" if index % 2 == 0 else "assistant", content=f"seed-{index}")
            for index in range(79)
        ]
        saved = self.store.append_turn("", "user-1", "첫 질문", "첫 답변", seed)

        self.assertTrue(saved.is_new)
        thread = self.store.get(saved.thread_id, "user-1")
        self.assertEqual(80, len(thread["messages"]))
        self.assertEqual("seed-1", thread["messages"][0]["text"])
        self.assertEqual("첫 답변", thread["messages"][-1]["text"])
        self.assertIsNone(self.store.get(saved.thread_id, "user-2"))
        self.assertEqual(1, len(self.store.list("user-1")))


class TravelPlannerContractTest(unittest.TestCase):
    def setUp(self):
        self.loader = IntegrationModelLoader()
        self.types = self.loader.model("ai_harness/types")
        Agent = self.loader.model("agents/travel_planner")
        self.agent = Agent(self.loader)
        self.logger = CapturingLogger()
        self.agent.logger = self.logger
        self.agent.harness.logger = self.logger

    def test_send_uses_unified_payload_and_persists_only_logged_in_user(self):
        response = self.types.ModelResponse(
            text="여행 조건을 조금 더 알려주세요.",
            tool_calls=[],
            model="fixture-model",
            interaction_id="interaction-1",
        )
        self.agent.harness.config.model_provider = SequenceProvider(self.types, [response, response])

        anonymous_status, anonymous = self.agent.send("질문", "[]", "", "")
        login_status, logged_in = self.agent.send("질문", "[]", "user-1", "")

        self.assertEqual(200, anonymous_status)
        for key in ["message", "reply", "stage", "travel_state", "itinerary_draft", "missing_slots", "action", "warnings"]:
            self.assertIn(key, anonymous)
        self.assertEqual("", anonymous["thread_id"])
        self.assertEqual(200, login_status)
        self.assertTrue(logged_in["thread_id"])
        self.assertEqual("질문", logged_in["title"])
        self.assertEqual(1, len(self.agent.threads("user-1")))
        self.assertEqual(2, len(self.agent.thread("user-1", logged_in["thread_id"])["messages"]))

    def test_empty_prompt_and_admin_settings_contract(self):
        status, payload = self.agent.send("   ")
        settings = self.agent.admin_settings()

        self.assertEqual(400, status)
        self.assertEqual("질문을 입력해주세요.", payload["message"])
        self.assertEqual("Google Gemini", settings["provider"])
        self.assertEqual(["장소 검색", "경로 조회"], settings["tools"])
        self.assertTrue(settings["api_key_configured"])

    def test_server_planner_tool_logs_keep_frontend_legacy_shape(self):
        response = self.types.ModelResponse(
            text=json.dumps({
                "changed_slots": {}, "user_intent": "generate_course",
                "action": "generate_itinerary", "assistant_message": "코스를 준비할게요.",
            }, ensure_ascii=False),
            tool_calls=[],
            model="fixture-model",
        )
        self.agent.harness.config.model_provider = SequenceProvider(self.types, [response])

        status, payload = self.agent.send("서울 1일 대중교통 자연 코스 만들어줘", "[]", "", "")

        self.assertEqual(200, status)
        self.assertEqual("draft_ready", payload["stage"])
        self.assertEqual("place_search", payload["tool_logs"][0]["functionCall"]["name"])
        self.assertEqual("서울 자연 1", payload["tool_logs"][0]["functionResponse"]["results"][0]["name"])

    def test_malformed_json_uses_deterministic_fallback_without_502(self):
        response = self.types.ModelResponse(text="JSON 아님", tool_calls=[], model="fixture-model")
        self.agent.harness.config.model_provider = SequenceProvider(self.types, [response])

        status, payload = self.agent.send("서울 1일 대중교통 자연 코스 만들어줘", "[]", "", "")

        self.assertEqual(200, status)
        self.assertEqual("json_parse_recovered", payload["_fallback_reason"])
        self.assertEqual("draft_ready", payload["stage"])
        self.assertTrue(payload["itinerary_draft"]["days"])

    def test_internal_tool_name_is_never_exposed(self):
        response = self.types.ModelResponse(
            text="place_search를 호출한 뒤 다시 답하겠습니다.",
            tool_calls=[],
            model="fixture-model",
        )
        self.agent.harness.config.model_provider = SequenceProvider(self.types, [response])

        status, payload = self.agent.send("부산으로 갈게")

        self.assertEqual(200, status)
        self.assertNotIn("place_search", payload["message"])
        self.assertEqual([], self.agent.harness.config.tools)
        self.assertEqual("days", payload["missing_slots"][0])

    def test_validation_error_recovers_with_server_slot_extraction(self):
        class ValidationRaisingHarness:
            def __init__(self, error_type):
                self.error_type = error_type

            def run(self, prompt, history):
                raise self.error_type("invalid model reply")

        self.agent.harness = ValidationRaisingHarness(self.types.ValidationFailed)

        status, payload = self.agent.send("부산 2일 대중교통으로 바다 여행")

        self.assertEqual(200, status)
        self.assertEqual("validation_failed", payload["_fallback_reason"])
        self.assertEqual("부산", payload["travel_state"]["region"])
        self.assertEqual(2, payload["travel_state"]["days"])
        self.assertNotIn("검증", payload["message"])

    def test_non_json_reply_does_not_replace_natural_server_message(self):
        response = self.types.ModelResponse(text="{not-json place_search", tool_calls=[], model="fixture-model")
        self.agent.harness.config.model_provider = SequenceProvider(self.types, [response])

        status, payload = self.agent.send("서울에서 자연 여행하고 싶어")

        self.assertEqual(200, status)
        self.assertEqual("서울", payload["travel_state"]["region"])
        self.assertIn("며칠", payload["message"])
        self.assertNotIn("place_search", payload["message"])


class AiChatRollbackContractTest(unittest.TestCase):
    def setUp(self):
        self.loader = IntegrationModelLoader()

    def test_runtime_switch_is_read_for_every_request_and_legacy_is_lazy(self):
        facade = self.loader.model("ai_chat")
        lines = []
        Monitor = self.loader.model("ai_chat_observability")
        facade.monitor = Monitor(sink=lines.append, clock=lambda: 1000)
        facade.agent = MarkerExecutor("harness")
        legacy_instances = []

        def legacy_factory():
            executor = MarkerExecutor("legacy")
            legacy_instances.append(executor)
            return executor

        facade.legacy_factory = legacy_factory

        self.assertEqual("harness", facade.send("질문")[1]["executor"])
        facade.switch.set_enabled(False)
        self.assertEqual("legacy", facade.send("질문")[1]["executor"])
        self.assertEqual("legacy", facade.threads("user-1")[0]["executor"])
        self.assertEqual(1, len(legacy_instances))
        facade.switch.set_enabled(True)
        self.assertEqual("harness", facade.send("질문")[1]["executor"])
        events = [json.loads(line.split(" ", 1)[1]) for line in lines]
        self.assertEqual(["harness", "legacy", "harness"], [event["executor"] for event in events])

    def test_internal_fallback_reason_is_logged_but_not_exposed(self):
        facade = self.loader.model("ai_chat")
        lines = []
        Monitor = self.loader.model("ai_chat_observability")
        facade.monitor = Monitor(sink=lines.append, clock=lambda: 1000)
        facade.agent = MarkerExecutor("harness", status=502, fallback_reason="validation_failed")

        status, payload = facade.send("질문")

        event = json.loads(lines[-1].split(" ", 1)[1])
        self.assertEqual(200, status)
        self.assertNotIn("_fallback_reason", payload)
        self.assertEqual("harness", event["executor"])
        self.assertEqual("validation_failed_recovered", event["fallback_reason"])
        self.assertNotIn("검증", payload["message"])

    def test_public_contract_hides_server_tool_traces(self):
        facade = self.loader.model("ai_chat")

        class ToolTraceExecutor(MarkerExecutor):
            def send(self, *args):
                return 200, {
                    "message": "코스 초안을 만들었어요.",
                    "stage": "draft_ready",
                    "tool_logs": [{"functionCall": {"name": "place_search"}}],
                }

        facade.agent = ToolTraceExecutor("harness")
        status, payload = facade.send("코스 만들어줘")

        self.assertEqual(200, status)
        self.assertNotIn("tool_logs", payload)
        self.assertNotIn("place_search", json.dumps(payload, ensure_ascii=False))

    def test_legacy_validation_failure_recovers_through_state_machine_executor(self):
        facade = self.loader.model("ai_chat")
        facade.switch.set_enabled(False)

        class UnsafeLegacy(MarkerExecutor):
            def send(self, *args):
                return 200, {
                    "reply": "place_search 검증 실패",
                    "_fallback_reason": "legacy_unverified_reply",
                }

        class SafeHarness(MarkerExecutor):
            def send(self, *args):
                return 200, {
                    "message": "여행 기간은 며칠로 생각하고 있나요?",
                    "stage": "collecting",
                    "missing_slots": ["days"],
                }

        facade.legacy_factory = lambda: UnsafeLegacy("legacy")
        facade.agent = SafeHarness("harness")

        status, payload = facade.send("부산으로 갈게")

        self.assertEqual(200, status)
        self.assertEqual("여행 기간은 며칠로 생각하고 있나요?", payload["message"])
        self.assertNotIn("place_search", json.dumps(payload, ensure_ascii=False))
        self.assertNotIn("검증 실패", json.dumps(payload, ensure_ascii=False))

    def test_legacy_and_harness_share_thread_storage_in_both_directions(self):
        Legacy = self.loader.model("ai_chat_legacy")
        Agent = self.loader.model("agents/travel_planner")
        legacy = Legacy()
        agent = Agent(self.loader)

        legacy_saved = legacy._save_thread("user-1", "", "legacy 질문", "legacy 답변", "[]")
        restored_by_harness = agent.thread("user-1", legacy_saved["thread_id"])
        self.assertEqual(["legacy 질문", "legacy 답변"], [row["text"] for row in restored_by_harness["messages"]])

        harness_saved = agent.store.append_turn("", "user-1", "harness 질문", "harness 답변", [])
        restored_by_legacy = legacy.thread("user-1", harness_saved.thread_id)
        self.assertEqual(["harness 질문", "harness 답변"], [row["text"] for row in restored_by_legacy["messages"]])

    def test_admin_settings_contract_is_independent_from_active_executor(self):
        facade = self.loader.model("ai_chat")
        enabled_view = facade.admin_settings()
        facade.switch.set_enabled(False)
        legacy_view = facade.admin_settings()

        self.assertTrue(enabled_view["harness_enabled"])
        self.assertFalse(legacy_view["harness_enabled"])
        for key in ["provider", "enabled", "model", "timeout", "temperature", "max_output_tokens", "tools"]:
            self.assertEqual(enabled_view[key], legacy_view[key])

        updated = facade.update_admin_settings({
            "enabled": True,
            "model": "gemini-2.5-flash-lite",
            "timeout": 25,
            "temperature": 0.3,
            "max_output_tokens": 800,
            "harness_enabled": True,
        })
        self.assertTrue(updated["harness_enabled"])
        self.assertEqual("gemini-2.5-flash-lite", updated["model"])
        self.assertEqual("gemini-2.5-flash-lite", self.loader.model("ai_chat_legacy")().admin_settings()["model"])

        rollback_view = facade.update_admin_settings({"harness_enabled": False})
        self.assertFalse(rollback_view["harness_enabled"])
        self.assertEqual("gemini-2.5-flash-lite", rollback_view["model"])

    def test_legacy_tool_adapter_signatures_still_match(self):
        Legacy = self.loader.model("ai_chat_legacy")
        legacy = Legacy()

        self.assertEqual(
            ["place_search", "directions_lookup"],
            [item["name"] for item in legacy._tool_declarations()],
        )
        place_result = legacy._execute_tool("place_search", {"region": "서울", "category": "관광지"})
        route_result = legacy._execute_tool("directions_lookup", {"mode": "walking"})
        self.assertEqual("서울숲", place_result["results"][0]["name"])
        self.assertEqual("ok", route_result["status"])

    def test_legacy_marks_unverified_reply_at_shared_budget_boundary(self):
        Legacy = self.loader.model("ai_chat_legacy")
        legacy = Legacy()
        responses = [
            {"steps": [{
                "type": "function_call",
                "id": f"call-{index}",
                "name": "place_search",
                "arguments": {"region": "서울", "category": "관광지"},
            }]}
            for index in range(4)
        ]
        responses.append({"steps": [{
            "type": "message",
            "content": "[일정 제안]\n동선: [가짜공원 | 위치: 서울]",
        }]})
        legacy._post_interaction = lambda input_steps: responses.pop(0)

        result = legacy._call_gemini("서울 여행", [])

        self.assertEqual("legacy_unverified_reply", result["fallback_reason"])
        self.assertIn("가짜공원", result["reply"])


class ChatStabilizationMonitorTest(unittest.TestCase):
    def test_alerts_when_harness_502_is_three_times_legacy_and_validation_is_high(self):
        loader = ModelLoader()
        Monitor = loader.model("ai_chat_observability")
        lines = []
        monitor = Monitor(sink=lines.append, clock=lambda: 1000)

        for index in range(20):
            monitor.record("legacy", 502 if index == 0 else 200, "legacy_provider_error" if index == 0 else "none")
        for index in range(20):
            monitor.record("harness", 502 if index < 3 else 200, "validation_failed" if index < 3 else "none")

        snapshot = monitor._snapshot()
        self.assertEqual(0.15, snapshot["harness_502_rate"])
        self.assertEqual(0.05, snapshot["legacy_502_rate"])
        self.assertEqual(3.0, snapshot["harness_to_legacy_502_ratio"])
        self.assertEqual(
            ["harness_502_absolute_rate", "harness_validation_502_rate", "harness_502_vs_legacy"],
            snapshot["alert_reasons"],
        )
        alert_events = [
            json.loads(line.split(" ", 1)[1])
            for line in lines
            if '"event": "chat_stabilization_alert"' in line
        ]
        self.assertEqual(1, len(alert_events))


class GeminiProviderContractTest(unittest.TestCase):
    def test_multiple_function_calls_are_preserved(self):
        loader = ModelLoader()
        Gemini = loader.model("ai_harness/providers/gemini")
        provider = Gemini.Provider(Gemini.Config(api_key="key", model="model"))

        calls = provider._extract_function_calls({"steps": [
            {"type": "function_call", "id": "1", "name": "place_search", "arguments": {"region": "서울"}},
            {"type": "function_call", "id": "2", "name": "directions_lookup", "arguments": "{\"mode\": \"walking\"}"},
        ]})

        self.assertEqual(["place_search", "directions_lookup"], [call.name for call in calls])
        self.assertEqual("walking", calls[1].arguments["mode"])


class RetryAndValidationTest(unittest.TestCase):
    def test_retry_policy_retries_only_retryable_errors(self):
        loader = ModelLoader()
        Types = loader.model("ai_harness/types")
        RetryPolicy = loader.model("ai_harness/observability/retry")
        attempts = []
        delays = []
        policy = RetryPolicy(
            max_retries=2,
            base_delay=0.1,
            jitter=0,
            sleep_fn=lambda delay: delays.append(delay),
        )

        def operation(attempt):
            attempts.append(attempt)
            if attempt < 2:
                raise Types.ProviderError("temporary", status_code=503, retryable=True)
            return "ok"

        result = policy.run(operation)

        self.assertEqual("ok", result)
        self.assertEqual([0, 1, 2], attempts)
        self.assertEqual([0.1, 0.2], delays)

    def test_itinerary_validator_uses_typed_tool_logs(self):
        loader = ModelLoader()
        Types = loader.model("ai_harness/types")
        Validator = loader.model("agents/travel_planner_validator")
        validator = Validator()
        call = Types.ToolCall(id="1", name="place_search", arguments={})
        result = Types.ToolResult(status="ok", data={"status": "ok", "results": [{"name": "서울숲"}]})
        log = Types.ToolLog(call=call, result=result, iteration=0, duration_ms=1)

        valid = validator.check("[일정 제안]\n동선: [서울숲 | 위치: 성동구]", [log])
        invalid = validator.check("[일정 제안]\n동선: [가짜공원 | 위치: 성동구]", [log])

        self.assertTrue(valid.ok)
        self.assertFalse(invalid.ok)
        self.assertEqual("unverified_place", invalid.code)


if __name__ == "__main__":
    unittest.main()
