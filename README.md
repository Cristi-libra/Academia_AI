# Gem — AI Professor Assistant

An educational chatbot with the persona of **Gem**, a Computer Science / Python
professor. It answers questions, reviews and grades student code, reads uploaded
documents, and keeps per-student memory — using a full RAG pipeline over a local
knowledge base plus tool calling.

Runs two ways from the same core: a **CLI** (`main.py`) and a **web app**
(`api.py` + `static/`).

---

## Architecture

```
                 ┌─────────── CLI (main.py) ────────────┐
   User ─────────┤                                       ├──► Agent
                 └─────── Web UI (api.py + static/) ──────┘      │
                                                                 ▼
                                                    ConversationContext
                                                   (history, tokens, per-user
                                                    identity, compression)
                                                                 │
                        ┌────────────────────────────────────────┤
                        ▼                                         ▼
              Knowledge Base (RAG)                    Tools (multi-step loop)
       chunking → embeddings → semantic search    web search · code check ·
       qwen3-embedding @ Ollama (local)            student records · datetime ·
                        │                           KB search · list/read files
                        ▼
              relevant chunks injected
                        │
                        ▼
                 LLM: gpt-5-mini @ Azure OpenAI
                        │
                        ▼
                     Answer
```

The agent runs a **multi-step tool loop**: it re-queries the model with the tools
after each tool result, so a single request can chain several tools (e.g. read an
uploaded file → grade it → save the evaluation) before producing the final answer.

## How to run

Prerequisites:
- **Python 3.10+**
- **Ollama** running locally with the embeddings model:
  `ollama pull qwen3-embedding`
- Dependencies:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```
- **API key** for the chat model. Copy the template and fill it in:
  ```powershell
  copy .env.example .env
  # then edit .env and set API_KEY=your-key
  ```
  Or, if you prefer not to use a file, set it in the environment:
  ```powershell
  $env:API_KEY = "your-key"          # current session
  setx API_KEY "your-key"            # persisted (reopen the terminal)
  ```

### Configuration

All settings live in [`config.py`](config.py), and **every one of them can be
overridden without touching the code**. Values resolve in this order:

1. a real environment variable (`$env:TOP_N = "8"`)
2. an entry in `.env` (gitignored — your local values)
3. the default in `config.py`

A real environment variable always beats `.env`, which is what makes it safe to
keep a `.env` for local work and still override it in CI. An unparsable value
(`TOP_N=abc`) falls back to the default instead of crashing at startup.

[`.env.example`](.env.example) is the committed template listing every supported
variable — copy it to `.env` and edit. Only `API_KEY` is actually required.

> The chat and embedding models are swappable with one line each — the
> OpenAI-compatible client works with Azure OpenAI, Gemini, or any compatible
> endpoint.

**CLI:**
```powershell
python main.py
```

**Web app:**
```powershell
uvicorn api:app --host 127.0.0.1 --port 8000
```
Then open http://127.0.0.1:8000 — enter a username, start conversations (they're
listed in the sidebar), chat, upload documents, switch theme or user.

> On first run, embeddings are generated from `knowledge/` and cached in
> `embeddings.json`. If you change the embedding model, delete `embeddings.json`
> so it regenerates.

### Example session

```
$ python main.py
AI Assistant started. Type 'exit' to quit.

You: salut, cine ești?
AI: Sunt Gem, asistentul tău pentru cursul de Python...

You: ce complexitate are quicksort?
AI: Quicksort are complexitate medie O(n log n)...   # answered from knowledge/

You: caută pe web noutăți despre Python 3.14
AI: ...                                              # triggers the web_search tool

