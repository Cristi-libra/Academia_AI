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
       bge-m3 @ Ollama (local)                     student records · datetime ·
                        │                           KB search · list/read files
                        ▼
              relevant chunks injected
                        │
                        ▼
                 LLM: gemini-3.1-flash-lite @ Google
                        │
                        ▼
                     Answer
```

The agent runs a **multi-step tool loop**: it re-queries the model with the tools
after each tool result, so a single request can chain several tools (e.g. read an
uploaded file → grade it → save the evaluation) before producing the final answer.

## How to run

Prerequisites:
- **Ollama** running locally with the embeddings model:
  `ollama pull bge-m3`
- **Gemini API key** in an environment variable:
  `setx GEMINI_API_KEY "your-key"` (PowerShell: `$env:GEMINI_API_KEY="your-key"`)
- Dependencies: `pip install -r requirements.txt`

> The chat model and embedding model are set in `config.py` and are swappable
> with a single line each — the OpenAI-compatible client works with Gemini,
> Azure OpenAI, or any compatible endpoint.

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

---

## Scalability & Extensibility

The system is designed so the two things you extend most often need **no changes
to the core code**.

### How to add a new tool

1. Create a file in `tools/`, following the shape of `tools/lucky_number_tool.py`:
   a callback function + a `Tool(name, description, parameters, callback)` instance.
2. Import it and add the instance to the `tools` list in `tools/tools.py`.

That's it — the agent discovers it, exposes it to the model, and runs it on demand.

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

- **Embeddings — `bge-m3` on Ollama (local)**: free, private (documents never
  leave the machine), low latency, run as often as needed for indexing.
- **Chat — `gemini-3.1-flash-lite` on Google**: higher-quality reasoning and tool
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
- **Empty retrieval**: an explicit fallback system message tells the model to
  answer from its own knowledge within its role.

## Agent, tools & multi-step reasoning

- **Tool calling in a loop**: `Agent.process_message` keeps calling the model
  *with the tools* as long as it requests tool calls (up to `MAX_TOOL_ROUNDS`), so
  the model can chain tools in one turn — read a file, grade it, then save the
  grade — instead of stopping after a single tool. A safety cap prevents infinite
  loops.
- **Tools available**: web search, static Python code check, save/get student
  evaluation, current datetime, knowledge-base search, and per-user
  `list_uploaded_files` / `read_uploaded_file`. Adding one is a single file plus a
  line in `tools/tools.py` (see Scalability).
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
- `student_records.json` (grades) is intentionally shared — the professor keeps a
  single gradebook across all students.

## Web app

A self-contained UI in `static/` (no external libraries), served by `api.py`:

- **Sidebar with conversation history** — browse, open, create (New conversation)
  and delete your past chats.
- **Streaming responses** word-by-word (Server-Sent Events) with a typing cursor.
- **Minimal loading indicator** — a spinner plus rotating status words while Gem
  works, replaced by the answer as it streams in.
- **Document attachments** (📎) — staged as chips, sent inline with your message
  (see Document attachments above); PDF / DOCX / any text format.
- **Model reasoning** shown in a collapsible panel when the model exposes it, plus
  chips for any tools that were used (each step of the multi-step loop).
- **Animated Gem loader** — the diamond avatar animates while Gem is thinking.
- **Professional SVG iconography** (no emoji), **light / dark theme**, live
  token & cost readout, responsive layout with a collapsible sidebar on mobile.

---

## Project layout

| File | Role |
|---|---|
| `main.py` | CLI entry point |
| `api.py` | FastAPI web backend (chat streaming, upload, conversations, static) |
| `agent.py` | Orchestration: RAG injection, multi-step tool loop, tracking |
| `conversation_context.py` | History, per-user identity, token tracking, compression, persistence |
| `llm_client.py` | Chat model client (OpenAI-compatible: Gemini / Azure / …), system-message merge |
| `embeddings_client.py` | Embeddings + cosine similarity + semantic search |
| `embedding_generator.py` | Builds & caches `embeddings.json` |
| `document_chunker.py` | Splits knowledge docs into chunks (with overlap) |
| `document_reader.py` | Extracts text from uploaded PDF/DOCX/text files |
| `utils.py` | `count_tokens` (tiktoken) |
| `config.py` | All settings and constants |
| `knowledge/` | Prompts, facts, procedures + registries |
| `tools/` | Tool definitions (incl. `file_tool.py` — per-user file access) |
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
