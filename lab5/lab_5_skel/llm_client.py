"""
LLM integration layer.

This module is responsible for all communication
with the language model.
"""

import requests

try:
    from .config import MODEL_NAME, MODEL_ENDPOINT, API_KEY
except ImportError:
    from config import MODEL_NAME, MODEL_ENDPOINT, API_KEY

from tools.tool import Tool


class LLMClient:
    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if "azure.com" in MODEL_ENDPOINT:
            headers["api-key"] = API_KEY
        else:
            headers["Authorization"] = f"Bearer {API_KEY}"
        return headers
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

        endpoint = MODEL_ENDPOINT
        if endpoint.endswith("/openai/v1"):
            endpoint = endpoint.rstrip("/") + "/chat/completions"
        error_message = None
        response = None
        for _ in range(2):
            try:
                response = requests.post(
                    endpoint, json=payload, headers=self._headers(), timeout=60
                )
                response.raise_for_status()
                error_message = None
                break
            except requests.exceptions.Timeout:
                error_message = (
                    "The model took too long to answer (timeout). "
                    "Please try again."
                )
            except requests.exceptions.ConnectionError:
                error_message = (
                    "Could not reach the model endpoint. "
                    "Check your internet connection and try again."
                )
            except requests.exceptions.HTTPError as error:
                status = error.response.status_code
                if status in (401, 403):
                    error_message = (
                        "The model rejected the API key. Check that the "
                        "GEMINI_API_KEY environment variable is set correctly."
                    )
                    break  # retrying with the same key cannot succeed
                elif status == 429:
                    error_message = (
                        "Too many requests (rate limit). "
                        "Wait a moment and try again."
                    )
                elif status >= 500:
                    error_message = (
                        f"The model service is temporarily unavailable "
                        f"(HTTP {status}). Please try again in a moment."
                    )
                else:
                    error_message = (
                        f"The model request failed with HTTP {status}: "
                        f"{error.response.text[:200]}"
                    )
                    break  # a client-side error will not fix itself on retry

        if error_message is not None:
            return {"message": {"content": error_message}}

        try:
            data = response.json()
        except ValueError:
            return {"message": {"content": (
                "The model returned an unreadable response. Please try again."
            )}}
        if "message" in data:
            return data

        if "choices" in data and len(data["choices"]) > 0:
            message = data["choices"][0].get("message")
            if message is not None:
                return {"message": message, "raw": data}

        raise ValueError(f"Unexpected model response format: {data}")
