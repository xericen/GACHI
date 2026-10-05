import io
import json
import os
import unittest
import urllib.error
from unittest import mock

from tests.test_ai_harness import IntegrationModelLoader, ModelLoader


class FactChatProviderTest(unittest.TestCase):
    def setUp(self):
        self.loader = ModelLoader()
        self.types = self.loader.model("ai_harness/types")
        self.factchat = self.loader.model("ai_harness/providers/factchat")
        self.types = self.factchat.Provider.generate.__globals__["Types"]
        self.agent_class = self.loader.model("agents/travel_planner")
        # Obtain the actual planner schema, not a reduced test-only contract.
        scope = self.agent_class.__init__.__globals__
        self.schema = scope["MODEL_RESPONSE_SCHEMA"]
        self.provider = self.factchat.Provider(self.factchat.Config(
            api_key="placeholder-factchat-key", response_schema=self.schema,
        ))

    def response(self, content="{}", finish="stop"):
        return io.BytesIO(json.dumps({
            "id": "chat-test", "choices": [
                {"finish_reason": finish, "message": {"content": content}},
            ],
        }).encode())

    def test_real_schema_auth_and_message_contract(self):
        with mock.patch("urllib.request.urlopen", return_value=self.response()) as call:
            result = self.provider.generate(
                [self.types.Message(role="user", content="내일 부산")], [], "system",
            )
        request = call.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(
            "https://factchat.mindlogic-kr-api.com/v1/gateway/chat/completions/", request.full_url,
        )
        self.assertEqual("placeholder-factchat-key", request.get_header("X-api-key"))
        self.assertIsNone(request.get_header("X-goog-api-key"))
        self.assertEqual("gpt-6-luna", payload["model"])
        self.assertFalse(payload["stream"])
        self.assertFalse(payload["store"])
        self.assertEqual("system", payload["messages"][0]["role"])
        self.assertEqual("내일 부산", payload["messages"][1]["content"])
        strict = payload["response_format"]["json_schema"]
        self.assertTrue(strict["strict"])
        slots = strict["schema"]["properties"]["changed_slots"]
        self.assertEqual(set(slots["properties"]), set(slots["required"]))
        self.assertEqual({"type": "null"}, slots["properties"]["days"]["anyOf"][1])
        self.assertNotIn("required", self.schema["properties"]["changed_slots"])
        self.assertEqual("{}", result.text)
        self.assertEqual("chat-test", result.interaction_id)

    def test_incomplete_refused_and_empty_responses_are_failures(self):
        for content, finish in [("{}", "length"), (None, "stop"), ("", "stop")]:
            with self.subTest(content=content, finish=finish):
                with mock.patch("urllib.request.urlopen", return_value=self.response(content, finish)):
                    with self.assertRaises(self.types.ProviderError):
                        self.provider.generate([], [], "system")

    def test_http_errors_keep_retry_policy_and_hide_provider_body(self):
        for status, retryable in [(401, False), (429, True), (503, True)]:
            error = urllib.error.HTTPError("url", status, "error", {}, io.BytesIO(b"placeholder-factchat-key"))
            with mock.patch("urllib.request.urlopen", side_effect=error):
                with self.assertRaises(self.types.ProviderError) as caught:
                    self.provider.generate([], [], "system")
            self.assertEqual(status, caught.exception.status_code)
            self.assertEqual(retryable, caught.exception.retryable)
            self.assertNotIn("placeholder-factchat-key", str(caught.exception))

    def test_invalid_json_and_network_errors_are_handled(self):
        for effect, retryable in [
            (io.BytesIO(b"invalid"), False),
            (urllib.error.URLError("private-error"), True),
        ]:
            kwargs = {"side_effect": effect} if isinstance(effect, Exception) else {"return_value": effect}
            with mock.patch("urllib.request.urlopen", **kwargs):
                with self.assertRaises(self.types.ProviderError) as caught:
                    self.provider.generate([], [], "system")
            self.assertEqual(retryable, caught.exception.retryable)

    def test_old_google_settings_cannot_override_new_provider(self):
        loader = IntegrationModelLoader()
        loader.databases["app_setting"].insert({
            "key": "ai_model_config",
            "value": json.dumps({"model": "gemini-2.5-flash-lite", "max_output_tokens": 800}),
        })
        with mock.patch.dict(os.environ, {"GOOGLE_AI_API_KEY": "old-google-key"}, clear=True):
            settings = loader.model("agents/travel_planner_settings")(loader)
            self.assertEqual("dummy-fixture-key", settings.api_key())
            self.assertEqual("gpt-6-luna", settings.model())
            self.assertEqual(4096, settings.max_output_tokens())
            view = settings.admin_view()
            self.assertEqual("FactChat (BAZE)", view["provider"])
            self.assertNotIn("api_key", view)
            with self.assertRaises(ValueError):
                settings.update({"model": "gemini-2.5-flash"})
        with mock.patch.dict(os.environ, {"BAZE_API_KEY": "new-key"}, clear=True):
            self.assertEqual("new-key", settings.api_key())

    def test_nullable_slots_preserve_existing_travel_state(self):
        loader = IntegrationModelLoader()
        agent = loader.model("agents/travel_planner")(loader)
        content = json.dumps({
            "changed_slots": {"region": None, "days": None, "companions": ["친구"]},
            "user_intent": "provide_information", "assistant_message": "언제 출발할까요?",
        })
        with mock.patch("urllib.request.urlopen", return_value=self.response(content)):
            status, payload = agent.send(
                "친구랑", state_raw=json.dumps({"region": "부산", "days": 2}),
            )
        self.assertEqual(200, status)
        self.assertEqual("부산", payload["travel_state"]["region"])
        self.assertEqual(2, payload["travel_state"]["days"])
        self.assertEqual(["친구"], payload["travel_state"]["companions"])
        self.assertEqual("gpt-6-luna", payload["model"])
