"""Tiny JSON file used as a fake inbox / calendar / disk.

Real Gmail or Google Calendar APIs come later. Orchestration is the
hard part to learn; OAuth is a separate project. Workers call these
functions so you can swap in live APIs without touching the graph.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STORE_PATH = Path(__file__).resolve().parents[2] / "data" / "store.json"

_EMPTY: dict[str, Any] = {
    "emails": [
        {
            "id": "e1",
            "from": "alex@example.com",
            "subject": "Invoice for March",
            "unread": True,
            "body": "Please review the attached invoice.",
        },
        {
            "id": "e2",
            "from": "sam@example.com",
            "subject": "Lunch next week?",
            "unread": True,
            "body": "Are you free Thursday?",
        },
    ],
    "events": [
        {
            "id": "c1",
            "title": "Team standup",
            "start": "2026-09-04T10:00:00+05:30",
            "end": "2026-09-04T10:30:00+05:30",
        }
    ],
    "files": [
        {"path": "notes/todo.txt", "content": "- buy milk\n- call dentist\n"},
        {"path": "notes/ideas.txt", "content": "learn multi-agent graphs\n"},
    ],
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


def list_unread_email() -> list[dict[str, Any]]:
    return [e for e in _load()["emails"] if e.get("unread")]


def mark_email_read(email_id: str) -> str:
    data = _load()
    for email in data["emails"]:
        if email["id"] == email_id:
            email["unread"] = False
            _save(data)
            return f"Marked {email_id} as read."
    return f"No email with id {email_id}."


def draft_email(to: str, subject: str, body: str) -> str:
    data = _load()
    drafts = data.setdefault("drafts", [])
    drafts.append({"to": to, "subject": subject, "body": body})
    _save(data)
    return f"Saved draft to {to} about '{subject}'."


def list_events() -> list[dict[str, Any]]:
    return list(_load()["events"])


def add_event(title: str, start: str, end: str) -> str:
    data = _load()
    event_id = f"c{len(data['events']) + 1}"
    data["events"].append(
        {"id": event_id, "title": title, "start": start, "end": end}
    )
    _save(data)
    return f"Added event {event_id}: {title}."


def read_file(path: str) -> str:
    for item in _load()["files"]:
        if item["path"] == path:
            return item["content"]
    return f"File not found: {path}"


def write_file(path: str, content: str) -> str:
    data = _load()
    for item in data["files"]:
        if item["path"] == path:
            item["content"] = content
            _save(data)
            return f"Updated {path}."
    data["files"].append({"path": path, "content": content})
    _save(data)
    return f"Created {path}."


def list_files() -> list[str]:
    return [item["path"] for item in _load()["files"]]


def add_reminder(text: str, when: str) -> str:
    data = _load()
    reminder_id = f"r{len(data['reminders']) + 1}"
    data["reminders"].append(
        {
            "id": reminder_id,
            "text": text,
            "when": when,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _save(data)
    return f"Reminder {reminder_id} set for {when}: {text}"


def list_reminders() -> list[dict[str, Any]]:
    return list(_load()["reminders"])
