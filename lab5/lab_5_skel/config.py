"""
Application configuration.

This module contains all configurable settings used by the AI agent.

Future exercises may extend this file with:
- Model configuration
- API credentials
- Prompt templates
- Embedding settings
- Logging configuration
"""

import os

MODEL_NAME = "gemini-3.1-flash-lite"
API_KEY = os.environ.get("GEMINI_API_KEY", "")
EMBEDDINGS_MODEL = "bge-m3:latest"
EMBEDDINGS_ENDPOINT = "http://localhost:11434/api/embed"
MODEL_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
)
SYSTEM_PROMPT = ""
CHUNK_SIZE = 100
CHUNK_OVERLAP = 20
TOP_N = 4
SIMILARITY_THRESHOLD = 0.5
DEBUG = False
EMBEDDINGS_FILE = "embeddings.json"
MAX_CONTEXT_TOKENS = 16000
KEEP_RECENT_MESSAGES = 4
STUDENT_RECORDS_FILE = "student_records.json"
SESSIONS_DIR = "sessions"
UPLOADS_DIR = "uploads"
UPLOAD_MAX_FILE_BYTES = 10_000_000  # 10 MB
WEB_SEARCH_MAX_RESULTS = 5
INPUT_TOKEN_PRICE_PER_MILLION = 30
OUTPUT_TOKEN_PRICE_PER_MILLION = 70

