"""
Application entry point.

This module provides a simple command-line
interface for interacting with the agent.
"""

from agent import Agent
from logging_config import setup_logging
from embedding_generator import embedding_generator
import config
from llm_client import LLMClient
from conversation_context import ConversationContext
from tools.tools import tools


def main():
    setup_logging()
    embedding_generator()
    context = ConversationContext()

    llm_client = LLMClient()

    agent = Agent(llm_client, context, tools=tools)

    print("AI Assistant started. Type 'exit' to quit.")

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() == "exit":
            break

        response = agent.process_message(user_input)

        print("\nToken Usage Summary:")
        print("Nr. total tokens in user input:", context.input_tokens)
        print("Input token total price:", context.input_tokens * config.INPUT_TOKEN_PRICE_PER_MILLION / 1_000_000)
        print("Nr. total tokens in AI response:", context.output_tokens)
        print("Output token total price:", context.output_tokens * config.OUTPUT_TOKEN_PRICE_PER_MILLION / 1_000_000)
        print("Total token price:", context.input_tokens * config.INPUT_TOKEN_PRICE_PER_MILLION / 1_000_000 + context.output_tokens * config.OUTPUT_TOKEN_PRICE_PER_MILLION / 1_000_000)


        print(f"\nAI: {response}")


if __name__ == "__main__":
    main()
