"""
Conversation memory management.

This module is responsible for storing and retrieving
messages exchanged between the user and the AI assistant.
"""


try:
    from .config import SYSTEM_PROMPT
except ImportError:
    from config import SYSTEM_PROMPT
import config

import json
import os
from utils import count_tokens


class ConversationContext:
    def __init__(self, username=None):
        self.username = username
        self.messages = [self.assemble_system_prompt()]
        self.input_tokens = 0
        self.output_tokens = 0
    
    def track_input(self, messages):
        for message in messages:
            self.input_tokens += count_tokens(str(message))
    
    def track_output(self, response):
        self.output_tokens += count_tokens(response)

    def assemble_system_prompt(self):
        # TODO: return a system message dict with the system prompt from config
        # Hint: Observe the message format used in agent.py
        # Hint: The system prompt should be a message dict with role "system"
        prompt = SYSTEM_PROMPT
        try:
            files_to_read = os.listdir("knowledge")
        except FileNotFoundError:
            print(
                "Warning: the 'knowledge' folder does not exist - "
                "starting with an empty system prompt."
            )
            return {"role": "system", "content": prompt}

        for file_to_read in files_to_read:
            sub_files = os.listdir(os.path.join("knowledge", file_to_read))
            for sub_file in sub_files:
                if file_to_read == "facts" or file_to_read == "procedures":
                    if sub_file.endswith(".json"):
                        registry_path = os.path.join("knowledge", file_to_read, sub_file)
                        try:
                            with open(registry_path, "r", encoding="utf-8") as f:
                                facts = json.load(f)
                        except json.JSONDecodeError:
                            print(f"Warning: registry '{registry_path}' is not valid JSON - skipped.")
                            continue
                        for fact in facts:
                            if fact.get("always_load"):
                                doc_path = os.path.join("knowledge", file_to_read, fact.get("id") + '.md')
                                try:
                                    with open(doc_path, "r", encoding="utf-8") as f2:
                                        prompt += "\n\n## " + fact.get("name") + "\n" + f2.read()
                                except FileNotFoundError:
                                    print(f"Warning: document '{doc_path}' is listed in the registry but does not exist - skipped.")
                elif file_to_read == "prompts":
                    with open(os.path.join("knowledge", file_to_read, sub_file), "r", encoding="utf-8") as f:
                        prompt += "\n" + f.read()

        if self.username:
            prompt += (
                "\n\n## Current User\n"
                f"The person you are talking to is: {self.username}. When using "
                "tools that require a student/user name (save_student_evaluation, "
                "get_student_record), use this name automatically - do not ask "
                "them to state it, unless they explicitly refer to someone else's "
                "work (e.g. grading a classmate)."
            )

        return {
            "role": "system",
            "content": prompt
        }

    def add_message(self, message):
        # TODO: Implement message addition logic

        self.messages.append(message)

    def get_history(self):
        # TODO: return the full message history
        return self.messages
    
    def compress_history(self, max_tokens, llm_client=None):
        """
        Ține istoricul conversației sub max_tokens ("smart compression").

        System prompt-ul (self.messages[0]) nu se atinge niciodată; ultimele
        KEEP_RECENT_MESSAGES rămân intacte; tot ce e între ele se trimite la
        LLM cu instrucțiunea "rezumă" și se înlocuiește cu un singur mesaj.
        Dacă llm_client e None sau rezumatul eșuează → fallback pe sliding
        window (pur și simplu arunci mesajele vechi).
        """
        total = 0
        for message in self.messages:
            total += count_tokens(str(message))

        if total <= max_tokens:
            return

        if len(self.messages) <= 1 + config.KEEP_RECENT_MESSAGES:
            return

        system_prompt = self.messages[0]
        recent = self.messages[-config.KEEP_RECENT_MESSAGES:]
        old = self.messages[1:-config.KEEP_RECENT_MESSAGES]

        while recent and recent[0].get("role") == "tool":
            old.append(recent.pop(0))

        lines = []
        for m in old:
            lines.append(f"{m.get('role')}: {str(m.get('content') or '')}")
        conversation_text = "\n".join(lines)

        summary = None
        if llm_client is not None:
            response = llm_client.generate_response([
                {"role": "system", "content": "You summarize conversations. Reply ONLY with a short factual summary (max 150 words). Keep: names, grades given, decisions made, questions that are still open."},
                {"role": "user", "content": conversation_text}
            ])
            if not response.get("error"):
                summary = response["message"].get("content", "")
            if not summary:
                summary = None

        if summary:
            self.messages = [system_prompt,
                             {"role": "system",
                              "content": "Summary of the earlier "
                                         "conversation: " + summary}] + recent
        else:
            self.messages = [system_prompt] + recent

    def save_to_file(self, path):
        """Salvează istoricul (fără system prompt) + contoarele de tokeni."""
        data = {
            "messages": self.messages[1:],
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_from_file(self, path):
        """Reîncarcă istoricul salvat peste system prompt-ul proaspăt asamblat."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return
        except json.JSONDecodeError:
            print(f"Warning: session file '{path}' is not valid JSON - starting a new session.")
            return

        self.messages = [self.messages[0]] + data.get("messages", [])
        self.input_tokens = data.get("input_tokens", 0)
        self.output_tokens = data.get("output_tokens", 0)

