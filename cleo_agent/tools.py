"""Search tools for the CLEO climate expert agent.

Provides two LangChain-compatible tools:

* ``search_trusted_climate_sources`` – Searches a curated list of trusted
  scientific and intergovernmental domains via Tavily when ``TAVILY_API_KEY``
  is present in the environment.  Falls back to DuckDuckGo (no key needed)
  while still appending domain-preference hints to the query.

* ``search_web_general`` – Unrestricted web search for supplementary
  information.  Uses Tavily when available, otherwise DuckDuckGo.
"""

from __future__ import annotations

import json
import os

from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# Domains we always prefer when searching for climate science information
# ---------------------------------------------------------------------------
TRUSTED_DOMAINS: list[str] = [
    "ipcc.ch",
    "nasa.gov",
    "noaa.gov",
    "nature.com",
    "science.org",
    "who.int",
    "worldbank.org",
    "unep.org",
    "iea.org",
    "wmo.int",
    "climate.gov",
    "carbonbrief.org",
    "un.org",
    "science.sciencemag.org",
    "essd.copernicus.org",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _format_tavily_results(results: dict) -> str:
    """Convert a Tavily search response to a readable string."""
    items = results.get("results", [])
    if not items:
        return "Ingen resultater funnet. / No results found."
    parts = []
    for item in items:
        parts.append(
            f"Tittel / Title: {item.get('title', 'N/A')}\n"
            f"URL: {item.get('url', 'N/A')}\n"
            f"Innhold / Content: {item.get('content', 'N/A')}"
        )
    return "\n\n---\n\n".join(parts)


def _format_ddg_results(results: list) -> str:
    """Convert a DuckDuckGo search response to a readable string."""
    if not results:
        return "Ingen resultater funnet. / No results found."
    parts = []
    for item in results:
        parts.append(
            f"Tittel / Title: {item.get('title', 'N/A')}\n"
            f"URL: {item.get('href', 'N/A')}\n"
            f"Innhold / Content: {item.get('body', 'N/A')}"
        )
    return "\n\n---\n\n".join(parts)


def _tavily_available() -> bool:
    return bool(os.environ.get("TAVILY_API_KEY"))


# ---------------------------------------------------------------------------
# Public LangChain tools
# ---------------------------------------------------------------------------

@tool
def search_trusted_climate_sources(query: str) -> str:
    """Search trusted scientific sources for climate and environmental information.

    Preferred domains include IPCC, NASA, NOAA, Nature, Science, WHO, UNEP, IEA,
    WMO and Carbon Brief.  Use this tool for factual questions about climate
    change, greenhouse gas emissions, climate impacts, and mitigation solutions.
    """
    if _tavily_available():
        from tavily import TavilyClient  # imported lazily to keep startup fast

        client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        results = client.search(
            query,
            max_results=10,
            search_depth="advanced",
            include_domains=TRUSTED_DOMAINS,
        )
        return _format_tavily_results(results)

    # Fallback: DuckDuckGo with domain hints appended to the query
    try:
        from duckduckgo_search import DDGS

        domain_hint = " site:" + " OR site:".join(TRUSTED_DOMAINS[:5])
        with DDGS() as ddgs:
            results = list(ddgs.text(query + domain_hint, max_results=10))
        return _format_ddg_results(results)
    except Exception as exc:
        return f"Søk mislyktes / Search failed: {exc}"


@tool
def search_web_general(query: str) -> str:
    """Search the web broadly for supplementary climate information.

    Use this tool when the trusted-domain search does not return sufficient
    results, or when looking for recent news, policy documents, or national
    reports that may not be hosted on the primary scientific domains.
    """
    if _tavily_available():
        from tavily import TavilyClient

        client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        results = client.search(
            query,
            max_results=10,
            search_depth="advanced",
        )
        return _format_tavily_results(results)

    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=10))
        return _format_ddg_results(results)
    except Exception as exc:
        return f"Søk mislyktes / Search failed: {exc}"


# Convenience list for use in the agent
CLEO_TOOLS = [search_trusted_climate_sources, search_web_general]
