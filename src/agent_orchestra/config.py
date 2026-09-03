"""Load settings from the environment.

Why a tiny config module: workers should not hard-code model names or
API hosts. You can switch providers by editing .env, not by rewriting
agent prompts.
"""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_model() -> ChatOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "replace-me":
        raise RuntimeError(
            "Set OPENAI_API_KEY in a .env file (copy .env.example). "
            "Any OpenAI-compatible key works."
        )

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=api_key,
        base_url=os.getenv("OPENAI_BASE_URL") or None,
        temperature=0,
    )
