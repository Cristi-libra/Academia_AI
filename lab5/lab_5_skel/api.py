"""
OpenAI-compatible HTTP backend for the Gem agent, also serving the static
web UI (see static/).

Exposes /v1/models and /v1/chat/completions. Each user gets its own
Agent + ConversationContext, keyed by the X-User-Id header (or "default"
if absent), persisted under config.SESSIONS_DIR.
"""

import asyncio
import json
import os
import re
import time
import uuid

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

import config
from agent import Agent
from conversation_context import ConversationContext
from embedding_generator import embedding_generator
from llm_client import LLMClient
from tools.file_tool import make_file_tools
from tools.tools import tools

MODEL_ID = "gem-agent"
USER_ID_HEADER = "x-user-id"
STREAM_CHUNK_DELAY_SECONDS = 0.03

app = FastAPI()
llm_client = LLMClient()
agents = {}  # user_id -> Agent, each with its own ConversationContext


@app.on_event("startup")
def startup():
    embedding_generator()
    os.makedirs(config.SESSIONS_DIR, exist_ok=True)


def _safe_user_id(user_id):
    """Keep only characters safe for a filename, to avoid path traversal."""
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "_", user_id)
    return cleaned or "default"


def _safe_filename(filename):
    """Strip any path components and unsafe characters, keep the extension."""
    cleaned = re.sub(r"[^A-Za-z0-9_.-]", "_", os.path.basename(filename or ""))
    return cleaned or "upload.txt"


def session_path(user_id):
    return os.path.join(config.SESSIONS_DIR, f"{user_id}.json")


def get_agent(user_id):
    if user_id not in agents:
        context = ConversationContext(username=user_id)
        context.load_from_file(session_path(user_id))
        user_tools = tools + make_file_tools(user_id)
        agents[user_id] = Agent(llm_client, context, tools=user_tools)
    return agents[user_id]


def _last_user_text(messages):
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "")
    return ""


def _delta_chunk(request_id, created, content):
    return {
        "id": request_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": MODEL_ID,
        "choices": [{
            "index": 0,
            "delta": {"role": "assistant", "content": content},
            "finish_reason": None,
        }],
    }


def _completion_payload(request_id, created, content, reasoning=None):
    message = {"role": "assistant", "content": content}
    if reasoning:
        message["reasoning"] = reasoning
    return {
        "id": request_id,
        "object": "chat.completion",
        "created": created,
        "model": MODEL_ID,
        "choices": [{
            "index": 0,
            "message": message,
            "finish_reason": "stop",
        }],
    }


async def _stream_chunks(request_id, created, content, reasoning=None):
    """Yield the response word by word, so the UI can show a typing effect."""
    if reasoning:
        reasoning_chunk = {
            "id": request_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": MODEL_ID,
            "choices": [{
                "index": 0,
                "delta": {"role": "assistant", "reasoning": reasoning},
                "finish_reason": None,
            }],
        }
        yield f"data: {json.dumps(reasoning_chunk)}\n\n"

    words = content.split(" ")
    for index, word in enumerate(words):
        piece = word if index == len(words) - 1 else word + " "
        yield f"data: {json.dumps(_delta_chunk(request_id, created, piece))}\n\n"
        await asyncio.sleep(STREAM_CHUNK_DELAY_SECONDS)

    done_chunk = {
        "id": request_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": MODEL_ID,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(done_chunk)}\n\n"
    yield "data: [DONE]\n\n"


@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [{"id": MODEL_ID, "object": "model", "owned_by": "lab5"}],
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    messages = body.get("messages", [])
    stream = bool(body.get("stream", False))
    request_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())

    last_user_text = _last_user_text(messages)

    user_id = _safe_user_id(request.headers.get(USER_ID_HEADER, "default"))
    agent = get_agent(user_id)
    content = agent.process_message(last_user_text)
    reasoning = agent.last_reasoning
    agent.context.save_to_file(session_path(user_id))

    if stream:
        return StreamingResponse(
            _stream_chunks(request_id, created, content, reasoning),
            media_type="text/event-stream",
        )

    return _completion_payload(request_id, created, content, reasoning)


@app.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    user_id = _safe_user_id(request.headers.get(USER_ID_HEADER, "default"))
    safe_name = _safe_filename(file.filename)

    content = await file.read()
    if len(content) > config.UPLOAD_MAX_FILE_BYTES:
        return {
            "error": (
                f"File too large ({len(content)} bytes). "
                f"Max is {config.UPLOAD_MAX_FILE_BYTES} bytes."
            )
        }

    user_dir = os.path.join(config.UPLOADS_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    with open(os.path.join(user_dir, safe_name), "wb") as f:
        f.write(content)

    return {"filename": safe_name, "size": len(content)}


# Mounted last so it never shadows the /v1/... routes above: FastAPI/Starlette
# matches routes in registration order, and this mount is a catch-all at "/".
app.mount("/", StaticFiles(directory="static", html=True), name="static")
