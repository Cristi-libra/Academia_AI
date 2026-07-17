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

MODEL_NAME = "gpt-5-mini"
API_KEY = os.environ.get("CHATGPT_API_KEY", "")
EMBEDDINGS_MODEL = "qwen3-embedding:latest"
EMBEDDINGS_ENDPOINT = "http://localhost:11434/api/embed"
MODEL_ENDPOINT = (
    "https://ai-academy-foundry.openai.azure.com/openai/v1/chat/completions"
)
SYSTEM_PROMPT = ""
CHUNK_SIZE = 100
CHUNK_OVERLAP = 20
TOP_N = 20
SIMILARITY_THRESHOLD = 0.5
EMBEDDINGS_FILE = "embeddings.json"
MAX_CONTEXT_TOKENS = 4096
KEEP_RECENT_MESSAGES = 4
STUDENT_RECORDS_FILE = "student_records.json"
WEB_SEARCH_MAX_RESULTS = 5
FETCH_PAGE_MAX_CHARS = 8000
INPUT_TOKEN_PRICE_PER_MILLION = 30
OUTPUT_TOKEN_PRICE_PER_MILLION = 70

