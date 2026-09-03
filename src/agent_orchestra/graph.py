from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from pydantic import BaseModel, Field

from agent_orchestra.config import get_model
from agent_orchestra.state import OrchestraState
from agent_orchestra.tools import (
    EMAIL_TOOLS,
    CALENDAR_TOOLS,
)


Worker = Literal["email", "calendar", "files", "reminders"]
WORKERS = {"email", "calendar"}


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

EMAIL_PROMPT = (
    "You are the email specialist. Use only email tools. "
    "When finished, reply with a short status for the lead agent."
)
CALENDAR_PROMPT = (
    "You are the calendar specialist. Use only calendar tools. "
    "When finished, reply with a short status for the lead agent."
)


def _worker_node(name: Worker, tools: list, prompt: str):
    """Build a graph node that runs one specialist, then returns to the lead.

    Why a factory: the four workers are the same shape — different tools
    and a different system prompt. One function keeps that rule obvious.
    """

    def node(state: OrchestraState) -> Command:
        agent = create_react_agent(get_model(), tools, prompt=prompt)
        task = state.get("task") or "Help with the user's latest request."
        result = agent.invoke({"messages": [HumanMessage(content=task)]})
        last = result["messages"][-1]
        report = getattr(last, "content", str(last))
        return Command(
            goto="supervisor",
            update={
                "last_worker": name,
                "messages": [
                    AIMessage(content=f"[{name}] {report}", name=name)
                ],
            },
        )

    node.__name__ = name
    return node


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

    if decision.next_worker == "finish" or decision.next_worker not in WORKERS:
        return Command(
            goto=END,
            update={"messages": [AIMessage(content=decision.task, name="supervisor")]},
        )

    return Command(
        goto=decision.next_worker,
        update={"task": decision.task, "last_worker": decision.next_worker},
    )


def build_graph():
    """Compile the state machine.

    START → supervisor ⇄ workers → END
    """
    graph = StateGraph(OrchestraState)
    graph.add_node("supervisor", supervisor)
    graph.add_node("email", _worker_node("email", EMAIL_TOOLS, EMAIL_PROMPT))
    graph.add_node("calendar", _worker_node("calendar", CALENDAR_TOOLS, CALENDAR_PROMPT))
    graph.add_edge(START, "supervisor")
    return graph.compile()
