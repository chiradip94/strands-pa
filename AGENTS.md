# strands-pa

Multi-agent chat app: Python FastAPI + strands Swarm backend, vanilla JS frontend.

## Approval Guidelines
- **Ask before every edit:** You must ask for explicit user permission EVERY single time before you modify, create, or delete any file. 
- **Present the diff first:** Show a quick summary or git-like diff of the proposed change and wait for the user to say "yes" or "approve" before writing to the disk.


## Code Modification Guidelines
- **Minimal code Changes:** Make as minimal code change as possible to achieve the functionality, if single line change can do it, attempt that
- **Use dependency injection:** Use the dependency injection library, try not to create objects on it own, use container.py to create and then inject them.
- **Be surgical:** Always make the least possible change required to solve the task. Do not rewrite or modify surrounding code blocks if they already work.
- **Keep changes short & crisp:** Prefer smaller, targeted edits over bulk rewrites.
- **Explain changes:** Every time you modify a file, you must explicitly state exactly what was changed and why it was changed. Do not skip this summary.
- **No fluff:** Do not add unrequested code comments, metadata headers, or logging lines.
- **Important** - Always follow the coding pattern, folder structure existing in the code base
- **README,md** - Keep README.md up to date. it should have a diagram of the agents too on how it looks to understand the branching clearly.
## Tool Execution
- Do not re-read files immediately after editing; trust the tool's success.
- If unsure whether a change is necessary, stop and ask the user.


## Structure

```
backend/
  agents/              Agent definitions
    all_agents.py        get_sub_agents() — factory for 5 sub-agents
    orchestrator.py      create_orchestrator() — wires agents + tools per session
    memory_graph.py      Memory Graph (extract → store → verify)
  container.py         DI container wiring everything together
  config.py            Config from .env
  main.py              FastAPI app, /ws endpoint
  mcp_servers/         MCP client connections (stdio/HTTP)
    local_servers.py     python_server (stdio), playwright_client (stdio/HTTP)
    remote_servers.py    rival_search_mcp_client, remote_time_client (HTTP)
    python_executor.py   Python code execution MCP server (FastMCP, stdio)
  services/            Business logic
    chat.py              Chat service — orchestrator per session + streaming
    confirmation.py      Human-in-the-loop via WebSocket
  tools/               Tool definitions
    browser_server.py    Playwright browser automation MCP server (FastMCP, stdio)
    cal_com.py           Cal.com REST API tools
    vector_search.py     Qdrant vector search tools
    scratchpad.py        Agent scratchpad tool (planning + notes, wired into orchestrator)
  utils/               Utilities
    get_tools.py         get_mcp_tools() — loads MCP tools from clients
    llm.py               LLM model factory
    langfuse.py          Langfuse client init
  vector_store/        Vector storage
    base.py              Abstract VectorStore
    qdrant.py            Qdrant implementation
  session_manager/     Session persistence
    mongo_session_repository.py

frontend/              Vanilla HTML/CSS/JS chat UI
  index.html, script.js, style.css
```

## Setup

- Python 3.11 (`.python-version`)
- `uv` package manager (brew-installed, not in venv). Run commands from `backend/`.
- Create `backend/.env` with: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LANGFUSE_SECRET_KEY` (plus `LANGFUSE_PUBLIC_KEY` if needed).
- Node.js 18+ with `npx` for Playwright MCP (Browser Agent). Install Firefox: `npx @playwright/mcp@latest install-browser firefox`

## Commands (run from `backend/`)

| Action | Command |
|---|---|
| Dev server | `uv run uvicorn app:app --host 0.0.0.0 --port 8000 --reload --reload-exclude validation/` |
| Frontend | `cd frontend && python3 -m http.server 8080` |
| Test swarm events | `uv run python test_swarm_events.py` |
| Test WS client | `uv run python test_ws.py` |
| Install Playwright Firefox | `npx @playwright/mcp@latest install-browser firefox` |

No test framework, no lint/typecheck config.

## Architecture

- **Entrypoint**: `backend/main.py` — FastAPI app with `lifespan` that loads MCP tools, single WebSocket endpoint at `/ws`.
- **Swarm**: Created per-query in `chat_with_agent()`. 5 sub-agents (Search, Python, Calendar, Memory, Browser) + Initial Agent. Time tools + scratchpad + file_ops + http_request wired directly into Initial Agent. `max_handoffs=10`, `max_iterations=20`.
- **DI**: `dependency-injector` `Container` provides `LLM` model singleton wired into agent constructors.
- **LLM**: `OpenAIModel` from strands (supports any OpenAI-compatible provider via `base_url`).
- **Langfuse**: Initialized at module level in `main.py` on import.
- **MCP tools**: Loaded once in `lifespan` and cached; `chat_with_agent` re-calls `load_tools()` (returns cached).
- **Browser Agent (Playwright)**: Uses `@playwright/mcp` via stdio with Firefox. Set `BROWSER_HEADLESS=true` for headless mode (WSL). Set `PLAYWRIGHT_MCP_URL=http://<windows-ip>:8931/mcp` to connect to a remote Playwright MCP server instead of stdio.
- **Event flow**: Swarm yields `TypedEvent` dicts → `_process_event()` maps to `{"type": ...}` messages → WebSocket sends JSON array to frontend.
- **Cal.com**: `CAL_API_KEY` must be set in `.env` — generate one at [app.cal.com/settings/developer/api-keys](https://app.cal.com/settings/developer/api-keys).

## WebSocket Event Protocol

`_process_event` returns a list of `{"type": ...}` messages per swarm event.

| WS type | When | Frontend action |
|---|---|---|
| `thinking` | node starts | Show "Thinking..." indicator |
| `node_start` | node starts | "🔄 {node_id} taking control" + thinking |
| `text` | agent streams text | Append to current agent bubble |
| `reasoning` | agent streams reasoning | Show in italic bubble |
| `stop` | agent/node finishes | Hide thinking, clear current bubble |
| `handoff` | handoff between agents | "🔀 from → to" + thinking |
| `done` | final result | Show final text + metadata |
| `error` | exception | Show error text |

## Known Pitfalls

- `SwarmResult.node_history` is `list[SwarmNode]` (not AgentResult). To get the last agent's text: `str(result.results[result.node_history[-1].node_id].result)`.
- `Status` enum must be serialized via `.value`, not passed raw.
- `AgentResult.message` is a `dict` (`Message`), not a string — use `str(agent_result)` to get concatenated text.
- `_process_event` changed from returning `dict|None` to returning `list[dict]`.
- Frontend connects to `ws://localhost:8000/ws` — update if backend port changes.