You: exit
```

In the web app you can additionally upload a `.pdf`, `.docx`, `.md` or `.txt`
file and ask the assistant to review or grade it — the file content is attached
to your next message.

---

## Running the tests

```powershell
pytest                                              # run the test suite
pytest --cov=embeddings_client --cov-report=term    # with coverage
```

Tests live in `tests/` and cover the pure logic only (e.g.
`EmbeddingsClient.cosine_similarity`). External services — Ollama, Azure — are
deliberately **not** called from tests, so the suite runs offline and without an
API key.

---

## Logs

The app logs to the console **and** to `app.log` in the project root (gitignored).
Configured in `logging_config.py`, tuned in `config.py`:

```python
LOG_LEVEL = "INFO"     # set to "DEBUG" for retrieval details
LOG_FILE = "app.log"
```

Each conversation turn is traceable end to end: the user question, how many
knowledge chunks were retrieved, every tool call and its result, the model's
answer, and token usage. Failures (model timeouts, Ollama down, tool errors) are
logged at `ERROR`.

```
[2026-07-20 13:34:19,093] INFO [agent]: User question: ce complexitate are quicksort?
[2026-07-20 13:34:19,540] INFO [agent]: Retrieved 4 relevant chunks: ['algorithm_complexity', ...]
[2026-07-20 13:34:21,102] INFO [agent]: Tool call: get_current_datetime({})
[2026-07-20 13:34:22,880] INFO [agent]: Model answer: Quicksort are complexitate medie O(n log n)...
[2026-07-20 13:34:22,881] INFO [agent]: Token usage: input=3142 output=87
```

---

## Scalability & Extensibility

The system is designed so the two things you extend most often need **no changes
to the core code**.

### How to add a new tool

1. Create a file in `tools/`, following the shape of `tools/lucky_number_tool.py`:
   a callback function + a module-level `Tool(name, description, parameters,
   callback)` instance.

That's the whole step. `tools/tools.py` scans the package at import time and
picks the new tool up automatically — no registry to edit. Restart the app and
the startup log will list it.

### How to add a knowledge document

1. Drop a `.md` file in `knowledge/facts/` or `knowledge/procedures/`.
2. Add one entry to that folder's `registry.json`:
   `{"id": "file_name", "name": "Human Title", "description": "...", "always_load": false}`.
3. Delete `embeddings.json` and restart (it re-indexes).

No code changes. `always_load: true` puts the document permanently in the system
prompt; `false` makes it retrievable via semantic search only when relevant.

---

## Cost Optimization

Every token sent to the model costs money and dilutes attention, so the design
keeps the prompt small:

- **Selective always-load**: only truly permanent facts (`course_facts`) live in
  the system prompt. Everything else is retrieved on demand.
- **Semantic retrieval with a cap**: `TOP_N = 4` chunks and
  `SIMILARITY_THRESHOLD = 0.5` — only a handful of relevant passages are injected,
  not the whole knowledge base.
- **No injection when nothing is relevant**: if search returns nothing, no chunk
  system-message is added.
- **Context compression**: when the history passes `MAX_CONTEXT_TOKENS`, older
  turns are summarized into a single message (see `compress_history`), so long
  conversations don't grow without bound.
- **Token & cost tracking**: `ConversationContext` counts input/output tokens;
  cost is estimated with the per-million prices in `config.py`.

## Retrieval Thresholds & Tuning

Method: ask several **relevant** and several **irrelevant** questions, and look at
the top similarity score for each. This calibrates the threshold.

| Question | Relevant to KB? | Top similarity |
|---|---|---|
| "What is the complexity of dict lookup?" | yes | _run to fill_ |
| "How do you review student code?" | yes | _run to fill_ |
| "What's the weather tomorrow?" | no | _run to fill_ |

Observed range in testing: relevant questions scored roughly **0.51–0.66**,
clearly separable from irrelevant ones. Hence `SIMILARITY_THRESHOLD = 0.5` (keeps
the relevant band) and `TOP_N = 4` (enough context without bloat). Re-run on your
machine to fill the exact numbers — they depend on the embedding model.

## Dedicated Embedding + Chat Model

Two different models, each chosen for its job (both swappable with one line in
`config.py`):

- **Embeddings — `qwen3-embedding` on Ollama (local)**: free, private (documents
  never leave the machine), low latency, run as often as needed for indexing.
- **Chat — `gpt-5-mini` on Azure OpenAI**: higher-quality reasoning and tool
  calling for the actual conversation.

---

## Error Handling & Fallbacks

The app degrades gracefully instead of crashing:

- **Model errors** (timeout, no connection, bad key, 5xx): one retry, then a clear
  message returned in place of a traceback (`llm_client.py`).
- **Ollama down / embeddings missing or corrupt**: semantic search is skipped with
  an explanation and the assistant answers from general knowledge
  (`embeddings_client.py`).
- **Missing / invalid knowledge files**: a warning naming the file, and the file is
  skipped (`conversation_context.py`, `document_chunker.py`).
- **Tool failures**: a crashing tool is caught, logged with its stack trace, and
  the error is handed back to the model as the tool result instead of killing
  the conversation (`agent.py`).
- **Empty retrieval**: an explicit fallback system message tells the model to
  answer from its own knowledge within its role.

All of the above are written to `app.log` at `WARNING`/`ERROR` — see [Logs](#logs).

## Agent, tools & multi-step reasoning

- **Tool calling in a loop**: `Agent.process_message` keeps calling the model
  *with the tools* as long as it requests tool calls (up to `MAX_TOOL_ROUNDS`), so
  the model can chain tools in one turn — read a file, grade it, then save the
  grade — instead of stopping after a single tool. A safety cap prevents infinite
  loops.
- **Tools available**: web search, static Python code check, save/get student
  evaluation, current datetime, knowledge-base search, and per-user
  `list_uploaded_files` / `read_uploaded_file`.
- **Dynamic tool discovery**: `tools/tools.py` holds no hand-written list. It
  imports every module in `tools/` and collects the module-level `Tool` instances
  it finds, deduplicated by name. **Adding a tool = dropping a `*_tool.py` file
  into `tools/`** — no import to add, no registry to edit. A module that fails to
  import (missing optional dependency, syntax error) is logged and skipped rather
  than taking the whole assistant down.
  ```
  [14:43:17] INFO [tools]: Discovered 7 tools: check_python_code, current_datetime, ...
  ```
  `tool.py` (the base class), `tools.py` (the registry) and `file_tool.py` (its
  tools are built per user by `make_file_tools`) are skipped by design.
- **Single system instruction**: Gemini's OpenAI-compatible endpoint honours only
  one system instruction, so `llm_client._merge_system_messages` merges the persona,
  the user identity and the injected RAG context into one system message before
  sending. (Without this, extra system messages silently drop the persona.)

## Per-user identity

The web UI identifies the user by the username they enter (no login). That name is
passed to `ConversationContext(username=...)` and written into the system prompt
(`## Current User`), so Gem knows who it is talking to, answers "what is my name",
and uses that name automatically for `save_student_evaluation` / `get_student_record`.
The prompt is explicit that a name found *inside* an uploaded CV/document is the
document's subject, not the user.

