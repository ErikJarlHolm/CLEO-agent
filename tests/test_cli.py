"""Tests for main.py – CLI argument parsing and dispatch logic.

The LLM and agent are fully mocked; no API keys are required.
"""

from __future__ import annotations

import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest


MOCK_RESPONSE = """\
**Report Body:**
Global temperatures have risen by approximately 1.1 °C since pre-industrial times.

**Date:**
2026-05-05

**Topic:**
Global Warming

**Problem Statement:**
What is the current state of global warming?

**Executive Summary:**
Temperatures are rising. Action is needed.

**Discussion:**
Uncertainty remains in exact projections.

**Sources:**
1. IPCC AR6 – https://www.ipcc.ch/ar6/
"""


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

class TestArgumentParser:
    def setup_method(self):
        # Import freshly each test to avoid module-level side-effects
        import importlib
        import main as m
        self.parser = m._build_parser()

    def test_single_query_argument(self):
        args = self.parser.parse_args(["What causes global warming?"])
        assert args.query == "What causes global warming?"
        assert not args.interactive
        assert not args.verbose

    def test_interactive_flag_short(self):
        args = self.parser.parse_args(["-i"])
        assert args.interactive is True
        assert args.query is None

    def test_interactive_flag_long(self):
        args = self.parser.parse_args(["--interactive"])
        assert args.interactive is True

    def test_verbose_flag_short(self):
        args = self.parser.parse_args(["-v", "some question"])
        assert args.verbose is True

    def test_verbose_flag_long(self):
        args = self.parser.parse_args(["--verbose", "some question"])
        assert args.verbose is True

    def test_model_flag(self):
        args = self.parser.parse_args(["--model", "gpt-4-turbo", "question"])
        assert args.model == "gpt-4-turbo"

    def test_model_defaults_to_none(self):
        args = self.parser.parse_args(["question"])
        assert args.model is None

    def test_no_args_query_is_none(self):
        args = self.parser.parse_args([])
        assert args.query is None
        assert not args.interactive


# ---------------------------------------------------------------------------
# _run_once
# ---------------------------------------------------------------------------

class TestRunOnce:
    def test_prints_response(self, monkeypatch, capsys):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")

        with patch("cleo_agent.agent.create_agent") as mock_create:
            mock_executor = MagicMock()
            mock_executor.invoke.return_value = {"output": MOCK_RESPONSE}
            mock_create.return_value = mock_executor

            import main

            main._run_once("What causes global warming?", None, False)

        captured = capsys.readouterr()
        assert "Report Body" in captured.out
        assert "Global Warming" in captured.out

    def test_uses_model_override(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")

        with patch("cleo_agent.agent.run_agent") as mock_run:
            mock_run.return_value = MOCK_RESPONSE

            import main

            main._run_once("test", "gpt-4-turbo", False)

        mock_run.assert_called_once_with("test", model="gpt-4-turbo", verbose=False)

    def test_uses_default_model_when_none(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")

        with patch("cleo_agent.agent.run_agent") as mock_run, \
             patch("cleo_agent.agent.DEFAULT_MODEL", "gpt-4o"):
            mock_run.return_value = MOCK_RESPONSE

            import main

            main._run_once("test", None, False)

        _, kwargs = mock_run.call_args
        assert kwargs["model"] == "gpt-4o"


# ---------------------------------------------------------------------------
# main() dispatch
# ---------------------------------------------------------------------------

class TestMainDispatch:
    def test_no_args_prints_help_and_exits(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["cleo"])

        import main

        with pytest.raises(SystemExit) as exc_info:
            main.main()

        assert exc_info.value.code == 1

    def test_query_dispatches_to_run_once(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["cleo", "test question"])
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")

        with patch("main._run_once") as mock_run_once:
            import main

            main.main()

        mock_run_once.assert_called_once()
        call_args = mock_run_once.call_args
        assert call_args.args[0] == "test question"

    def test_interactive_flag_dispatches_to_interactive(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["cleo", "--interactive"])
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")

        with patch("main._run_interactive") as mock_interactive:
            import main

            main.main()

        mock_interactive.assert_called_once()


# ---------------------------------------------------------------------------
# _run_interactive – quit paths
# ---------------------------------------------------------------------------

class TestRunInteractiveQuit:
    def _make_executor(self):
        mock_executor = MagicMock()
        mock_executor.invoke.return_value = {"output": MOCK_RESPONSE}
        return mock_executor

    @pytest.mark.parametrize("quit_word", ["quit", "exit", "avslutt", "q"])
    def test_quit_words_exit_loop(self, monkeypatch, quit_word):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")

        with patch("cleo_agent.agent.create_agent", return_value=self._make_executor()), \
             patch("builtins.input", side_effect=[quit_word]):
            import main

            # Should return without error
            main._run_interactive(None, False)

    def test_eof_exits_gracefully(self, monkeypatch, capsys):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")

        with patch("cleo_agent.agent.create_agent", return_value=self._make_executor()), \
             patch("builtins.input", side_effect=EOFError):
            import main

            main._run_interactive(None, False)

        captured = capsys.readouterr()
        assert "Goodbye" in captured.out or "Avslutt" in captured.out

    def test_keyboard_interrupt_exits_gracefully(self, monkeypatch, capsys):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")

        with patch("cleo_agent.agent.create_agent", return_value=self._make_executor()), \
             patch("builtins.input", side_effect=KeyboardInterrupt):
            import main

            main._run_interactive(None, False)

        captured = capsys.readouterr()
        assert "Goodbye" in captured.out or "Avslutt" in captured.out

    def test_empty_input_is_skipped(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")

        mock_executor = self._make_executor()

        with patch("cleo_agent.agent.create_agent", return_value=mock_executor), \
             patch("builtins.input", side_effect=["", "  ", "quit"]):
            import main

            main._run_interactive(None, False)

        # No actual agent invocation should happen
        mock_executor.invoke.assert_not_called()
