import tiktoken

# Encoding-ul se creează O SINGURĂ dată la import (e scump), nu la fiecare apel.
_ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text):
    """Return the number of tokens in the given text (tiktoken, cl100k_base)."""
    return len(_ENCODING.encode(text))
