
import tiktoken

def count_tokens(text):
    """Return the number of word tokens in the given text."""
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    return len(tokens)
