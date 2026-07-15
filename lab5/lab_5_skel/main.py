"""
Application entry point.

This module provides a simple command-line
interface for interacting with the agent.
"""

from agent import Agent
from llm_client import LLMClient
from conversation_context import ConversationContext
from tools.tools import tools


def main():
    context = ConversationContext()

    llm_client = LLMClient()

    agent = Agent(llm_client, context, tools=tools)

    print("AI Assistant started. Type 'exit' to quit.")

    while True:
        user_input = input(
            "\nYou: "
        )

        if user_input.lower() == "exit":
            break

        response = agent.process_message(user_input)

        print(f"\nAI: {response}")


if __name__ == "__main__":
    main()
