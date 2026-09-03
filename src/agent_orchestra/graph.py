from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from pydantic import BaseModel, Field

from agent_orchestra.config import get_model
from agent_orchestra.state import OrchestraState


Worker = Literal["email", "calendar", "files", "reminders"]


class SupervisorDecision(BaseModel):
    """The only thing the lead agent is allowed to produce."""

    next_worker: Literal["email", "calendar", "files", "reminders", "finish"]
    task: str = Field(
        description=(
            "If routing: a concrete instruction for that specialist. "
            "If finish: the final answer to show the user."
        )
    )


SUPERVISOR_PROMPT = """You are the lead personal-ops agent.
The user talks only to you. You do not call tools. You assign work.

Specialists:
- email: unread mail, mark read, save drafts (does not send)
- calendar: list and add events
- files: list, read, and write notes/files
- reminders: create and list reminders

Rules:
1. Pick one specialist per turn. Multi-part requests are done in sequence.
2. Use each specialist's last report (named assistant messages) before repeating them.
3. When the user's request is satisfied, choose finish and write a clear summary in task.
4. If a specialist reported a failure, either retry with a sharper task or finish and explain.
"""


def supervisor(state: OrchestraState) -> Command:
    """Decide who works next, or stop.

    Structured output matters here. Free-form text like 'go to email'
    is easy for a model to phrase differently every time, which breaks
    routing. A schema forces a worker name the graph can match.
    """
    model = get_model().with_structured_output(SupervisorDecision)
    decision = model.invoke(
        [SystemMessage(content=SUPERVISOR_PROMPT), *state["messages"]]
    )

    # Workers are not wired yet; finish so the graph can still compile.
    return Command(
        goto=END,
        update={"messages": [AIMessage(content=decision.task, name="supervisor")]},
    )


def build_graph():
    graph = StateGraph(OrchestraState)
    graph.add_node("supervisor", supervisor)
    graph.add_edge(START, "supervisor")
    return graph.compile()
