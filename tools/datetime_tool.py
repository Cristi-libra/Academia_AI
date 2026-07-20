"""
Current Datetime Tool.

Language models do not know the current date or time.
This tool provides it, so evaluations get correct dates
and time-related questions get accurate answers.
"""

import datetime

try:
    from .tool import Tool
except ImportError:
    from tool import Tool


def current_datetime() -> str:
    """
    Return the current local date and time.

    Returns:
        str: Human-readable current date and time.
    """
    now = datetime.datetime.now()
    return now.strftime("Current date and time: %A, %d %B %Y, %H:%M")


current_datetime_tool = Tool(
    name="current_datetime",
    description=(
        "Returns the current local date and time. Use it whenever the "
        "current date or time is needed (e.g. dating an evaluation, "
        "answering 'what day is it?'). Never guess the date."
    ),
    parameters={
        "type": "object",
        "properties": {}
    },
    callback=current_datetime
)
