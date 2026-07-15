"""
LLM integration layer.

This module is responsible for all communication
with the language model.
"""

import requests

from config import MODEL_NAME, MODEL_ENDPOINT
from tools.tool import Tool


class LLMClient:
    def _tool_to_dict(self, tool: Tool):
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
        }

    def generate_response(self, messages, tools=None):
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "stream": False
        }

        if tools:
            payload["tools"] = [self._tool_to_dict(t) for t in tools]

        response = requests.post(MODEL_ENDPOINT, json=payload)
        response.raise_for_status()
        return response.json()
