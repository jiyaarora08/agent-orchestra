"""Command-line front door."""

from __future__ import annotations

import argparse
import sys

from langchain_core.messages import HumanMessage

from agent_orchestra.graph import build_graph


def run_once(prompt: str) -> None:
    app = build_graph()
    result = app.invoke(
        {
            "messages": [HumanMessage(content=prompt)],
            "task": "",
            "last_worker": "",
        }
    )
    print(result["messages"][-1].content)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send an instruction to the personal-ops supervisor."
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="What you want done. Omit to type interactively.",
    )
    args = parser.parse_args()
    prompt = " ".join(args.prompt).strip()
    if not prompt:
        prompt = input("You: ").strip()
    if not prompt:
        print("No instruction given.", file=sys.stderr)
        sys.exit(1)
    run_once(prompt)


if __name__ == "__main__":
    main()
