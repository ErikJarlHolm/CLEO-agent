"""Live end-to-end integration test for CLEO.

This test is automatically SKIPPED unless both OPENAI_API_KEY and
TAVILY_API_KEY are present in the environment.  It is intended to be run
manually (or in CI once secrets are configured) to verify the full pipeline
from user query → LLM → search tools → structured response.

Run just this test:
    pytest tests/test_integration.py -v -s
"""

from __future__ import annotations

import os
import re

import pytest

# ---------------------------------------------------------------------------
# Skip markers
# ---------------------------------------------------------------------------

requires_openai = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set – skipping live integration test",
)

requires_tavily = pytest.mark.skipif(
    not os.environ.get("TAVILY_API_KEY"),
    reason="TAVILY_API_KEY not set – skipping Tavily integration test",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_section(text: str, section_keywords: list[str]) -> bool:
    """Return True if any of the section keywords appear in the response."""
    lower = text.lower()
    return any(kw.lower() in lower for kw in section_keywords)


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

@requires_openai
class TestLiveAgentResponse:
    """Full end-to-end test using real OpenAI API (no Tavily key needed)."""

    def test_english_query_returns_response(self):
        from cleo_agent.agent import run_agent

        response = run_agent(
            "What is the current atmospheric CO2 concentration?",
            verbose=False,
        )
        assert isinstance(response, str)
        assert len(response) > 100

    def test_response_contains_date_section(self):
        from cleo_agent.agent import run_agent

        response = run_agent("What is global warming?", verbose=False)
        # Date section should contain a YYYY-MM-DD pattern
        assert re.search(r"\d{4}-\d{2}-\d{2}", response), (
            "Response does not contain a date in YYYY-MM-DD format"
        )

    def test_response_contains_mandatory_sections(self):
        from cleo_agent.agent import run_agent

        response = run_agent(
            "Briefly explain what the greenhouse effect is.", verbose=False
        )

        # Each mandatory section must appear (either in English or Norwegian)
        section_checks = [
            (["Report Body", "Rapport"], "Report Body"),
            (["Executive Summary", "Oppsummering"], "Executive Summary"),
            (["Discussion", "Diskusjon"], "Discussion"),
            (["Sources", "Kilder"], "Sources"),
            (["Topic", "Emne"], "Topic"),
            (["Problem Statement", "Problemformulering"], "Problem Statement"),
        ]
        for keywords, label in section_checks:
            assert _has_section(response, keywords), (
                f"Mandatory section missing from response: {label!r}\n\n"
                f"Full response:\n{response[:500]}"
            )

    def test_norwegian_query_returns_norwegian(self):
        from cleo_agent.agent import run_agent

        response = run_agent("Hva er drivhuseffekten?", verbose=False)
        # At minimum the response should contain common Norwegian words
        norwegian_indicators = ["er", "og", "av", "til", "den", "det", "som"]
        found = sum(1 for w in norwegian_indicators if f" {w} " in response.lower())
        assert found >= 3, (
            "Response to a Norwegian query does not appear to be in Norwegian. "
            f"Norwegian word matches: {found}\n\nResponse:\n{response[:300]}"
        )

    def test_sources_section_contains_urls(self):
        from cleo_agent.agent import run_agent

        response = run_agent(
            "What does the IPCC say about sea level rise?", verbose=False
        )
        # Sources section should contain at least one URL
        urls = re.findall(r"https?://\S+", response)
        assert len(urls) >= 1, (
            f"No URLs found in Sources section.\n\nResponse:\n{response[:500]}"
        )


@requires_openai
@requires_tavily
class TestLiveAgentWithTavily:
    """Integration test that also exercises Tavily search."""

    def test_trusted_domain_search_returns_results(self):
        from cleo_agent.tools import search_trusted_climate_sources

        result = search_trusted_climate_sources.invoke(
            {"query": "IPCC AR6 global surface temperature findings"}
        )
        assert isinstance(result, str)
        assert len(result) > 50
        assert "No results found" not in result

    def test_general_search_returns_results(self):
        from cleo_agent.tools import search_web_general

        result = search_web_general.invoke(
            {"query": "climate change 2024 news"}
        )
        assert isinstance(result, str)
        assert len(result) > 50

    def test_full_pipeline_with_search(self):
        from cleo_agent.agent import run_agent

        response = run_agent(
            "What are the latest IPCC findings on Arctic warming?",
            verbose=True,
        )
        assert len(response) > 200
        # Should cite IPCC or similar trusted source
        assert any(
            domain in response.lower()
            for domain in ["ipcc", "nasa", "noaa", "arctic", "warming"]
        )
