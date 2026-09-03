"""Shared graph state.

LangGraph is a state machine. Every node reads this object and returns
updates. Keeping one schema for the whole crew means the supervisor and
workers speak the same language.
"""

from typing import Annotated, Literal

from langgraph.graph import MessagesState


WorkerName = Literal["email", "calendar", "files", "reminders"]


class OrchestraState(MessagesState):
    """Conversation plus routing fields.

    We inherit MessagesState so LangGraph appends chat messages for us.
    Extra fields are ours:

    - task: the latest instruction the supervisor handed a worker
    - last_worker: who just ran, so the supervisor can avoid loops
    """

    task: str
    last_worker: Annotated[str, "name of the last specialist that ran"]
