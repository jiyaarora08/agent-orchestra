"""Tools the specialists are allowed to call.

A tool is a Python function with a description the model can read.
We keep each worker's tool list tiny on purpose.
"""

from langchain_core.tools import tool

from agent_orchestra import store


@tool
def list_unread_email() -> str:
    """List unread emails in the inbox."""
    items = store.list_unread_email()
    if not items:
        return "No unread email."
    lines = [
        f"{e['id']}: {e['subject']} (from {e['from']})" for e in items
    ]
    return "\n".join(lines)


@tool
def mark_email_read(email_id: str) -> str:
    """Mark one email as read by its id."""
    return store.mark_email_read(email_id)


@tool
def draft_email(to: str, subject: str, body: str) -> str:
    """Save an email draft. Does not send."""
    return store.draft_email(to, subject, body)


EMAIL_TOOLS = [list_unread_email, mark_email_read, draft_email]


@tool
def list_calendar_events() -> str:
    """List calendar events."""
    events = store.list_events()
    if not events:
        return "No events."
    return "\n".join(
        f"{e['id']}: {e['title']} ({e['start']} → {e['end']})" for e in events
    )


@tool
def add_calendar_event(title: str, start: str, end: str) -> str:
    """Add a calendar event. start and end should be ISO-8601 datetimes."""
    return store.add_event(title, start, end)


CALENDAR_TOOLS = [list_calendar_events, add_calendar_event]
