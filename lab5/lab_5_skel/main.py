"""
Application entry point.

This module provides a simple command-line
interface for interacting with the agent.
"""

import os
import shutil

from agent import Agent
from embedding_generator import embedding_generator
import config
from llm_client import LLMClient
from conversation_context import ConversationContext
from tools.file_tool import make_file_tools
from tools.tools import tools

CLI_USER_ID = "cli"


def session_path(name):
    return os.path.join(config.SESSIONS_DIR, f"{name}.json")


def main():
    embedding_generator()
    name = input("Numele tău (opțional, Enter pentru a sări): ").strip()
    context = ConversationContext(username=name or None)

    default_session = session_path("cli_default")
    if os.path.exists(default_session):
        answer = input("Continui conversația anterioară? [y/n]: ")
        if answer.strip().lower() == "y":
            context.load_from_file(default_session)

    llm_client = LLMClient()

    agent = Agent(llm_client, context, tools=tools + make_file_tools(CLI_USER_ID))

    print(
        "AI Assistant started. Type 'exit' to quit, 'save <name>' or 'load <name>' "
        "to manage sessions, 'upload <path>' to make a file available to the agent."
    )

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() == "exit":
            context.save_to_file(default_session)
            break

        if user_input.lower().startswith("save "):
            name = user_input[len("save "):].strip()
            context.save_to_file(session_path(name))
            print(f"Session saved to {session_path(name)}")
            continue

        if user_input.lower().startswith("load "):
            name = user_input[len("load "):].strip()
            context.load_from_file(session_path(name))
            print(f"Session loaded from {session_path(name)}")
            continue

        if user_input.lower().startswith("upload "):
            source_path = user_input[len("upload "):].strip()
            if not os.path.isfile(source_path):
                print(f"File not found: {source_path}")
                continue
            user_dir = os.path.join(config.UPLOADS_DIR, CLI_USER_ID)
            os.makedirs(user_dir, exist_ok=True)
            dest_name = os.path.basename(source_path)
            shutil.copyfile(source_path, os.path.join(user_dir, dest_name))
            print(f"Uploaded '{dest_name}' - ask the agent to read it.")
            continue

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