You can verify what the model actually receives at
`GET /debug/prompt/<user>/<conv_id>` — it returns the full system prompt, the stored
student name, and the available tools.

## Document attachments

Uploads work like ChatGPT: attaching a file (📎) stages it as a chip; on send, its
extracted text (PDF / DOCX / any text format, via `document_reader.py`) is inlined
into that message so the model reads it directly — no separate "I read the file"
step. Files are also saved under `uploads/<user>/` and remain reachable later
through the `read_uploaded_file` tool.

## Sessions, Memory & Multi-user

- **Multiple conversations per user**: each is persisted to
  `sessions/<user>/<conversation_id>.json` (messages + token counters), listed in
  `sessions/<user>/index.json` with an auto-derived title. Conversations
  **survive a server restart** — this is the assistant's memory.
- **Isolation by name (no login)**: users are identified by a username only; each
  `(user, conversation)` gets its own `ConversationContext`, so users never see
  each other's data. Usernames are sanitized to prevent path traversal.
- **Continuing an old conversation stays cheap**: the model is *not* fed the whole
  history. `Agent.process_message` runs `compress_history` before every turn, so
  once the history passes `MAX_CONTEXT_TOKENS` the old messages are replaced by a
  single LLM-generated summary. The sidebar shows all messages for display; the
  model receives `[system prompt] [summary] [last few messages]`.
- **Export / import**: any conversation can be downloaded as a self-contained
  JSON file (the download icon in the header) and imported back from the sidebar
  — into the same account, another account, or another machine. The export
  carries messages, token counters and title; the system prompt is deliberately
  excluded, since it is reassembled from `knowledge/` on load. **An import always
  creates a new conversation** rather than overwriting an existing one, so it can
  never destroy history. Files that are not valid JSON, or not a Gem export, are
  rejected with a message.
- `student_records.json` (grades) is intentionally shared — the professor keeps a
  single gradebook across all students.

