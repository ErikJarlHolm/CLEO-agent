"""Core agent logic for CLEO – Climate Expert Agent.

Usage
-----
>>> from cleo_agent.agent import run_agent
>>> response = run_agent("Hva er status for Arktis-isen?")
>>> print(response)
"""

from __future__ import annotations

import os
from datetime import datetime

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from .prompts import SYSTEM_PROMPT
from .tools import CLEO_TOOLS

# Load .env automatically when this module is imported so the agent works
# whether invoked from the CLI or imported as a library.
load_dotenv()

# ---------------------------------------------------------------------------
# Default model – can be overridden via the CLEO_MODEL environment variable
# or by passing ``model`` to :func:`create_agent` / :func:`run_agent`.
# ---------------------------------------------------------------------------
DEFAULT_MODEL = os.environ.get("CLEO_MODEL", "gpt-4o")


def create_agent(
    model: str = DEFAULT_MODEL,
    temperature: float = 0.0,
    verbose: bool = False,
) -> AgentExecutor:
    """Create and return a configured CLEO AgentExecutor.

    Parameters
    ----------
    model:
        OpenAI model identifier, e.g. ``"gpt-4o"`` or ``"gpt-4-turbo"``.
    temperature:
        Sampling temperature for the LLM (0 = deterministic).
    verbose:
        If ``True``, LangChain will print the agent's internal reasoning steps.

    Returns
    -------
    AgentExecutor
        A fully configured LangChain agent ready to ``invoke()``.
    """
    current_date = datetime.now().strftime("%Y-%m-%d")
    system_prompt = SYSTEM_PROMPT.format(current_date=current_date)

    llm = ChatOpenAI(model=model, temperature=temperature)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_openai_tools_agent(llm, CLEO_TOOLS, prompt)

    return AgentExecutor(
        agent=agent,
        tools=CLEO_TOOLS,
        verbose=verbose,
        max_iterations=8,
        handle_parsing_errors=True,
    )


def run_agent(
    query: str,
    model: str = DEFAULT_MODEL,
    verbose: bool = False,
) -> str:
    """Run CLEO with a single query and return the formatted response string.

    Parameters
    ----------
    query:
        The user's climate question or request (any language).
    model:
        OpenAI model identifier.
    verbose:
        Print agent reasoning steps to stdout.

    Returns
    -------
    str
        The agent's formatted response following the mandatory CLEO format.
    """
    agent = create_agent(model=model, verbose=verbose)
    result = agent.invoke({"input": query})
    return result["output"]
