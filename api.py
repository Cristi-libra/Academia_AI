"""
Web backend for the Gem assistant (FastAPI).

Reuses the exact same Agent / LLMClient / ConversationContext / tools as the
CLI (main.py). The CLI keeps working untouched - this is just an alternative,
prettier front-end.

Persistence model:
    sessions/<user>/<conv_id>.json   -> one saved conversation (messages + tokens)
    sessions/<user>/index.json       -> list of the user's conversations (title, time)

Each (user, conversation) pair gets its own isolated Agent + ConversationContext,
so a user can keep several conversations and switch between them, and different
users never see each other's data.

Run:
    uvicorn api:app --host 127.0.0.1 --port 8000
Then open http://127.0.0.1:8000 in the browser.
"""

import json
import logging
import os
import re
import time
import uuid

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
from agent import Agent
from conversation_context import ConversationContext
from document_reader import extract_text
from embedding_generator import embedding_generator
from llm_client import LLMClient
from logging_config import setup_logging
from tools.tools import tools
from tools.file_tool import make_file_tools

logger = logging.getLogger(__name__)

app = FastAPI(title="Gem Assistant")

llm_client = LLMClient()
agents = {}             # "user::conv_id" -> Agent (fiecare cu propriul ConversationContext)
pending_files = {}      # "user::conv_id" -> [(filename, text)] atașate, de trimis cu mesajul

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@app.on_event("startup")
def on_startup():
    setup_logging()
    logger.info("Gem Assistant starting up.")
    embedding_generator()
    os.makedirs(config.SESSIONS_DIR, exist_ok=True)


# ----------------------------------------------------------------------------
# Căi & fișiere pe disc (memorie persistentă + izolare)
# ----------------------------------------------------------------------------
def _safe(name: str) -> str:
    """Nume sigur de fișier (fără path traversal)."""
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "_", (name or "").strip())
    return cleaned or "x"


def _user_dir(user: str) -> str:
    directory = os.path.join(config.SESSIONS_DIR, _safe(user))
    os.makedirs(directory, exist_ok=True)
    return directory


def _conv_path(user: str, conv_id: str) -> str:
    return os.path.join(_user_dir(user), _safe(conv_id) + ".json")


def _index_path(user: str) -> str:
    return os.path.join(_user_dir(user), "index.json")