## Performance metrics

Every turn is timed by phase and logged next to the token usage, so a slow answer
can be attributed instead of guessed at:

```
[14:45:02] INFO [agent]: Timing: total=12.27s (retrieval=11.83s, model=0.35s over 1 call(s), tools=0.00s)
```

The same numbers are sent to the web UI in the `done` event and shown in the
stats line under the composer.

`Agent.last_metrics` holds the last turn's breakdown — `retrieval`, `model`
(summed across every round of the tool loop), `tools`, and `total`, in seconds.

> Worth knowing: on a typical local setup **retrieval dominates**. Embedding the
> question through Ollama costs several seconds, while the chat model answers in
> well under one. If a turn feels slow, that is usually where it went — not the
> LLM.

## Web app

A self-contained UI in `static/` (no external libraries), served by `api.py`:

- **Sidebar with conversation history** — browse, open, create (New conversation),
  import and delete your past chats.
- **Export / import** — download the open conversation as JSON from the header,
  restore one from the sidebar.
- **Streaming responses** word-by-word (Server-Sent Events) with a typing cursor.
- **Minimal loading indicator** — a spinner plus rotating status words while Gem
  works, replaced by the answer as it streams in.
- **Document attachments** (📎) — staged as chips, sent inline with your message
  (see Document attachments above); PDF / DOCX / any text format.
- **Model reasoning** shown in a collapsible panel when the model exposes it, plus
  chips for any tools that were used (each step of the multi-step loop).
- **Animated Gem loader** — the diamond avatar animates while Gem is thinking.
- **Professional SVG iconography** (no emoji), **light / dark theme**, live
  token, cost & timing readout, responsive layout with a collapsible sidebar on
  mobile.

---

## Project layout

| File | Role |
|---|---|
| `main.py` | CLI entry point |
| `api.py` | FastAPI web backend (chat streaming, upload, conversations, static) |
| `agent.py` | Orchestration: RAG injection, multi-step tool loop, tracking |
| `conversation_context.py` | History, per-user identity, token tracking, compression, persistence |
| `llm_client.py` | Chat model client (OpenAI-compatible: Azure / Gemini / …), system-message merge |
| `embeddings_client.py` | Embeddings + cosine similarity + semantic search |
| `embedding_generator.py` | Builds & caches `embeddings.json` |
| `document_chunker.py` | Splits knowledge docs into chunks (with overlap) |
| `document_reader.py` | Extracts text from uploaded PDF/DOCX/text files |
| `utils.py` | `count_tokens` (tiktoken) |
| `config.py` | All settings — env var → `.env` → default |
| `.env.example` | Committed template of every supported setting (copy to `.env`) |
| `logging_config.py` | `setup_logging()` — console + `app.log`, called once per entry point |
| `tests/` | pytest suite (`test_embeddings_client.py`) |
| `knowledge/` | Prompts, facts, procedures + registries |
| `tools/` | Tool definitions; `tools.py` discovers them automatically |
| `static/` | Web UI (HTML/CSS/JS) |
| `sessions/`, `uploads/` | Per-user conversations and uploaded files (gitignored) |

---

## Requirements coverage (Session 6)

**Mandatory (10p)** — all implemented: agent persona, conversation context, dynamic
system prompt, knowledge base (prompts/facts/procedures) with registries, chunking,
embeddings generation, semantic search, retrieval-based context injection, token
usage tracking, cost estimation.

**Required extensions (12p)** — all six:
- Context recycling / compression — `compress_history` (summary + sliding-window fallback)
- Cost optimization — selective always-load, `TOP_N`, threshold, compression, tracking
- Robust error handling — network / file / JSON failures handled gracefully
- Fallback strategy — retry + clear message on model errors; general-knowledge fallback on empty retrieval
- Scalability & extensibility — add a tool or a document with no core changes
- Code quality — single client instances, module-level encoding, no debug prints, docstrings

**Optional enhancements implemented:** minimal web UI, HTTP backend + REST endpoints,
multi-user support, session management, multiple conversations per user, several extra
tools, **multi-step tool reasoning**, chunk-overlap strategy, retrieval thresholds &
tuning, embedding cache, dedicated embedding + chat model, per-user file tools, and a
live token/cost readout.
