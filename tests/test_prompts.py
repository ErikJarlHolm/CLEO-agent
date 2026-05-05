"""Tests for cleo_agent/prompts.py"""

import re
from datetime import datetime

import pytest

from cleo_agent.prompts import SYSTEM_PROMPT


class TestSystemPromptContent:
    """Verify the system prompt contains all required content."""

    def test_prompt_is_non_empty_string(self):
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 500

    def test_contains_current_date_placeholder(self):
        assert "{current_date}" in SYSTEM_PROMPT

    def test_prompt_formatting_with_date(self):
        formatted = SYSTEM_PROMPT.format(current_date="2026-05-05")
        assert "2026-05-05" in formatted
        assert "{current_date}" not in formatted

    # ------------------------------------------------------------------
    # Mandatory response-format sections
    # ------------------------------------------------------------------
    @pytest.mark.parametrize(
        "section",
        [
            "Report Body",
            "Date",
            "Topic",
            "Problem Statement",
            "Executive Summary",
            "Discussion",
            "Sources",
        ],
    )
    def test_mandatory_section_present(self, section):
        assert section in SYSTEM_PROMPT, f"Mandatory section missing: {section!r}"

    # ------------------------------------------------------------------
    # Language rules
    # ------------------------------------------------------------------
    def test_norwegian_default_mentioned(self):
        assert "Norwegian" in SYSTEM_PROMPT
        assert "norsk" in SYSTEM_PROMPT.lower()

    def test_language_mirroring_rule_present(self):
        # The prompt must instruct the agent to respond in the user's language
        assert "SAME language" in SYSTEM_PROMPT or "same language" in SYSTEM_PROMPT.lower()

    # ------------------------------------------------------------------
    # Scientific-advisor role
    # ------------------------------------------------------------------
    def test_scientific_advisor_role(self):
        assert "scientific advisor" in SYSTEM_PROMPT.lower()

    def test_not_politician_rule(self):
        assert "NOT a politician" in SYSTEM_PROMPT or "IKKE politiker" in SYSTEM_PROMPT

    # ------------------------------------------------------------------
    # Trusted domains
    # ------------------------------------------------------------------
    @pytest.mark.parametrize(
        "domain",
        [
            "ipcc.ch",
            "nasa.gov",
            "noaa.gov",
            "nature.com",
            "science.org",
            "unep.org",
            "iea.org",
            "wmo.int",
            "carbonbrief.org",
        ],
    )
    def test_trusted_domain_mentioned(self, domain):
        assert domain in SYSTEM_PROMPT, f"Trusted domain not listed: {domain!r}"

    # ------------------------------------------------------------------
    # Executive summary / Discussion word limits
    # ------------------------------------------------------------------
    def test_executive_summary_word_limit_stated(self):
        assert "400" in SYSTEM_PROMPT

    def test_discussion_word_limit_stated(self):
        assert "500" in SYSTEM_PROMPT

    def test_sources_limit_stated(self):
        assert "20" in SYSTEM_PROMPT
