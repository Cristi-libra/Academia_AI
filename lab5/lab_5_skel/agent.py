"""Core agent orchestration.
The agent coordinates communication between
the conversation context and the language model."""

import json

from embeddings_client import EmbeddingsClient
import config


class Agent:
    def __init__(self, llm_client, context, tools=None):
        self.llm_client = llm_client
        self.context = context
        self.tools = {tool.name: tool for tool in tools} if tools else {}
        # O singură instanță, refolosită la fiecare mesaj (nu una nouă de fiecare dată).
        self.embeddings_client = EmbeddingsClient()
        # Best-effort: unele modele "reasoning" întorc gândirea lor separat.
        # O păstrăm aici ca s-o poată afișa interfața web (dacă există).
        self.last_reasoning = ""
        self.last_tools_used = []

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

    def _extract_reasoning(self, message):
        """Întoarce textul de 'thinking' dacă modelul îl expune, altfel ''."""
        for key in ("reasoning_content", "reasoning", "thinking"):
            value = message.get(key)
            if value:
                return str(value)
        return ""

    def process_message(self, user_message):
        # 2.4: comprimă istoricul ÎNAINTE de a adăuga mesajele noi ale turei.
        self.context.compress_history(config.MAX_CONTEXT_TOKENS, self.llm_client)
        self.last_reasoning = ""
        self.last_tools_used = []

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
        self.last_reasoning = self._extract_reasoning(message)

        # Multi-step tool calling: cât timp modelul cere tool-uri, le executăm și
        # îl re-chemăm CU tool-uri, ca să poată înlănțui (ex. read_uploaded_file →
        # save_student_evaluation). Limită de siguranță ca să nu bucleze la infinit.
        MAX_TOOL_ROUNDS = 5
        rounds = 0
        while message.get("tool_calls") and rounds < MAX_TOOL_ROUNDS:
            self.last_tools_used += [tc["function"]["name"] for tc in message["tool_calls"]]
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
            reasoning = self._extract_reasoning(message)
            if reasoning:
                self.last_reasoning = reasoning
            rounds += 1

        # Dacă tot cere tool-uri după limită, dăm un mesaj de siguranță.
        if message.get("tool_calls"):
            message = {
                "role": "assistant",
                "content": (
                    "Am încercat mai multe operații, dar nu am ajuns la un răspuns "
                    "final. Poți reformula cererea?"
                ),
            }

        self.context.add_message(message)
        content = message.get("content", "") or ""
        self.context.track_output(content)
        return content
