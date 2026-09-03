"""Tiny JSON file used as a fake inbox.

Real Gmail APIs come later. Orchestration is the hard part to learn.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STORE_PATH = Path(__file__).resolve().parents[2] / "data" / "store.json"

_EMPTY: dict[str, Any] = {
    "emails": [],
    "events": [],
    "files": [],
    "reminders": [],
}


def _load() -> dict[str, Any]:
    if not STORE_PATH.exists():
        STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _save(_EMPTY)
        return json.loads(json.dumps(_EMPTY))
    return json.loads(STORE_PATH.read_text(encoding="utf-8"))


def _save(data: dict[str, Any]) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
