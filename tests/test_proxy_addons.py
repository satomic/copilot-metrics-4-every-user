import importlib
import os
import pathlib
import sys
import tempfile
import types
import unittest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


class _FakeLogger:
    def info(self, *_args, **_kwargs):
        pass

    def warn(self, *_args, **_kwargs):
        pass

    def error(self, *_args, **_kwargs):
        pass


def _import_proxy_addons():
    fake_mitmproxy = types.ModuleType("mitmproxy")
    fake_http = types.ModuleType("mitmproxy.http")
    fake_http.HTTPFlow = object
    fake_http.Response = types.SimpleNamespace(make=lambda *_args, **_kwargs: None)
    fake_ctx = types.SimpleNamespace(log=_FakeLogger())
    fake_mitmproxy.http = fake_http
    fake_mitmproxy.ctx = fake_ctx

    sys.modules["mitmproxy"] = fake_mitmproxy
    sys.modules["mitmproxy.http"] = fake_http
    sys.modules["mitmproxy.ctx"] = fake_ctx
    sys.modules.pop("proxy_addons", None)

    previous_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        try:
            return importlib.import_module("proxy_addons")
        finally:
            os.chdir(previous_cwd)


class ContentHandlerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proxy_addons = _import_proxy_addons()

    def test_json_parser_preserves_json_literals_and_string_values(self):
        content = '{"enabled": false, "count": null, "note": "false true null"}'

        result, convert_status = self.proxy_addons.ContentHandler.to_dicts(content)

        self.assertTrue(convert_status)
        self.assertEqual(
            result,
            {"enabled": False, "count": None, "note": "false true null"},
        )


class ActionClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proxy_addons = _import_proxy_addons()

    def test_nonempty_tools_can_identify_newer_agent_requests(self):
        action_type = self.proxy_addons.classify_action_type(
            request_type=self.proxy_addons.RequestType.chat,
            content_request_dict={
                "messages": [{"role": "user", "content": "Fix this"}],
                "tools": [{"name": "editFile"}],
            },
            model="gpt-4o-copilot",
            openai_intent="conversation-panel",
            x_initiator=None,
            x_interaction_type=None,
            x_onbehalf_extension_id=None,
        )

        self.assertEqual(action_type, "agent")

    def test_empty_tools_do_not_force_chat_panel_into_agent(self):
        action_type = self.proxy_addons.classify_action_type(
            request_type=self.proxy_addons.RequestType.chat,
            content_request_dict={
                "messages": [{"role": "user", "content": "Hello"}],
                "tools": [],
            },
            model="gpt-4o-copilot",
            openai_intent="conversation-panel",
            x_initiator=None,
            x_interaction_type=None,
            x_onbehalf_extension_id=None,
        )

        self.assertEqual(action_type, "chat-panel")

    def test_null_model_does_not_crash_classification(self):
        action_type = self.proxy_addons.classify_action_type(
            request_type=self.proxy_addons.RequestType.chat,
            content_request_dict={"messages": [{"role": "user", "content": "Hello"}]},
            model=None,
            openai_intent="unknown",
            x_initiator=None,
            x_interaction_type=None,
            x_onbehalf_extension_id=None,
        )

        self.assertEqual(action_type, "other")

    def test_extension_header_without_dot_does_not_crash_classification(self):
        action_type = self.proxy_addons.classify_action_type(
            request_type=self.proxy_addons.RequestType.chat,
            content_request_dict={"messages": [{"role": "user", "content": "Hello"}]},
            model="gpt-4o-copilot",
            openai_intent="conversation-other",
            x_initiator=None,
            x_interaction_type=None,
            x_onbehalf_extension_id="copilot-chat",
        )

        self.assertEqual(action_type, "copilot-chat")


if __name__ == "__main__":
    unittest.main()