def _read_index(user: str) -> list:
    try:
        with open(_index_path(user), "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _write_index(user: str, items: list):
    with open(_index_path(user), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def _touch_index(user: str, conv_id: str, context: ConversationContext):
    """Actualizează (sau creează) intrarea din index: titlu + timp."""
    items = _read_index(user)
    entry = next((e for e in items if e["id"] == conv_id), None)

    title = None
    for m in context.get_history():
        if m.get("role") == "user" and m.get("content"):
            title = str(m["content"]).strip()[:48]
            break

    now = time.strftime("%Y-%m-%d %H:%M")
    if entry is None:
        items.append({"id": conv_id, "title": title or "Conversație nouă", "updated": now})
    else:
        if title:
            entry["title"] = title
        entry["updated"] = now
    _write_index(user, items)


# ----------------------------------------------------------------------------
# Agenți per (user, conversație)
# ----------------------------------------------------------------------------
def get_agent(user: str, conv_id: str) -> Agent:
    key = f"{_safe(user)}::{_safe(conv_id)}"
    if key not in agents:
        # numele intră în system prompt din constructor (assemble_system_prompt);
        # tool-urile de fișiere sunt legate de folderul de upload al userului.
        context = ConversationContext(username=user)
        context.load_from_file(_conv_path(user, conv_id))
        user_tools = tools + make_file_tools(_safe(user))
        agents[key] = Agent(llm_client, context, tools=user_tools)
    return agents[key]


def _cost(ctx) -> float:
    return (
        ctx.input_tokens / 1_000_000 * config.INPUT_TOKEN_PRICE_PER_MILLION
        + ctx.output_tokens / 1_000_000 * config.OUTPUT_TOKEN_PRICE_PER_MILLION
    )


# ----------------------------------------------------------------------------
# Modele de request
# ----------------------------------------------------------------------------
class ChatRequest(BaseModel):
    user: str
    conv_id: str
    message: str = ""


# ----------------------------------------------------------------------------
# Lista de conversații ale unui user
# ----------------------------------------------------------------------------
@app.get("/conversations/{user}")
def list_conversations(user: str):
    items = _read_index(user)
    items.sort(key=lambda e: e.get("updated", ""), reverse=True)
    return {"conversations": items}


@app.post("/conversations/{user}")
def new_conversation(user: str):
    # doar generăm un id; fișierul se creează la primul mesaj
    return {"id": uuid.uuid4().hex[:12]}


@app.delete("/conversations/{user}/{conv_id}")
def delete_conversation(user: str, conv_id: str):
    agents.pop(f"{_safe(user)}::{_safe(conv_id)}", None)
    path = _conv_path(user, conv_id)
    if os.path.exists(path):
        os.remove(path)
    _write_index(user, [e for e in _read_index(user) if e["id"] != conv_id])
    return {"status": "deleted"}


@app.get("/export/{user}/{conv_id}")
def export_conversation(user: str, conv_id: str):
    """Downloads one conversation as a portable JSON file.

    Self-contained on purpose: the exported file carries the messages, the token
    counters and the metadata from the index, so it can be imported into another
    account (or another machine) without needing anything else.
    """
    agent = get_agent(user, conv_id)
    entry = next((e for e in _read_index(user) if e["id"] == conv_id), None)

    payload = {
        "format": "gem-conversation",
        "version": 1,
        "exported_at": time.strftime("%Y-%m-%d %H:%M"),
        "title": (entry or {}).get("title", "Conversație"),
        # [1:] scoate system prompt-ul: se reasamblează din knowledge/ la import.
        "messages": agent.context.get_history()[1:],
        "input_tokens": agent.context.input_tokens,
        "output_tokens": agent.context.output_tokens,
    }
    logger.info(
        "User '%s' exported conversation %s (%d messages).",
        user, conv_id, len(payload["messages"]),
    )
    filename = f"gem-conversation-{_safe(conv_id)}.json"
    return Response(
        content=json.dumps(payload, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/import/{user}")
async def import_conversation(user: str, file: UploadFile = File(...)):
    """Imports a previously exported conversation as a NEW conversation.

    Always creates a fresh id instead of overwriting: importing must never
    destroy a conversation the user already has.
    """
    raw = await file.read()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        logger.warning("Import failed for user '%s': not valid JSON (%s).", user, error)
        return {"error": "That file is not valid JSON."}

    if not isinstance(payload, dict) or payload.get("format") != "gem-conversation":
        logger.warning("Import failed for user '%s': unrecognised format.", user)
        return {"error": "That file is not a Gem conversation export."}

    messages = payload.get("messages")
    if not isinstance(messages, list):
        return {"error": "The export contains no messages."}

    conv_id = uuid.uuid4().hex[:12]
    context = ConversationContext(username=user)
    context.messages = [context.messages[0]] + messages
    context.input_tokens = payload.get("input_tokens", 0) or 0
    context.output_tokens = payload.get("output_tokens", 0) or 0
    context.save_to_file(_conv_path(user, conv_id))
    _touch_index(user, conv_id, context)

    logger.info(
        "User '%s' imported conversation as %s (%d messages).",
        user, conv_id, len(messages),
    )
    return {"id": conv_id, "messages": len(messages)}


@app.get("/history/{user}/{conv_id}")
def history(user: str, conv_id: str):
    agent = get_agent(user, conv_id)
    turns = [
        {"role": m.get("role"), "content": m.get("content")}
        for m in agent.context.get_history()[1:]
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]
    ctx = agent.context
    return {
        "messages": turns,
        "input_tokens": ctx.input_tokens,
        "output_tokens": ctx.output_tokens,
        "total_cost": _cost(ctx),
    }


@app.get("/debug/prompt/{user}/{conv_id}")
def debug_prompt(user: str, conv_id: str):
    """Arată exact ce conține system prompt-ul (messages[0]) trimis modelului.

    Deschide http://127.0.0.1:8000/debug/prompt/<nume>/<conv_id> ca să verifici
    că numele tău e acolo. Găsești conv_id în /conversations/<nume>.
    """
    agent = get_agent(user, conv_id)
    system_prompt = agent.context.messages[0]["content"]
    return {
        "student_name": agent.context.username,
        "name_in_system_prompt": (user in system_prompt),
        "tools_available": list(agent.tools.keys()),
        "system_prompt": system_prompt,
    }


# ----------------------------------------------------------------------------
# Chat cu streaming (Server-Sent Events)
# ----------------------------------------------------------------------------
def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.post("/chat")
def chat(req: ChatRequest):
    """
    Rulează agentul și transmite răspunsul în flux (efect de typing).

    Important: agentul comprimă întâi istoricul (compress_history), deci modelul
    primește contextul REZUMAT, nu tot istoricul - vezi Agent.process_message.
    """
    agent = get_agent(req.user, req.conv_id)

    # Lipește conținutul fișierelor atașate DE mesaj (stil ChatGPT):
    # modelul le vede direct în prompt, nu trebuie să cheme un tool.
    key = f"{_safe(req.user)}::{_safe(req.conv_id)}"
    attachments = pending_files.pop(key, [])
    message = req.message
    if attachments:
        blocks = [f'[Attached file "{fn}"]:\n{txt}' for fn, txt in attachments]
        message = "\n\n".join(blocks) + "\n\n---\n\n" + req.message

    def event_stream():
        try:
            answer = agent.process_message(message)
        except Exception as error:
            logger.exception(
                "Unhandled error while answering user '%s' (conv %s): %s",
                req.user, req.conv_id, error,
            )
            yield _sse({"type": "error", "message": f"Server error: {error}"})
            return

        if agent.last_reasoning:
            yield _sse({"type": "thinking", "text": agent.last_reasoning})
        if agent.last_tools_used:
            yield _sse({"type": "tools", "names": agent.last_tools_used})

        for word in answer.split(" "):
            yield _sse({"type": "delta", "text": word + " "})
            time.sleep(0.02)

        agent.context.save_to_file(_conv_path(req.user, req.conv_id))
        _touch_index(req.user, req.conv_id, agent.context)

        ctx = agent.context
        yield _sse({
            "type": "done",
            "input_tokens": ctx.input_tokens,
            "output_tokens": ctx.output_tokens,
            "total_cost": _cost(ctx),
            "timing": {k: round(v, 3) for k, v in agent.last_metrics.items()},
        })

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ----------------------------------------------------------------------------
# Upload de document: extragem textul și îl reținem ca "atașament" pentru
# conversație. Se lipește de următorul mesaj (stil ChatGPT), iar fișierul se
# salvează și pe disc ca să rămână accesibil prin tool-urile de fișiere.
# ----------------------------------------------------------------------------
def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]", "_", os.path.basename(filename or ""))
    return cleaned or "upload.txt"


@app.post("/upload")
async def upload(
    user: str = Form(...),
    conv_id: str = Form(...),
    file: UploadFile = File(...),
):
    data = await file.read()
    if len(data) > config.UPLOAD_MAX_FILE_BYTES:
        logger.warning(
            "Upload rejected for user '%s': '%s' is %d bytes (max %d).",
            user, file.filename, len(data), config.UPLOAD_MAX_FILE_BYTES,
        )
        return {"error": f"File too large (max {config.UPLOAD_MAX_FILE_BYTES} bytes)."}

    safe_name = _safe_filename(file.filename)
    text = extract_text(safe_name, data)
    logger.info(
        "User '%s' uploaded '%s' (%d bytes, %d chars extracted).",
        user, safe_name, len(data), len(text),
    )

    # salvăm pe disc (pentru tool-urile de fișiere / referire ulterioară)
    user_dir = os.path.join(config.UPLOADS_DIR, _safe(user))
    os.makedirs(user_dir, exist_ok=True)
    with open(os.path.join(user_dir, safe_name), "wb") as f:
        f.write(data)

    # reținem textul ca atașament pentru următorul mesaj din această conversație
    key = f"{_safe(user)}::{_safe(conv_id)}"
    pending_files.setdefault(key, []).append((safe_name, text))

    return {"filename": safe_name, "chars": len(text)}


# ----------------------------------------------------------------------------
# Static UI
# ----------------------------------------------------------------------------
@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
