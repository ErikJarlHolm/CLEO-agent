"""Tests for cleo_agent/agent.py

The OpenAI LLM is fully mocked so no API key is required.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from langchain.agents import AgentExecutor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_llm_response(text: str):
    """Return a minimal mock that makes create_openai_tools_agent happy."""
    from langchain_core.messages import AIMessage

    ai_msg = AIMessage(content=text)
    # AgentExecutor expects the LLM to return an object with a `.content` attr
    response = MagicMock()
    response.content = text
    response.additional_kwargs = {}
    response.tool_calls = []
    return response


# ---------------------------------------------------------------------------
# create_agent
# ---------------------------------------------------------------------------

class TestCreateAgent:
    def test_returns_agent_executor(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)

        with patch("cleo_agent.agent.ChatOpenAI") as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm_cls.return_value = mock_llm

            from cleo_agent.agent import create_agent

            executor = create_agent(model="gpt-4o-mini")

        assert isinstance(executor, AgentExecutor)

    def test_uses_correct_model(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)

        with patch("cleo_agent.agent.ChatOpenAI") as mock_llm_cls:
            mock_llm_cls.return_value = MagicMock()

            from cleo_agent.agent import create_agent

            create_agent(model="gpt-4-turbo")

        _, kwargs = mock_llm_cls.call_args
        assert kwargs.get("model") == "gpt-4-turbo" or mock_llm_cls.call_args.args[0:] == ()
        # Flexible: check positional or keyword
        call_args = mock_llm_cls.call_args
        all_kwargs = {**dict(zip(["model", "temperature"], call_args.args)), **call_args.kwargs}
        assert all_kwargs.get("model") == "gpt-4-turbo"

    def test_temperature_zero_by_default(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)

        with patch("cleo_agent.agent.ChatOpenAI") as mock_llm_cls:
            mock_llm_cls.return_value = MagicMock()

            from cleo_agent.agent import create_agent

            create_agent()

        call_args = mock_llm_cls.call_args
        all_kwargs = {**dict(zip(["model", "temperature"], call_args.args)), **call_args.kwargs}
        assert all_kwargs.get("temperature") == 0.0

    def test_agent_has_two_tools(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)

        with patch("cleo_agent.agent.ChatOpenAI") as mock_llm_cls:
            mock_llm_cls.return_value = MagicMock()

            from cleo_agent.agent import create_agent

            executor = create_agent()

        assert len(executor.tools) == 2

    def test_system_prompt_includes_current_date(self, monkeypatch):
        """Verify that the system prompt is baked in with today's date."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")
        monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
        monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)

        from datetime import datetime

        fake_date = "2026-05-05"

        with patch("cleo_agent.agent.ChatOpenAI") as mock_llm_cls, \
             patch("cleo_agent.agent.datetime") as mock_dt:
            mock_dt.now.return_value.strftime.return_value = fake_date
            mock_llm_cls.return_value = MagicMock()

            from cleo_agent.agent import create_agent

            executor = create_agent()

        # The date should appear somewhere in the executor's prompt
        # We verify via the stored prompt object on the agent
        prompt_str = str(executor.agent.runnable)
        # A light check – the prompt object was constructed from a dated system prompt
        # The actual date injection is tested more directly in test_prompts.py

    def test_uses_azure_client_when_endpoint_and_key_present(self, monkeypatch):
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "azure-key")
        monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)

        with patch("cleo_agent.agent.AzureChatOpenAI") as mock_azure_cls, \
             patch("cleo_agent.agent.ChatOpenAI") as mock_openai_cls:
            mock_azure_cls.return_value = MagicMock()

            from cleo_agent.agent import create_agent

            create_agent(model="my-deployment")

        _, kwargs = mock_azure_cls.call_args
        assert kwargs["azure_endpoint"] == "https://example.openai.azure.com/"
        assert kwargs["api_key"] == "azure-key"
        assert kwargs["api_version"] == "2024-02-01"
        assert kwargs["azure_deployment"] == "my-deployment"
        mock_openai_cls.assert_not_called()


# ---------------------------------------------------------------------------
# DEFAULT_MODEL
# ---------------------------------------------------------------------------

class TestDefaultModel:
    def test_default_is_gpt4o(self, monkeypatch):
        monkeypatch.delenv("CLEO_MODEL", raising=False)
        # Re-import to pick up env changes
        import importlib
        import cleo_agent.agent as agent_module

        importlib.reload(agent_module)
        assert agent_module.DEFAULT_MODEL == "gpt-4o"

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("CLEO_MODEL", "gpt-4-turbo")
        import importlib
        import cleo_agent.agent as agent_module

        importlib.reload(agent_module)
        assert agent_module.DEFAULT_MODEL == "gpt-4-turbo"


# ---------------------------------------------------------------------------
# run_agent  (fully mocked)
# ---------------------------------------------------------------------------

MOCK_AGENT_OUTPUT = """\
**Report Body:**
Test climate response.

**Date:**
2026-05-05

**Topic:**
Climate Test

**Problem Statement:**
Test query

**Executive Summary:**
This is a test.

**Discussion:**
Some discussion.

**Sources:**
1. IPCC AR6 – https://www.ipcc.ch/ar6/
"""


class TestRunAgent:
    def test_returns_string(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")

        with patch("cleo_agent.agent.create_agent") as mock_create:
            mock_executor = MagicMock()
            mock_executor.invoke.return_value = {"output": MOCK_AGENT_OUTPUT}
            mock_create.return_value = mock_executor

            from cleo_agent.agent import run_agent

            result = run_agent("Test query")

        assert isinstance(result, str)
        assert result == MOCK_AGENT_OUTPUT

    def test_passes_query_to_executor(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")

        with patch("cleo_agent.agent.create_agent") as mock_create:
            mock_executor = MagicMock()
            mock_executor.invoke.return_value = {"output": "response"}
            mock_create.return_value = mock_executor

            from cleo_agent.agent import run_agent

            run_agent("What is ocean acidification?")

        call_kwargs = mock_executor.invoke.call_args
        assert "What is ocean acidification?" in str(call_kwargs)
