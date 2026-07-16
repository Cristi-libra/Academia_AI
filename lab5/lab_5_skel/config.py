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

MODEL_NAME = "gpt-5-mini"
API_KEY = 
EMBEDDINGS_MODEL = "qwen3-embedding:latest"
EMBEDDINGS_ENDPOINT = "http://localhost:11434/api/embed"
MODEL_ENDPOINT = (
    "https://ai-academy-foundry.openai.azure.com/openai/v1/chat/completions"
)
SYSTEM_PROMPT = ""
CHUNK_SIZE = 100
TOP_N = 20
SIMILARITY_THRESHOLD = 0.5
INPUT_TOKEN_PRICE_PER_MILION = 30
OUTPUT_TOKEN_PRICE_PER_MILION = 70
INPUT_TOKEN_TOTAL = 0
INPUT_TOKEN_TOTAL_PRICE = 0
OUTPUT_TOKEN_TOTAL = 0
OUTPUT_TOKEN_TOTAL_PRICE = 0
