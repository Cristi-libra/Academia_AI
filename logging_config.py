"""
Application-wide logging setup.

Call setup_logging() once, from an entry point (main.py or api.py).
Every other module just does `logger = logging.getLogger(__name__)`.
"""

import logging
import sys

import config


def setup_logging():
    """Configures the root logger: console + log file.

    Both handlers are forced to UTF-8. The app logs Romanian text, and on
    Windows the default encoding is cp1252, which mangles diacritics in the
    console and can raise UnicodeEncodeError when writing the log file.
    """
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass  # not a real stream (e.g. captured by a test runner) - ignore

    logging.basicConfig(
        level=config.LOG_LEVEL,
        format=config.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
        ],
    )
