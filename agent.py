"""Core agent orchestration.
The agent coordinates communication between
the conversation context and the language model."""

import json
import logging
from time import perf_counter

from embeddings_client import EmbeddingsClient
import config

logger = logging.getLogger(__name__)


def _short(text, limit=200):
    """Trims long text so a single log line stays readable."""
    text = str(text).replace("\n", " ")
    return text if len(text) <= limit else text[:limit] + "..."


class _Timer:
    """Context manager measuring a block's wall-clock duration, in seconds.

    Used to find out where a slow turn actually goes: retrieval, the model,
    or the tools. Read `.seconds` after the block.
    """

    def __enter__(self):
        self._start = perf_counter()
        return self

    def __exit__(self, *_exc):
        self.seconds = perf_counter() - self._start
        return False


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
        # Durata fiecărei faze din ultima tură (secunde) - vezi process_message.
        self.last_metrics = {"retrieval": 0.0, "model": 0.0, "tools": 0.0, "total": 0.0}

    def _handle_tool_calls(self, tool_calls):
        results = []
        for tc in tool_calls:
            tool_name = tc["function"]["name"]
            arguments = tc["function"]["arguments"]
            tool_id = tc["id"]

            tool = self.tools.get(tool_name)
            if tool:
                logger.info("Tool call: %s(%s)", tool_name, _short(arguments))
                try:
                    result = tool.callback(**json.loads(arguments))
                except Exception as error:
                    logger.exception("Tool '%s' failed: %s", tool_name, error)
                    result = f"Tool '{tool_name}' failed: {error}"
                else:
                    logger.info("Tool result: %s -> %s", tool_name, _short(result))
            else:
                logger.warning("Tool '%s' not found", tool_name)
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
        logger.info("User question: %s", _short(user_message))
        turn_started = perf_counter()

        # Cât timp s-a dus pe fiecare fază a turei (secunde).
        self.last_metrics = {"retrieval": 0.0, "model": 0.0, "tools": 0.0, "total": 0.0}

        # 2.4: comprimă istoricul ÎNAINTE de a adăuga mesajele noi ale turei.
        self.context.compress_history(config.MAX_CONTEXT_TOKENS, self.llm_client)
        self.last_reasoning = ""
        self.last_tools_used = []

        with _Timer() as retrieval_timer:
            semantic_search_results = self.embeddings_client.semantic_search(user_message)
        self.last_metrics["retrieval"] = retrieval_timer.seconds

        if semantic_search_results:
            logger.info(
                "Retrieved %d relevant chunks: %s",
                len(semantic_search_results),
                [r["document_id"] for r in semantic_search_results],
            )
            relevant_text = "\n\n".join(
                result["content"] for result in semantic_search_results
            )
            self.context.add_message({
                "role": "system",
                "content": "Relevant knowledge from the knowledge base:\n\n" + relevant_text
            })
        else:
            logger.warning(
                "No relevant chunks found for: %s", _short(user_message, 100)
            )
            self.context.add_message({
                "role": "system",
                "content": "No relevant knowledge found, try responding from your own knowledge in the limits of your role"
            })

        self.context.add_message({
            "role": "user",
            "content": user_message
        })

        self.context.track_input(self.context.get_history())
        with _Timer() as model_timer:
            response = self.llm_client.generate_response(
                self.context.get_history(),
                tools=list(self.tools.values())
            )
        self.last_metrics["model"] += model_timer.seconds

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

            with _Timer() as tools_timer:
                tool_results = self._handle_tool_calls(message["tool_calls"])
            self.last_metrics["tools"] += tools_timer.seconds

            for result in tool_results:
                self.context.add_message(result)

            self.context.track_input(self.context.get_history())
            with _Timer() as model_timer:
                response = self.llm_client.generate_response(
                    self.context.get_history(),
                    tools=list(self.tools.values())
                )
            self.last_metrics["model"] += model_timer.seconds

            message = response["message"]
            reasoning = self._extract_reasoning(message)
            if reasoning:
                self.last_reasoning = reasoning
            rounds += 1

        # Dacă tot cere tool-uri după limită, dăm un mesaj de siguranță.
        if message.get("tool_calls"):
            logger.warning(
                "Tool loop did not converge after %d rounds; giving up",
                MAX_TOOL_ROUNDS,
            )
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

        logger.info("Model answer: %s", _short(content))
        logger.info(
            "Token usage: input=%d output=%d",
            self.context.input_tokens,
            self.context.output_tokens,
        )

        self.last_metrics["total"] = perf_counter() - turn_started
        logger.info(
            "Timing: total=%.2fs (retrieval=%.2fs, model=%.2fs over %d call(s), "
            "tools=%.2fs)",
            self.last_metrics["total"],
            self.last_metrics["retrieval"],
            self.last_metrics["model"],
            rounds + 1,
            self.last_metrics["tools"],
        )
        return content
