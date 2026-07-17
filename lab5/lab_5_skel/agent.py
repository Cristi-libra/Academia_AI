"""Core agent orchestration.
The agent coordinates communication between
the conversation context and the language model."""

import json

from embeddings_client import EmbeddingsClient
import config


REASONING_FIELDS = ("reasoning_content", "reasoning", "thinking")


class Agent:
    def __init__(self, llm_client, context, tools=None):
        self.llm_client = llm_client
        self.context = context
        self.tools = {tool.name: tool for tool in tools} if tools else {}
        self.embeddings_client = EmbeddingsClient()
        self.last_reasoning = None

    def _handle_tool_calls(self, tool_calls):
        results = []
        for tc in tool_calls:
            tool_name = tc["function"]["name"]
            arguments = tc["function"]["arguments"]
            tool_id = tc["id"]

            tool = self.tools.get(tool_name)
            if tool:
                result = tool.callback(**json.loads(arguments))
            else:
                result = f"Tool '{tool_name}' not found"

            results.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "content": str(result)
            })
        return results

    def process_message(self, user_message):
        self.context.compress_history(config.MAX_CONTEXT_TOKENS, self.llm_client)

        semantic_search_results = self.embeddings_client.semantic_search(user_message)
        if semantic_search_results:
            relevant_text = "\n\n".join(
                result["content"] for result in semantic_search_results
            )
            self.context.add_message({
                "role": "system",
                "content": "Relevant knowledge from the knowledge base:\n\n" + relevant_text
            })
        else:
            self.context.add_message({
                "role": "system",
                "content": "No relevant knowledge found, try responding from your own knowledge in the limits of your role"
            })

        self.context.add_message({
            "role": "user",
            "content": user_message
        })

        self.context.track_input(self.context.get_history())
        response = self.llm_client.generate_response(
            self.context.get_history(),
            tools=list(self.tools.values())
        )
        message = response["message"]

        # Some requests need more than one tool call in sequence (e.g. list
        # uploaded files, then read the one that's relevant) - keep offering
        # tools and looping until the model answers with plain content.
        # MAX_TOOL_ROUNDS is a safety cap against a runaway tool-call loop.
        MAX_TOOL_ROUNDS = 5
        rounds = 0
        while message.get("tool_calls") and rounds < MAX_TOOL_ROUNDS:
            self.context.add_message(message)

            tool_results = self._handle_tool_calls(message["tool_calls"])
            for result in tool_results:
                self.context.add_message(result)

            self.context.track_input(self.context.get_history())
            response = self.llm_client.generate_response(
                self.context.get_history(),
                tools=list(self.tools.values())
            )
            message = response["message"]
            rounds += 1

        if message.get("tool_calls"):
            # Hit MAX_TOOL_ROUNDS without the model settling on a final
            # answer - don't persist a tool call with no result, and don't
            # return a silently empty reply.
            message = {
                "role": "assistant",
                "content": (
                    "I attempted several tool calls but couldn't reach a "
                    "final answer. Could you rephrase your request?"
                ),
            }

        self.context.add_message(message)
        content = message.get("content") or ""
        self.context.track_output(content)

        # Some reasoning-capable models return their chain-of-thought under
        # one of these keys, separate from the final answer. Passed through
        # as-is if present; None (and simply not shown) otherwise.
        self.last_reasoning = next(
            (message[field] for field in REASONING_FIELDS if message.get(field)),
            None,
        )

        return content
