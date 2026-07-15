"""
Lucky Number Tool.

This tool generates a lucky number based on a user's
birth date and the current date.

The implementation is intentionally incomplete and must
be finalized during the laboratory.
"""

try:
    from .tool import Tool
except ImportError:
    from tool import Tool

import datetime


def lucky_number(birth_date):
    """
    Generate a lucky number.

    Parameters:
        birth_date (str): User birth date in format DDMMYYYY.

    Returns:
        int: The generated lucky number.

    TODO:
    - Get the current date.
    - Extract all digits from the current date.
    - Extract all digits from the birth date.
    - Sum all digits together.
    - Return the resulting value.

    Example:

        Current date:
        14/07/2026

        Birth date:
        05/09/2000

        Calculation:
        1 + 4 + 0 + 7 + 2 + 0 + 2 + 6
        +
        0 + 5 + 0 + 9 + 2 + 0 + 0 + 0

        Result:
        38
    """
    current_date = datetime.datetime.now().strftime("%d%m%Y")
    all_digits = current_date + birth_date
    print(all_digits)
    number = sum(int(digit) for digit in all_digits)
    return number


"""
Create and return the tool definition.

Configure the Tool instance.

Name:
    A short unique identifier used internally by the agent.

Description:
    A natural language description explaining
    when the tool should be used.

Parameters:
    A dictionary describing all arguments expected
    by the lucky_number function.

Callback:
    The Python function that must be executed when
    the tool is invoked.
"""

lucky_number_tool = Tool(
    name="lucky_number",
    description=(
        "Generates a lucky number based on the user's birth date and today's "
        "date"
    ),
    parameters={
        "type": "object",
        "properties": {
            "birth_date": {
                "type": "string",
                "description": (
                    "The user's birth date in format DDMMYYYY, e.g. 31121993 "
                    "for 31/12/1993"
                )
            }
        },
        "required": ["birth_date"]
    },
    callback=lucky_number
)
