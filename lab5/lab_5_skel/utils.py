
import tiktoken

_encoding = tiktoken.get_encoding("cl100k_base")


def count_tokens(text):
    """Return the number of tiktoken tokens in the given text."""
    return len(_encoding.encode(text))
