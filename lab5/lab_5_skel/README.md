# Gem — AI Teaching Assistant

An agent-based chatbot with a fixed persona ("Gem", a computer science professor),
retrieval-augmented generation over a local knowledge base, tool calling, token/cost
tracking, and context compression. Built for the AI Academy final project
(Session 6 — Orchestration and Automation).

## 1. Architecture

```
                    ┌────────────┐
   CLI (main.py) ──▶│            │
                    │   Agent    │──▶ ConversationContext (history, token/cost tracking,
  Browser (static/) │  (agent.py)│    compression, session persistence)
   via api.py ──────▶            │
                    └─────┬──────┘
                          │
              ┌───────────┼────────────┐
              ▼                        ▼
     EmbeddingsClient            Tools (tools/)
     (semantic_search)           web_search, fetch_page,
              │                  check_python_code,
              ▼                  student records, datetime,
   qwen3-embedding (Ollama,      knowledge_search
   local, http://localhost:11434)
                                        │
                                        ▼
                              gpt-5-mini (Azure AI Foundry)
```

Two entry points share the same `Agent` + `ConversationContext` classes:

- **`main.py`** — command-line interface, single user, session saved to
  `sessions/cli_default.json`.
- **`api.py`** — OpenAI-compatible HTTP backend (FastAPI), one `Agent` per user, and
  also serves the [static web UI](#8-web-ui) directly (`static/index.html`) — a single
  process is both the API and the frontend.

### Running it

```powershell
$env:CHATGPT_API_KEY = "your-azure-key"
# Ollama must be running locally with qwen3-embedding:latest pulled

python main.py                              # CLI
uvicorn api:app --host 127.0.0.1 --port 8000 # HTTP backend + web UI at http://127.0.0.1:8000/
```

## 2. Scalability & Extensibility

The architecture is designed so new capabilities are added by **dropping in a file**,
not by editing existing code.

### How to add a tool

1. Create a new file in `tools/`, following the pattern in
   [`tools/lucky_number_tool.py`](tools/lucky_number_tool.py): a plain Python function,
   plus a `Tool(...)` instance describing its name, description, JSON-schema
   parameters, and callback.
2. Register it in [`tools/tools.py`](tools/tools.py): import the module and add the
   `Tool` instance to the `tools` list.

[`tools/file_tool.py`](tools/file_tool.py) is the one exception to this flat pattern:
`list_uploaded_files`/`read_uploaded_file` must only ever see one user's own uploaded
files, so instead of a module-level `Tool` instance, it exports a factory
`make_file_tools(user_id)` that both `api.py::get_agent` and `main.py::main` call when
building each `Agent`, closing over that specific user's upload folder.

That's it — `Agent.__init__` builds its dispatch dict from whatever is in `tools`, and
`LLMClient` advertises it to the model automatically.

### How to add a knowledge document

1. Write a `.md` file under `knowledge/facts/` or `knowledge/procedures/`.
2. Add an entry to the corresponding `registry.json`: `id` (matches the filename),
   `name` (used as the markdown section heading), `description`, and `always_load`
   (`true` = injected into every system prompt, `false` = only retrieved via semantic
   search when relevant).

No code changes required — `conversation_context.py::assemble_system_prompt` and
`document_chunker.py::load_n_chunk_docs` both read the registry dynamically.

## 3. Cost Optimization

Several layers work together to keep the prompt small:

- **`always_load` facts** (currently just Course Facts) are injected into every
  system prompt — measured at **265 tokens**. Everything else is retrieved on demand.
- **Semantic search + `TOP_N`**: only the most relevant chunks are added per message,
  not the whole knowledge base. `TOP_N` was reduced from 20 to **4**
  (`config.py`) — with ~123 tokens/chunk on average, that's roughly 300–650 tokens
  of retrieved context per message instead of the full knowledge base.
- **`SIMILARITY_THRESHOLD = 0.5`** discards irrelevant chunks entirely rather than
  padding the prompt with noise (see the [tuning experiment](#4-retrieval-thresholds--tuning) below).
- **No injection on empty retrieval**: `agent.py::process_message` sends a short
  fallback system message ("no relevant knowledge found") instead of nothing, so the
  model doesn't silently invent facts, but it also never pastes an empty or generic
  KB dump.
- **Context compression** (`ConversationContext.compress_history`, see below) caps
  the total conversation size the model has to pay for on every single turn, not just
  the first one.

Measured on this knowledge base (`knowledge/`, 7 documents):

| | Tokens |
|---|---|
| Full knowledge base (all documents) | 4360 |
| Always-load (system prompt, every message) | 265 |
| Retrieved context, `TOP_N=4` (typical) | ~300–650 |

So a typical message pays for roughly 265 + 300–650 tokens of knowledge, not 4360 —
about an 80–85% reduction versus loading everything.

## 4. Retrieval Thresholds & Tuning

Ran `EmbeddingsClient.semantic_search` directly against `embeddings.json` with three
questions that map onto retrievable (non always-load) documents, and three unrelated
questions, to see where relevant vs. irrelevant similarity scores land.

| Question | Relevant? | Top similarity score | Chunks above threshold |
|---|---|---|---|
| "How do I handle exceptions when opening a file in Python?" | yes (Python Best Practices) | 0.669 | 3 |
| "What's the time complexity of a dictionary lookup?" | yes (Algorithm Complexity) | 0.708 | 4 (of 6 above 0.5, capped by `TOP_N`) |
| "What does the code review procedure check before grading?" | yes (Code Review Procedure) | 0.813 | 4 (of 9 above 0.5, capped by `TOP_N`) |
| "What's the best recipe for carbonara?" | no | — | 0 |
| "Who won the 2022 World Cup?" | no | — | 0 |
| "What's the weather like in Bucharest today?" | no | — | 0 |

Relevant questions score **0.67–0.81**, well above the `SIMILARITY_THRESHOLD = 0.5`
cutoff; the three unrelated questions retrieve **zero** chunks above threshold and
correctly fall back to the "no relevant knowledge found" path in `agent.py`. This
confirms 0.5 is a safe cutoff for this embedding model — it doesn't need to be looser
to catch relevant content, and it already filters out unrelated questions completely.
Reproduce with:

```powershell
python -c "from embeddings_client import EmbeddingsClient; c = EmbeddingsClient(); [print(q, '->', c.semantic_search(q)[:1]) for q in ['How do I handle exceptions when opening a file in Python?', 'What is the time complexity of a dictionary lookup?', 'What does the code review procedure check before grading?', 'Best recipe for carbonara?', 'Who won the 2022 World Cup?', 'Weather in Bucharest today?']]"
```

`TOP_N=4` was chosen because the knowledge base has only 29 chunks total — 4 chunks
already covers a full document section without pulling in unrelated ones.

## 5. Dedicated Embedding + Chat Model

Embeddings and chat generation intentionally use different, purpose-built models:

- **Embeddings**: `qwen3-embedding:latest`, served locally by **Ollama**
  (`config.EMBEDDINGS_ENDPOINT`). Free, no data leaves the machine, low latency —
  well suited to being called on every message for retrieval.
- **Chat**: `gpt-5-mini` on **Azure AI Foundry** (`config.MODEL_NAME`,
  `config.MODEL_ENDPOINT`). Higher quality generation and tool-calling support that a
  small local embedding model isn't designed for.

Swapping either model is a one-line change in `config.py` — nothing else in the
codebase assumes a specific model.

## 6. Error Handling & Fallbacks

| Scenario | Behavior |
|---|---|
| Model endpoint times out / connection fails | `llm_client.py` retries once, then returns a polite error message instead of raising |
| Model returns 401/403 | Clear "check your API key" message, no retry (won't succeed) |
| Model returns 429 / 5xx | Retried once; clear "temporarily unavailable" message on repeat failure |
| Ollama not running | `embeddings_client.py` catches the connection error, prints a clear message, semantic search returns `[]` (chat still works, just without RAG) |
| `embeddings.json` missing or corrupted | Semantic search skipped with a clear message instead of crashing |
| `knowledge/` registry or document missing | Warning printed, that entry skipped, rest of the knowledge base still loads |
| Semantic search finds nothing relevant | Agent injects a fallback system message telling the model to answer from general knowledge and say so |
| Session file missing or corrupted | `ConversationContext.load_from_file` starts a fresh session with a warning instead of crashing |

## 7. Multi-user Support & Sessions

`api.py` keeps one `Agent` (and one `ConversationContext`) per user, keyed by the
`X-User-Id` request header (`"default"` if absent). Each user's history is
persisted to `sessions/<user_id>.json` after every message and reloaded the first time
that user is seen again — so restarting the server doesn't lose anyone's conversation.

There's no real authentication behind this: the web UI (`static/app.js`) asks for a
name on first load, stores it in the browser's `localStorage`, and sends it as
`X-User-Id` on every request. That's enough to demonstrate per-user isolation and
persistent history — a real login system was out of scope for this project.

The CLI (`main.py`) has the same persistence via `save`/`load <name>` commands and a
default session at `sessions/cli_default.json`.

**Known limitation**: the `save_student_evaluation` / `get_student_record` tools write
to a single shared `student_records.json`, not a per-user file — intentional, since in
this project all users are students of the same professor sharing one gradebook.

## 8. Web UI

A small static frontend lives in `static/` (`index.html`, `style.css`, `app.js` — plain
HTML/CSS/vanilla JS, no build step, no framework, no CDN dependencies) and is served
directly by `api.py` via `StaticFiles(directory="static", html=True)`, mounted at `/`
*after* the `/v1/...` routes are declared so it never shadows them. One process, one
port, no separate frontend server.

- **Username flow**: on first load, `app.js` prompts for a name and stores it in
  `localStorage`; every chat request sends it as the `X-User-Id` header. A "Schimbă
  userul" button clears it, making it easy to switch users in one browser window.
- **Typing effect**: `agent.process_message()` returns the full reply in one call — it
  isn't itself a token-streaming API. `api.py::_stream_chunks` simulates streaming
  server-side: it splits the finished reply into words and yields one SSE chunk per
  word with a short `asyncio.sleep(STREAM_CHUNK_DELAY_SECONDS)` between them. The
  frontend just appends each chunk's content as it arrives — no client-side timers.
- **History isn't replayed into the DOM on page reload** — the chat window starts
  empty, but the server-side `ConversationContext` still remembers everything (provable
  by asking a follow-up question right after a refresh). Fetching and re-rendering
  history was left out as unnecessary complexity for what the course requires.
- **File uploads**: the 📎 button opens a file picker, `app.js` `POST`s the file to
  `/upload` (as `multipart/form-data`, header `X-User-Id`), and `api.py` saves it under
  `uploads/<user_id>/`. The agent doesn't see the content automatically — it only reads
  it if it decides to call the `read_uploaded_file`/`list_uploaded_files` tools (see
  `tools/file_tool.py`), same as it decides when to call any other tool. This keeps the
  upload itself free (no tokens spent) until the content is actually needed. There's no
  web-fetch dependency here (`fetch_page`/`web_search` still need outbound internet
  access and won't work behind a restrictive firewall) — uploads are pure local
  file I/O between the browser and `api.py`.

### Running it

```powershell
$env:CHATGPT_API_KEY = "your-azure-key"
uvicorn api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` in a browser.

**Demo checklist**: enter a username, send a message, watch the reply type itself out
word by word → open a private/incognito window, enter a *different* username, ask
"what's my name?" and confirm it has no knowledge of the first user → switch back to
the first window and confirm it still remembers → check `dir sessions` shows one JSON
file per username → restart `uvicorn` and confirm both histories reload from disk →
`python main.py` still works independently as a CLI, unaffected.
