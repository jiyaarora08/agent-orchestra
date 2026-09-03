# Agent Orchestra

You talk to **one lead agent**. That lead does not rummage through email, calendars, files, and reminders itself. It **assigns** those jobs to specialists, then answers you.

This README is the tutorial: what we built, why each piece exists, and what you should do next.

## The idea in one picture

```
You
  │  "Remind me to call mom tomorrow, and what's unread?"
  ▼
Lead (supervisor)
  │  chooses ONE specialist per turn
  ├─► Email worker     → inbox tools only
  ├─► Calendar worker  → event tools only
  ├─► Files worker     → read/write notes
  └─► Reminders worker → reminder tools only
        │
        ▼
Lead summarizes → you
```

This pattern is called a **supervisor (or orchestrator) with specialist workers**.

## Why not one giant agent?

A single agent with every tool will:

- Mix jobs ("I'll email your calendar invite into a reminder file")
- Waste tokens staring at tools it does not need
- Become hard to debug — you cannot tell *who* made a bad call

Specialists are boring on purpose. Boring agents are easier to trust.

## Why LangGraph?

The lead and the workers are a **state machine**:

1. Start at the lead.
2. Lead picks a worker or finishes.
3. Worker runs tools, reports back.
4. Repeat until the lead says the request is done.

LangGraph makes that loop explicit (nodes and edges). You can print the path later when something routes wrong. A free-form "agents chatting in a list" design hides that path.

## What we deliberately skipped

- No editor-specific agent runtimes, plugins, or assistant badges in this repo. It should look like ordinary Python you maintain yourself.
- No live Gmail / Google Calendar yet. OAuth is a weekend of its own. Workers talk to a local JSON fake inbox in `data/store.json` (created on first run). Swap that module for real APIs later without rewriting the graph.

## Folders (and why each file exists)

| Path | Job |
| --- | --- |
| `pyproject.toml` | Declares the package and dependencies so `pip install -e .` works. |
| `.env.example` | Shows which secrets to set. Copied to `.env`, which is gitignored. |
| `.gitignore` | Keeps virtualenv, secrets, and the fake data file out of git. |
| `src/agent_orchestra/state.py` | The shared clipboard: chat messages + current task. |
| `src/agent_orchestra/config.py` | Builds the chat model from environment variables. |
| `src/agent_orchestra/store.py` | Fake inbox / calendar / files / reminders. |
| `src/agent_orchestra/tools.py` | Python functions the model is allowed to call. |
| `src/agent_orchestra/graph.py` | Lead + workers + wiring. This is the product. |
| `src/agent_orchestra/cli.py` | Lets you type an instruction in the terminal. |

`src/` layout exists so your project code does not get confused with a folder named `agent_orchestra` inside tests or a venv.

## Setup (do this in order)

### 1. Create a virtual environment

Isolates this project's packages from the rest of your machine.

```powershell
cd C:\Users\arora\Projects\agent-orchestra
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install the package in editable mode

Editable (`-e`) means you can edit Python files and run them without reinstalling.

```powershell
pip install -e .
```

### 3. Configure the model

```powershell
copy .env.example .env
```

Edit `.env`:

- `OPENAI_API_KEY` — required
- `OPENAI_BASE_URL` — leave the OpenAI default, or point at any compatible server
- `OPENAI_MODEL` — a model that server actually hosts

Temperature is fixed at `0` in code so routing is less random while you learn.

### 4. Talk to the lead

```powershell
python -m agent_orchestra "What unread email do I have, and remind me to call mom tomorrow 9am"
```

Or:

```powershell
orchestra "List my files and add a calendar event called Focus time from 2026-09-04T15:00:00+05:30 to 2026-09-04T16:00:00+05:30"
```

Watch `data/store.json` after a run. If a tool really ran, that file changes. That is your proof, not the model's confident tone.

## How a single request flows

Take: *"What's unread, and remind me to call mom tomorrow?"*

1. **CLI** wraps your sentence in a `HumanMessage` and calls `graph.invoke`.
2. **Lead** reads the message. It cannot list email itself. It outputs something like `{ next_worker: "email", task: "List unread mail" }`.
3. **Graph** jumps to the `email` node because that name matches a node.
4. **Email worker** is a small ReAct loop: think → maybe call `list_unread_email` → see the result → write a short status.
5. **Handoff:** only that short status goes back to the lead, tagged `[email] ...`. Tool dumps stay inside the worker so the lead does not drown.
6. **Lead** still sees an unfinished reminder, so it routes to `reminders` with a new task.
7. **Reminders worker** calls `add_reminder`.
8. **Lead** chooses `finish` and writes the user-facing answer.
9. **CLI** prints the message named `supervisor`.

The recursion limit (`12`) is a safety cap. If the lead and a worker argue forever, the run stops instead of burning money.

## Why structured routing?

The lead uses a Pydantic schema (`SupervisorDecision`) instead of "please go to the email agent". Graphs need **stable labels** (`email`, `calendar`, `finish`). Schemas turn a chat model into something closer to a function that returns an enum.

## What you should do next (in this order)

1. **Run the two example prompts above** and open `data/store.json`. Confirm tools did work.
2. **Break routing on purpose.** Ask something that needs two workers. If the lead skips one, tighten `SUPERVISOR_PROMPT` in `graph.py` — that file is the steering wheel.
3. **Add a fifth worker** (for example `travel` with a mock `search_flights` tool). Copy an existing node. This is how you learn the pattern: same graph, new specialist.
4. **Replace `store.py`** with a real API for *one* domain only (start with calendar *or* email, not both). Keep the tool *names* the same so the worker prompt barely changes.
5. **Add a check node** after workers: a tiny function (not even an LLM) that verifies JSON was written. Deterministic checks catch "I set the reminder" lies.
6. **Only then** consider a chat UI. The CLI is enough until routing is boringly correct.

## Design rules to keep

- One worker, one domain, few tools.
- The lead never gets the workers' tools.
- Secrets stay in `.env`, never in git.
- Fake backends first; live accounts second.
