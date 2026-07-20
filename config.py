"""
Application configuration.

Every setting can be overridden from the environment, so nothing sensitive or
machine-specific has to live in this file. Values are resolved in this order:

    1. a real environment variable   (e.g. $env:API_KEY)
    2. an entry in the local .env    (not committed - see .env.example)
    3. the default written here

A real environment variable always wins over `.env`: that is what makes it safe
to keep a `.env` for local work and still override it in CI or in production.
"""

import os

from dotenv import load_dotenv

# Loads .env from the project root if present. Missing file is not an error -
# the app must run on defaults + real env vars alone.
load_dotenv()


def _str(name, default):
    """Reads a string setting; an empty variable falls back to the default."""
    return os.environ.get(name) or default


def _int(name, default):
    """Reads an int setting; an unparsable value falls back to the default."""
    try:
        return int(os.environ[name])
    except (KeyError, ValueError):
        return default


def _float(name, default):
    try:
        return float(os.environ[name])
    except (KeyError, ValueError):
        return default


def _bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


# --- Models & credentials ---------------------------------------------------
MODEL_NAME = _str("MODEL_NAME", "gpt-5-mini")
MODEL_ENDPOINT = _str(
    "MODEL_ENDPOINT",
    "https://ai-academy-foundry.openai.azure.com/openai/v1/chat/completions",
)
API_KEY = _str("API_KEY", "")
EMBEDDINGS_MODEL = _str("EMBEDDINGS_MODEL", "qwen3-embedding:latest")
EMBEDDINGS_ENDPOINT = _str("EMBEDDINGS_ENDPOINT", "http://localhost:11434/api/embed")

# --- Prompting & retrieval --------------------------------------------------
SYSTEM_PROMPT = _str("SYSTEM_PROMPT", "")
CHUNK_SIZE = _int("CHUNK_SIZE", 100)
CHUNK_OVERLAP = _int("CHUNK_OVERLAP", 20)
TOP_N = _int("TOP_N", 4)
SIMILARITY_THRESHOLD = _float("SIMILARITY_THRESHOLD", 0.5)
MAX_CONTEXT_TOKENS = _int("MAX_CONTEXT_TOKENS", 16000)
KEEP_RECENT_MESSAGES = _int("KEEP_RECENT_MESSAGES", 4)

# --- Files & directories ----------------------------------------------------
EMBEDDINGS_FILE = _str("EMBEDDINGS_FILE", "embeddings.json")
STUDENT_RECORDS_FILE = _str("STUDENT_RECORDS_FILE", "student_records.json")
SESSIONS_DIR = _str("SESSIONS_DIR", "sessions")
UPLOADS_DIR = _str("UPLOADS_DIR", "uploads")
UPLOAD_MAX_FILE_BYTES = _int("UPLOAD_MAX_FILE_BYTES", 10_000_000)  # 10 MB

# --- Tools ------------------------------------------------------------------
WEB_SEARCH_MAX_RESULTS = _int("WEB_SEARCH_MAX_RESULTS", 5)

# --- Cost tracking (USD per million tokens) ---------------------------------
INPUT_TOKEN_PRICE_PER_MILLION = _float("INPUT_TOKEN_PRICE_PER_MILLION", 30)
OUTPUT_TOKEN_PRICE_PER_MILLION = _float("OUTPUT_TOKEN_PRICE_PER_MILLION", 70)

# --- Logging ----------------------------------------------------------------
LOG_FORMAT = _str("LOG_FORMAT", "[%(asctime)s] %(levelname)s [%(module)s]: %(message)s")
LOG_LEVEL = _str("LOG_LEVEL", "INFO")
LOG_FILE = _str("LOG_FILE", "app.log")
DEBUG = _bool("DEBUG", False)
