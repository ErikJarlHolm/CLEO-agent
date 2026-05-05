#!/usr/bin/env python3
"""CLEO – Climate Expert Agent  |  Command-line interface.

Examples
--------
Single question (Norwegian default):
    python main.py "Hva er tilstanden til Arktis-isen?"

Single question (English):
    python main.py "What are the main causes of global warming?"

Policy advice query:
    python main.py "Hvilke tiltak bør Norge prioritere for å redusere klimagassutslipp?"

Interactive session:
    python main.py --interactive

Use a specific model:
    python main.py --model gpt-4-turbo "Explain ocean acidification"

Show agent reasoning:
    python main.py --verbose "What is the IPCC AR6 key finding on 1.5 degrees?"
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

load_dotenv()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cleo",
        description="CLEO – International Climate Expert Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "query",
        nargs="?",
        metavar="QUESTION",
        help=(
            "Climate question or request.  Omit when using --interactive.  "
            "Default language is Norwegian; write in English for English replies."
        ),
    )
    parser.add_argument(
        "--model",
        default=None,
        metavar="MODEL",
        help="OpenAI model name (default: gpt-4o or $CLEO_MODEL).",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Start an interactive multi-turn session.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print the agent's internal reasoning steps.",
    )
    return parser


def _run_once(query: str, model_override: str | None, verbose: bool) -> None:
    """Run a single query and print the result."""
    from cleo_agent.agent import DEFAULT_MODEL, run_agent

    model = model_override or DEFAULT_MODEL
    print(f"\n[CLEO] Behandler spørsmål / Processing query …\n", flush=True)
    response = run_agent(query, model=model, verbose=verbose)
    print(response)


def _run_interactive(model_override: str | None, verbose: bool) -> None:
    """Start an interactive session that keeps the conversation going."""
    from cleo_agent.agent import DEFAULT_MODEL, create_agent

    model = model_override or DEFAULT_MODEL

    print("=" * 60)
    print("  CLEO – Klimaekspert / Climate Expert Agent")
    print("=" * 60)
    print("Skriv spørsmålet ditt / Type your question.")
    print("Skriv 'avslutt', 'quit' eller 'exit' for å avslutte.\n")

    # Create the agent once and reuse it so the LLM context persists
    agent = create_agent(model=model, verbose=verbose)
    from langchain_core.messages import AIMessage, HumanMessage

    chat_history: list[HumanMessage | AIMessage] = []

    while True:
        try:
            query = input("Du / You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAvslutt / Goodbye!")
            break

        if not query:
            continue
        if query.lower() in {"avslutt", "quit", "exit", "q"}:
            print("Avslutt / Goodbye!")
            break

        print("\n[CLEO] Behandler / Processing …\n", flush=True)
        result = agent.invoke({"input": query, "chat_history": chat_history})
        response = result["output"]
        print(response)
        print()

        # Maintain conversation history using simple human/AI message objects
        chat_history.append(HumanMessage(content=query))
        chat_history.append(AIMessage(content=response))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.interactive:
        _run_interactive(args.model, args.verbose)
    elif args.query:
        _run_once(args.query, args.model, args.verbose)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
