"""
Conversation memory management.

This module is responsible for storing and retrieving
messages exchanged between the user and the AI assistant.
"""


try:
    from .config import SYSTEM_PROMPT
except ImportError:
    from config import SYSTEM_PROMPT

import json
import os


class ConversationContext:
    def __init__(self):
        self.messages = [
            self.assemble_system_prompt()
        ]

    def assemble_system_prompt(self):
        # TODO: return a system message dict with the system prompt from config
        # Hint: Observe the message format used in agent.py
        # Hint: The system prompt should be a message dict with role "system"
        prompt = SYSTEM_PROMPT
        files_to_read = os.listdir("knowledge")
        for file_to_read in files_to_read:
            sub_files = os.listdir(os.path.join("knowledge", file_to_read))
            for sub_file in sub_files:
                if file_to_read == "facts" or file_to_read == "procedures":
                    if sub_file.endswith(".json"):
                        with open(os.path.join("knowledge", file_to_read, sub_file), "r", encoding="utf-8") as f:
                            facts = json.load(f)
                            for fact in facts:
                                if fact.get("always_load"):
                                    with open(os.path.join("knowledge", file_to_read, fact.get("id")+'.md'), "r", encoding="utf-8") as f2:
                                        prompt += "\n" + f2.read()
                elif file_to_read == "prompts":
                    with open(os.path.join("knowledge", file_to_read, sub_file), "r", encoding="utf-8") as f:
                        prompt += "\n" + f.read()

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
    def compress_history(self, max_tokens):
        """
        Compresses the conversation history to fit within the specified token limit.

        This method removes the oldest messages from the conversation history
        until the total token count is less than or equal to max_tokens.

        Args:
            max_tokens (int): The maximum number of tokens allowed in the conversation history.
        """
        
