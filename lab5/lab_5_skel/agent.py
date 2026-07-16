"""Core agent orchestration.
The agent coordinates communication between
the conversation context and the language model."""

import json

from embeddings_client import EmbeddingsClient


class Agent:
    def __init__(self, llm_client, context, tools=None):
        self.llm_client = llm_client
        self.context = context
        self.tools = {tool.name: tool for tool in tools} if tools else {}

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
        # TODO (2.4): comprimă istoricul ÎNAINTE de a adăuga mesajele noi ale
        # turei curente. Decomentează linia de mai jos după ce completezi
        # compress_history (și importă MAX_CONTEXT_TOKENS din config, sus):
        # self.context.compress_history(MAX_CONTEXT_TOKENS, self.llm_client)

        semantic_search_results = EmbeddingsClient().semantic_search(user_message)
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
        tool_calls = message.get("tool_calls", [])

        if tool_calls:
            self.context.add_message(message)

            tool_results = self._handle_tool_calls(tool_calls)
            for result in tool_results:
                self.context.add_message(result)
            
            self.context.track_input(self.context.get_history())
            response = self.llm_client.generate_response(
                self.context.get_history()
            )
            message = response["message"]

        self.context.add_message(message)
        self.context.track_output(message.get("content", ""))
        return message.get("content", "")
