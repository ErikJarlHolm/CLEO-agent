"""Tests for cleo_agent/tools.py

All external network calls (Tavily, DuckDuckGo) are mocked so the tests run
without any API keys or internet access.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from cleo_agent.tools import (
    CLEO_TOOLS,
    TRUSTED_DOMAINS,
    _format_ddg_results,
    _format_tavily_results,
    _tavily_available,
    search_trusted_climate_sources,
    search_web_general,
)


# ---------------------------------------------------------------------------
# TRUSTED_DOMAINS list
# ---------------------------------------------------------------------------

class TestTrustedDomains:
    def test_is_list_of_strings(self):
        assert isinstance(TRUSTED_DOMAINS, list)
        assert all(isinstance(d, str) for d in TRUSTED_DOMAINS)

    def test_key_domains_present(self):
        required = ["ipcc.ch", "nasa.gov", "noaa.gov", "nature.com", "unep.org"]
        for domain in required:
            assert domain in TRUSTED_DOMAINS, f"Missing: {domain}"

    def test_no_duplicates(self):
        assert len(TRUSTED_DOMAINS) == len(set(TRUSTED_DOMAINS))


# ---------------------------------------------------------------------------
# CLEO_TOOLS list
# ---------------------------------------------------------------------------

class TestCleoTools:
    def test_tools_list_length(self):
        assert len(CLEO_TOOLS) == 2

    def test_tool_names(self):
        names = {t.name for t in CLEO_TOOLS}
        assert "search_trusted_climate_sources" in names
        assert "search_web_general" in names

    def test_tools_have_descriptions(self):
        for tool in CLEO_TOOLS:
            assert tool.description, f"Tool {tool.name!r} has no description"

    def test_tools_accept_string_input(self):
        for tool in CLEO_TOOLS:
            # LangChain tools built with @tool expose args_schema
            schema = tool.args_schema.model_json_schema()
            assert "query" in schema.get("properties", {}), (
                f"Tool {tool.name!r} does not have a 'query' parameter"
            )


# ---------------------------------------------------------------------------
# _tavily_available helper
# ---------------------------------------------------------------------------

class TestTavilyAvailable:
    def test_returns_false_without_key(self, monkeypatch):
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        assert _tavily_available() is False

    def test_returns_true_with_key(self, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key")
        assert _tavily_available() is True

    def test_returns_false_with_empty_key(self, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "")
        assert _tavily_available() is False


# ---------------------------------------------------------------------------
# _format_tavily_results
# ---------------------------------------------------------------------------

class TestFormatTavilyResults:
    def test_empty_results(self):
        result = _format_tavily_results({"results": []})
        assert "No results found" in result or "Ingen resultater" in result

    def test_missing_results_key(self):
        result = _format_tavily_results({})
        assert "No results found" in result or "Ingen resultater" in result

    def test_single_result(self):
        data = {
            "results": [
                {
                    "title": "IPCC AR6 Summary",
                    "url": "https://www.ipcc.ch/ar6/",
                    "content": "Global warming of 1.5°C …",
                }
            ]
        }
        result = _format_tavily_results(data)
        assert "IPCC AR6 Summary" in result
        assert "https://www.ipcc.ch/ar6/" in result
        assert "1.5°C" in result

    def test_multiple_results_separated(self):
        data = {
            "results": [
                {"title": "A", "url": "https://a.com", "content": "Content A"},
                {"title": "B", "url": "https://b.com", "content": "Content B"},
            ]
        }
        result = _format_tavily_results(data)
        assert "---" in result  # separator between results
        assert "Content A" in result
        assert "Content B" in result

    def test_handles_missing_fields_gracefully(self):
        data = {"results": [{}]}
        result = _format_tavily_results(data)
        assert "N/A" in result


# ---------------------------------------------------------------------------
# _format_ddg_results
# ---------------------------------------------------------------------------

class TestFormatDdgResults:
    def test_empty_list(self):
        result = _format_ddg_results([])
        assert "No results found" in result or "Ingen resultater" in result

    def test_single_result(self):
        items = [
            {
                "title": "NASA Climate",
                "href": "https://climate.nasa.gov",
                "body": "Arctic sea ice …",
            }
        ]
        result = _format_ddg_results(items)
        assert "NASA Climate" in result
        assert "https://climate.nasa.gov" in result
        assert "Arctic sea ice" in result

    def test_handles_missing_fields(self):
        result = _format_ddg_results([{}])
        assert "N/A" in result


# ---------------------------------------------------------------------------
# search_trusted_climate_sources  (mocked)
# ---------------------------------------------------------------------------

MOCK_TAVILY_RESPONSE = {
    "results": [
        {
            "title": "IPCC AR6 – Climate Change 2021",
            "url": "https://www.ipcc.ch/report/ar6/",
            "content": "The global surface temperature has increased faster since 1970.",
        }
    ]
}

MOCK_DDG_RESPONSE = [
    {
        "title": "NASA – Global Climate Change",
        "href": "https://climate.nasa.gov",
        "body": "CO₂ concentration is now above 420 ppm.",
    }
]


class TestSearchTrustedClimateSources:
    def test_uses_tavily_when_key_present(self, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-fake")

        mock_client = MagicMock()
        mock_client.search.return_value = MOCK_TAVILY_RESPONSE

        # TavilyClient is imported lazily inside the function, so patch at source
        with patch("tavily.TavilyClient", return_value=mock_client):
            result = search_trusted_climate_sources.invoke(
                {"query": "Arctic sea ice trends"}
            )

        assert "IPCC AR6" in result
        # Verify include_domains was passed (trusted-domain filtering)
        call_kwargs = mock_client.search.call_args.kwargs
        assert "include_domains" in call_kwargs
        assert "ipcc.ch" in call_kwargs["include_domains"]

    def test_falls_back_to_ddg_without_key(self, monkeypatch):
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.__enter__ = MagicMock(return_value=mock_ddgs_instance)
        mock_ddgs_instance.__exit__ = MagicMock(return_value=False)
        mock_ddgs_instance.text.return_value = iter(MOCK_DDG_RESPONSE)

        # DDGS is imported lazily inside the function, so patch at source
        with patch("duckduckgo_search.DDGS", return_value=mock_ddgs_instance):
            result = search_trusted_climate_sources.invoke(
                {"query": "Arctic sea ice trends"}
            )

        assert "NASA" in result
        # Verify domain hints are appended to the query
        actual_query = mock_ddgs_instance.text.call_args.args[0]
        assert "site:" in actual_query

    def test_returns_error_string_on_ddg_exception(self, monkeypatch):
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        with patch("duckduckgo_search.DDGS", side_effect=RuntimeError("network error")):
            result = search_trusted_climate_sources.invoke({"query": "test"})

        assert "Search failed" in result or "mislyktes" in result


# ---------------------------------------------------------------------------
# search_web_general  (mocked)
# ---------------------------------------------------------------------------

class TestSearchWebGeneral:
    def test_uses_tavily_when_key_present(self, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "tvly-fake")

        mock_client = MagicMock()
        mock_client.search.return_value = MOCK_TAVILY_RESPONSE

        with patch("tavily.TavilyClient", return_value=mock_client):
            result = search_web_general.invoke({"query": "latest IPCC report"})

        assert "IPCC AR6" in result
        # General search must NOT restrict to trusted domains
        call_kwargs = mock_client.search.call_args.kwargs
        assert "include_domains" not in call_kwargs

    def test_falls_back_to_ddg_without_key(self, monkeypatch):
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.__enter__ = MagicMock(return_value=mock_ddgs_instance)
        mock_ddgs_instance.__exit__ = MagicMock(return_value=False)
        mock_ddgs_instance.text.return_value = iter(MOCK_DDG_RESPONSE)

        with patch("duckduckgo_search.DDGS", return_value=mock_ddgs_instance):
            result = search_web_general.invoke({"query": "climate policy"})

        assert "NASA" in result

    def test_returns_error_string_on_ddg_exception(self, monkeypatch):
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)

        with patch("duckduckgo_search.DDGS", side_effect=RuntimeError("timeout")):
            result = search_web_general.invoke({"query": "test"})

        assert "Search failed" in result or "mislyktes" in result
