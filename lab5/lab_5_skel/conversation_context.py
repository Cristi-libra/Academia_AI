"""
Conversation memory management.

This module is responsible for storing and retrieving
messages exchanged between the user and the AI assistant.
"""
from config import SYSTEM_PROMPT


class ConversationContext:
    def __init__(self):
        self.messages = [
            self.assemble_system_prompt()
        ]

    def assemble_system_prompt(self):
        return {
            "role": "system",
            "content": SYSTEM_PROMPT
        }

    def add_message(self, message):
        self.messages.append(message)

    def get_history(self):
        return self.messages
