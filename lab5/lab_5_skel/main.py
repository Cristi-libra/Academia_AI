"""
Application entry point.

This module provides a simple command-line
interface for interacting with the agent.
"""

from agent import Agent
from embedding_generator import embedding_generator
import config
from utils import count_tokens
from llm_client import LLMClient
from conversation_context import ConversationContext
from tools.tools import tools


def main():
    embedding_generator()
    context = ConversationContext()

    llm_client = LLMClient()

    agent = Agent(llm_client, context, tools=tools)

    print("AI Assistant started. Type 'exit' to quit.")

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() == "exit":
            break

        config.INPUT_TOKEN_TOTAL += count_tokens(user_input)
        config.INPUT_TOKEN_TOTAL_PRICE += count_tokens(user_input) / 1_000_000 * config.INPUT_TOKEN_PRICE_PER_MILION

        response = agent.process_message(user_input)

        config.OUTPUT_TOKEN_TOTAL += count_tokens(response)
        config.OUTPUT_TOKEN_TOTAL_PRICE += count_tokens(response) / 1_000_000 * config.OUTPUT_TOKEN_PRICE_PER_MILION

        print("\nToken Usage Summary:")
        print("Nr. tokens in user input:", count_tokens(user_input))
        print("Nr. tokens in AI response:", count_tokens(response))
        print("Nr. total tokens in user input:", config.INPUT_TOKEN_TOTAL)
        print("Input token total price:", config.INPUT_TOKEN_TOTAL_PRICE)
        print("Nr. total tokens in AI response:", config.OUTPUT_TOKEN_TOTAL)
        print("Output token total price:", config.OUTPUT_TOKEN_TOTAL_PRICE)
        print("Total token price:", config.INPUT_TOKEN_TOTAL_PRICE + config.OUTPUT_TOKEN_TOTAL_PRICE)


        print(f"\nAI: {response}")


if __name__ == "__main__":
    main()
