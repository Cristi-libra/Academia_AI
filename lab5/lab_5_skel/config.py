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
TOP_N = 20
SIMILARITY_THRESHOLD = 0.5
EMBEDDINGS_FILE = "embeddings.json"
MAX_CONTEXT_TOKENS = 6000
KEEP_RECENT_MESSAGES = 4
STUDENT_RECORDS_FILE = "student_records.json"
WEB_SEARCH_MAX_RESULTS = 5
FETCH_PAGE_MAX_CHARS = 8000
INPUT_TOKEN_PRICE_PER_MILLION = 30
OUTPUT_TOKEN_PRICE_PER_MILLION = 70

