
import nltk
from nltk.tokenize import word_tokenize
nltk.download('punkt_tab')

def count_tokens(text):
    """Return the number of word tokens in the given text."""
    tokens = word_tokenize(text)
    print("------------------------------------------------------")
    print(f"Tokens: {tokens}")
    print("------------------------------------------------------")
    return len(tokens)
