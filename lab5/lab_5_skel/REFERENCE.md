# Gem — API Reference

Technical reference for the Gem assistant: every public class, module function,
tool, and HTTP endpoint — signatures, parameters, return values, and what happens
behind the scenes.

For a conceptual overview and setup, see [`README.md`](README.md).

**Conventions**
- All paths are relative to `lab5/lab_5_skel/`.
- "Model" means the chat LLM behind `LLMClient` (OpenAI-compatible: Gemini by default).
- Tool callbacks always return a **string** — that string is what the model reads
  back as the tool result.

---

## Table of contents

1. [Configuration](#1-configuration)
2. [Core classes](#2-core-classes)
   - [`Tool`](#tool)
   - [`ConversationContext`](#conversationcontext)
   - [`Agent`](#agent)
   - [`LLMClient`](#llmclient)
   - [`EmbeddingsClient`](#embeddingsclient)
3. [Module functions](#3-module-functions)
4. [Tools](#4-tools)
5. [HTTP API](#5-http-api)

---

## 1. Configuration

All settings live in `config.py` as module-level constants. Import what you need:
`from config import TOP_N`.

| Constant | Default | Meaning |
|---|---|---|
| `MODEL_NAME` | `"gemini-3.1-flash-lite"` | Chat model id sent in the request body. |
| `API_KEY` | `os.environ["GEMINI_API_KEY"]` | Chat API key. Read from the environment — never hardcode. |
| `MODEL_ENDPOINT` | Gemini OpenAI-compat URL | Chat completions endpoint. |
| `EMBEDDINGS_MODEL` | `"bge-m3:latest"` | Ollama embedding model. |
| `EMBEDDINGS_ENDPOINT` | `http://localhost:11434/api/embed` | Ollama embeddings URL. |
| `SYSTEM_PROMPT` | `""` | Prefix prepended before the knowledge base in the system prompt. |
| `CHUNK_SIZE` | `100` | Words per chunk when indexing knowledge docs. |
| `CHUNK_OVERLAP` | `20` | Words shared between consecutive chunks. |
| `TOP_N` | `4` | Max chunks returned by semantic search. |
| `SIMILARITY_THRESHOLD` | `0.5` | Minimum cosine similarity to keep a chunk. |
| `DEBUG` | `False` | Enables verbose prints (e.g. retrieval counts). |
| `EMBEDDINGS_FILE` | `"embeddings.json"` | Cached embeddings path. |
| `MAX_CONTEXT_TOKENS` | `16000` | History budget before compression kicks in. |
| `KEEP_RECENT_MESSAGES` | `4` | Messages kept verbatim during compression. |
| `STUDENT_RECORDS_FILE` | `"student_records.json"` | Shared gradebook path. |
| `SESSIONS_DIR` | `"sessions"` | Per-user conversation storage. |
| `UPLOADS_DIR` | `"uploads"` | Per-user uploaded files. |
| `UPLOAD_MAX_FILE_BYTES` | `10_000_000` | Upload size limit. |
| `WEB_SEARCH_MAX_RESULTS` | `5` | Results returned by `web_search`. |
| `INPUT_TOKEN_PRICE_PER_MILLION` | `30` | Input price used for cost estimate. |
| `OUTPUT_TOKEN_PRICE_PER_MILLION` | `70` | Output price used for cost estimate. |

---

## 2. Core classes

### `Tool`

`tools/tool.py` — a plain data holder describing one callable exposed to the model.

```python
Tool(name, description, parameters, callback)
```

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Unique identifier the model uses to call the tool. |
| `description` | `str` | Natural-language explanation of when to use it (the model reads this). |
| `parameters` | `dict` | JSON Schema of the arguments (OpenAI function-calling format). |
| `callback` | `callable` | Python function invoked with the parsed arguments; must return `str`. |

**Behind the scenes:** `LLMClient` serializes each `Tool` into the OpenAI
`{"type": "function", "function": {...}}` shape. When the model emits a tool call,
`Agent._handle_tool_calls` looks the tool up by `name` and calls `callback(**args)`.

---

### `ConversationContext`

`conversation_context.py` — owns the message history, token counters, per-user
identity, compression, and persistence.

```python
ConversationContext(username=None)
```

| Parameter | Type | Description |
|---|---|---|
| `username` | `str \| None` | If set, a `## Current User` block naming this person is appended to the system prompt. |

**Attributes:** `messages` (list; `messages[0]` is the system prompt), `input_tokens`,
`output_tokens`, `username`.

#### Methods

**`assemble_system_prompt() -> dict`**
Builds the system message by walking `knowledge/`: loads `prompts/*`, plus `facts`
and `procedures` marked `always_load: true` (each under a `## <name>` heading), then
appends the `## Current User` block if `username` is set. Missing/corrupt files are
skipped with a warning. Returns `{"role": "system", "content": ...}`.

**`add_message(message: dict) -> None`**
Appends a message (`{"role", "content", ...}`) to the history.

**`get_history() -> list[dict]`**
Returns the full message list (the exact list sent to the model).

**`track_input(messages: list[dict]) -> None`**
Adds `count_tokens` over every message's content to `input_tokens`. Call with what
you are about to send to the model.

**`track_output(response: str) -> None`**
Adds `count_tokens(response)` to `output_tokens`.

**`compress_history(max_tokens: int, llm_client=None) -> None`**
If the history exceeds `max_tokens`, keeps `messages[0]` and the last
`KEEP_RECENT_MESSAGES`, and replaces the middle with a single LLM-generated summary
(`## smart compression`). Falls back to a plain sliding window if `llm_client` is
`None` or the summary fails. No-op when the history fits.

**`save_to_file(path: str) -> None`**
Writes `{messages (minus the system prompt), input_tokens, output_tokens}` as JSON.
Creates parent directories as needed.

**`load_from_file(path: str) -> None`**
Restores saved messages on top of a freshly-assembled system prompt, and restores the
token counters. Missing/corrupt files are ignored (starts fresh).

---

### `Agent`

`agent.py` — orchestrates one turn: retrieval → model call → multi-step tools → answer.

```python
Agent(llm_client, context, tools=None)
```

| Parameter | Type | Description |
|---|---|---|
| `llm_client` | `LLMClient` | Chat client. |
| `context` | `ConversationContext` | Conversation state. |
| `tools` | `list[Tool] \| None` | Tools available this turn (indexed by name). |

**Attributes:** `last_reasoning` (str; the model's thinking if exposed) and
`last_tools_used` (list[str]; tool names called this turn — used by the web UI).

#### Methods

**`process_message(user_message: str) -> str`**
Runs a full turn and returns the assistant's text. Steps:
1. `compress_history(MAX_CONTEXT_TOKENS, llm_client)`.
2. Semantic search on `user_message`; injects a `system` message with the relevant
   chunks, or a fallback note if none are found.
3. Appends the user message; calls the model **with tools**.
4. **Multi-step loop** (up to `MAX_TOOL_ROUNDS = 5`): while the model returns
   `tool_calls`, execute them, append the results, and call the model again *with
   tools*. This lets it chain tools (read file → grade → save).
5. Records `input`/`output` tokens and returns the final content.

**`_handle_tool_calls(tool_calls: list) -> list[dict]`** *(internal)*
Executes each requested call and returns `{"role": "tool", "tool_call_id", "content"}`
results. Unknown tool names return a `"Tool '...' not found"` string.

---

### `LLMClient`

`llm_client.py` — all communication with the chat model.

```python
LLMClient()   # reads MODEL_NAME / MODEL_ENDPOINT / API_KEY from config
```

**`generate_response(messages: list[dict], tools=None) -> dict`**
Sends an OpenAI-style chat completion and returns `{"message": {...}, "raw": ...}`.

| Parameter | Type | Description |
|---|---|---|
| `messages` | `list[dict]` | Full conversation in OpenAI format. |
| `tools` | `list[Tool] \| None` | If given, serialized and offered to the model. |

**Behind the scenes:**
- `_merge_system_messages` collapses **all** `system` messages into one at the front
  (Gemini's OpenAI endpoint honours only a single system instruction, so this keeps
  the persona + identity + RAG context intact).
- Auth header is `api-key` for Azure endpoints, else `Bearer`.
- Retries once; maps timeout / connection / HTTP 401/403/429/5xx errors to a clear
  message returned as `{"message": {"content": ...}}` instead of raising.

---

### `EmbeddingsClient`

`embeddings_client.py` — embeddings and semantic search over the indexed knowledge.

```python
EmbeddingsClient()
```

**`get_embedding(text: str) -> list[float]`**
Calls the Ollama embeddings endpoint and returns the vector. Raises `ConnectionError`
with a clear message if Ollama is unreachable / times out / errors.

**`cosine_similarity(vec1, vec2) -> float`**
Cosine similarity in `[-1, 1]` (1 = identical meaning, 0 = unrelated).

**`semantic_search(user_question: str) -> list[dict]`**
Embeds the question, scores it against every chunk in `EMBEDDINGS_FILE`, and returns
the chunks above `SIMILARITY_THRESHOLD`, sorted by similarity, capped at `TOP_N`.
Each result: `{"document_id", "chunk_index", "similarity", "content"}`. Returns `[]`
(with a printed reason) if Ollama is down or the embeddings file is missing/corrupt.

---

## 3. Module functions

**`utils.count_tokens(text: str) -> int`**
Token count via `tiktoken` (`cl100k_base`). The encoder is created once at import.

**`document_chunker.load_n_chunk_docs() -> list[dict]`**
Walks `knowledge/facts` and `knowledge/procedures`, reads every doc marked
`always_load: false`, and splits each into overlapping word chunks
(`CHUNK_SIZE` / `CHUNK_OVERLAP`). Returns `{"document_id", "chunk_index", "content"}`.

**`embedding_generator.embedding_generator() -> None`**
Builds `EMBEDDINGS_FILE` from `load_n_chunk_docs()`. Skips work if the cache is newer
than every file under `knowledge/` (`_knowledge_mtime()`, recursive). Degrades
gracefully (prints and returns) if Ollama is unavailable.

**`document_reader.extract_text(filename: str, data: bytes) -> str`**
Extracts readable text from an uploaded file, dispatching by extension: `.pdf`
(pypdf), `.docx` (python-docx), or any text format (UTF-8/UTF-16/latin-1). Truncated
to 20 000 chars. Returns a clear message for unsupported/empty/unreadable files.

**`tools.file_tool.make_file_tools(user_id: str) -> list[Tool]`**
Returns two `Tool`s bound (via closure) to `uploads/<user_id>/`:
`list_uploaded_files` and `read_uploaded_file` — see below.

---

## 4. Tools

Each tool is a `Tool` instance registered in `tools/tools.py` (the per-user file
tools are added at runtime by `make_file_tools`). The model calls them by `name`;
arguments follow each tool's JSON Schema. **Every tool returns a string.**

### `lucky_number`
Generates a lucky number from a birth date and today's date (sums all digits).
| Param | Type | Required | Description |
|---|---|---|---|
| `birth_date` | string | yes | `DDMMYYYY`, e.g. `31121993`. |

### `web_search`
DuckDuckGo search (no API key). Returns up to `WEB_SEARCH_MAX_RESULTS` results as
title / URL / snippet. Network errors are returned as text, not raised.
| Param | Type | Required | Description |
|---|---|---|---|
| `query` | string | yes | Search query. |

### `check_python_code`
Static analysis of a Python snippet — **never executes it**. Parses with `ast`,
reports syntax errors, function/class counts, PEP 8 naming, missing docstrings, bare
`except`, and over-long lines. Use before grading code.
| Param | Type | Required | Description |
|---|---|---|---|
| `code` | string | yes | Python source to analyze. |

### `save_student_evaluation`
Appends one evaluation to `STUDENT_RECORDS_FILE`. Validates the grade (1–10) and
stamps the date automatically.
| Param | Type | Required | Description |
|---|---|---|---|
| `student` | string | yes | Student name. |
| `topic` | string | yes | What was evaluated. |
| `grade` | integer | yes | 1–10. |
| `feedback` | string | yes | Short constructive feedback. |

### `get_student_record`
Returns a student's evaluation history and average grade (case-insensitive match), or
a "no evaluations" message.
| Param | Type | Required | Description |
|---|---|---|---|
| `student` | string | yes | Student name. |

### `current_datetime`
Returns the current local date and time. No parameters.

### `search_knowledge_base`
On-demand semantic search over the course knowledge base (wraps
`EmbeddingsClient.semantic_search`). Returns the matching passages with source and
score. Requires Ollama running.
| Param | Type | Required | Description |
|---|---|---|---|
| `query` | string | yes | What to look up. |

### `list_uploaded_files` *(per-user)*
Lists files the current user uploaded (from `uploads/<user>/`). No parameters.

### `read_uploaded_file` *(per-user)*
Reads an uploaded file's text (PDF/DOCX/text via `document_reader`). Filename is
sanitized to prevent path traversal.
| Param | Type | Required | Description |
|---|---|---|---|
| `filename` | string | yes | Exact uploaded file name. |

---

## 5. HTTP API

Served by `api.py` (FastAPI). Start with `uvicorn api:app --port 8000`. The web UI is
served at `/`. In the requests below, `{user}` is the username and `{conv_id}` a
conversation id.

| Method & path | Body / params | Returns |
|---|---|---|
| `GET /` | — | The web UI (`static/index.html`). |
| `GET /conversations/{user}` | — | `{conversations: [{id, title, updated}]}`, newest first. |
| `POST /conversations/{user}` | — | `{id}` — a new conversation id (file created on first message). |
| `DELETE /conversations/{user}/{conv_id}` | — | `{status: "deleted"}`; removes the session file + index entry. |
| `GET /history/{user}/{conv_id}` | — | `{messages: [{role, content}], input_tokens, output_tokens, total_cost}`. |
| `POST /chat` | JSON `{user, conv_id, message}` | **SSE stream** — see below. Any pending uploads are inlined into the message first. |
| `POST /upload` | multipart `user`, `conv_id`, `file` | `{filename, chars}` or `{error}`. Extracts text, stages it for the next message, saves the file under `uploads/<user>/`. |
| `POST /reset` | JSON `{user, conv_id}` | `{status}`. |
| `GET /debug/prompt/{user}/{conv_id}` | — | `{student_name, name_in_system_prompt, tools_available, system_prompt}` — inspect exactly what the model receives. |

### `POST /chat` streaming events

The response is `text/event-stream`; each line is `data: {json}`. Event `type`s:

| `type` | Payload | Meaning |
|---|---|---|
| `thinking` | `{text}` | Model reasoning, if exposed. |
| `tools` | `{names}` | Tool names used this turn. |
| `delta` | `{text}` | A chunk of the answer (word by word). |
| `done` | `{input_tokens, output_tokens, total_cost}` | Final stats; stream ends. |
| `error` | `{message}` | Something failed; shown in place of the answer. |
