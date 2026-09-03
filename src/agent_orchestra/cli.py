"""Command-line front door.

The graph is a library. This module is how a human talks to it.
Keeping them separate means you can later hang a web chat or a
messaging bot on the same build_graph() without rewriting agents.
"""

from __future__ import annotations

import argparse
import sys

from langchain_core.messages import AIMessage, HumanMessage

from agent_orchestra.graph import build_graph


def _print_final(messages: list) -> None:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and getattr(message, "name", None) == "supervisor":
            print(message.content)
            return
    last = messages[-1]
    print(getattr(last, "content", last))


def run_once(prompt: str) -> None:
    app = build_graph()
    result = app.invoke(
        {
            "messages": [HumanMessage(content=prompt)],
            "task": "",
            "last_worker": "",
        },
        config={"recursion_limit": 12},
    )
    _print_final(result["messages"])


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
