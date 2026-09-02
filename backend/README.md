# Orchestrator — Backend (Phases 1–5)

The agent architecture: a **Supervisor** decomposes a request into a
dependency-aware plan, **Specialists** execute subtasks with real tool access, a
**Reviewer** grades each output, and the whole thing runs as a **LangGraph**
state machine. LLM providers are swappable; Groq's free tier is the default.

## Layout

```
app/
  config.py            env-driven settings
  llm/                 provider-agnostic LLM layer (base, groq, echo, factory)
  models/              Pydantic v2 schemas (plan, tools, review, escalation, state)
  tools/               registry + real built-ins, with an invocation log
                       (file_read/write, calculator, python_exec, http_get,
                        web_search [keyless DuckDuckGo], db_query [SQLite])
  agents/              supervisor, specialist, reviewer
  memory/              working (in-mem/Redis) + long-term semantic memory
                       (offline vector store or ChromaDB), lifecycle, recall
  hitl/                approval queue (pauses a run), graded levels, chat panel
  observability/       trace tree (spans), token/cost tracking, analytics, store
  db/                  SQLAlchemy persistence (SQLite / Supabase-Postgres)
  dataset/             task schema, loader, and the eval harness
  orchestration/       the LangGraph graph
data/agentic_tasks/    the generated 72-task dataset (tasks.jsonl)
scripts/generate_dataset.py   template generator (deterministic, offline)
eval/run_harness.py    runs the dataset, writes eval/report.json
scripts/demo.py        run one task end-to-end from the CLI
tests/                 unit + offline end-to-end tests
```

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows;  source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
copy .env.example .env            # cp on macOS/Linux
```

Then either run **offline** (no key) by setting `LLM_PROVIDER=echo` in `.env`,
or get a free Groq key at https://console.groq.com/keys, set
`LLM_PROVIDER=groq` and `GROQ_API_KEY=...`.

## Run

```bash
python -m scripts.demo "Compare three vendors' pricing and flag hidden fees"
```

Prints the plan, per-subtask execution + review scores, any escalations, the
tool-call log, and the synthesised final answer.

## Run the API (streams to the frontend)

```bash
uvicorn app.api.main:app --reload --port 8000
```

- `GET /health` — liveness + active provider
- `GET /api/tasks` — recent task runs (from the database)
- `GET /api/tools` — the tool registry
- `POST /api/tasks/stream` — run a task, streamed as Server-Sent Events
- `GET /api/memory` — long-term memories (ranked by importance)
- `DELETE /api/memory/{id}` — remove a memory (data-removal)
- `POST /api/memory/maintain` — consolidate near-duplicates and prune stale ones
- `GET /api/approvals` — runs paused awaiting a human decision
- `POST /api/approvals/{id}/resolve` — approve / reject / modify / take_over
- `POST /api/approvals/{id}/chat` — ask the agent about a pending decision
- `GET /api/traces` / `GET /api/traces/{id}` — execution trace trees
- `GET /api/analytics` — aggregate cost, latency, tool-usage, escalation rate
- `GET /api/eval/report` — the eval-harness report (if generated)

## Dataset & eval harness (§6)

```bash
python -m scripts.generate_dataset     # writes data/agentic_tasks/tasks.jsonl (72 tasks)
python -m eval.run_harness             # runs the dataset, writes eval/report.json
python -m eval.run_harness --limit 20  # quick subset
```

The harness reports success / escalation / cost / latency by category and tier,
plus the memory result: recall coverage on repeated task families (offline echo
run: 100% recall on repeat occurrences, 0% on first).

## Database (tasks, traces, approvals)

Every run persists to a real database via SQLAlchemy — **SQLite by default**
(no setup, file under `_data/`), swappable to **Supabase / Postgres** with one
env var:

```
# .env — from Supabase: Settings → Database → Connection string (URI)
DATABASE_URL=postgresql+psycopg://postgres:<PASSWORD>@db.<REF>.supabase.co:5432/postgres
```

Tables (`tasks`, `traces`, `approvals`) are auto-created on startup. The trace
explorer, analytics, and replay all read from this store; set `STORE_BACKEND=file`
to fall back to JSON files.

The desktop's **New Task** app calls `POST /api/tasks/stream` and animates the
constellation from the live events. It expects the API at
`http://localhost:8000` (override with `NEXT_PUBLIC_API_BASE` in the frontend).

## Test

```bash
pytest -q
```

Tests run offline against the deterministic `echo` provider — no key or network
needed. `test_graph.py` runs the whole graph end-to-end and is skipped if
`langgraph` isn't installed yet.

## Swapping providers

The agents only depend on `app.llm.base.LLMProvider`. To add Anthropic/OpenAI/
Ollama later, implement that interface and register it in `app/llm/factory.py`;
no agent code changes.
