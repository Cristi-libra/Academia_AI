"""
Fetch Page Tool.

Downloads a web page (e.g. official documentation found via
web_search) and extracts its readable text so the professor
can quote real sources instead of guessing.
"""

import requests

try:
    from .tool import Tool
except ImportError:
    from tool import Tool

try:
    from config import FETCH_PAGE_MAX_CHARS
except ImportError:
    from ..config import FETCH_PAGE_MAX_CHARS


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )
}


def fetch_page(url: str) -> str:
    """
    Fetch a web page and return its readable text content.

    Parameters:
        url (str): The full URL of the page to fetch.

    Returns:
        str: The extracted text (truncated to FETCH_PAGE_MAX_CHARS),
             or an error message if the page could not be fetched.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return (
            "Page fetching is unavailable: the 'beautifulsoup4' package is "
            "not installed. Install it with: pip install beautifulsoup4"
        )

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return f"The request to {url} timed out."
    except requests.exceptions.RequestException as error:
        return f"Could not fetch {url}: {error}"

    soup = BeautifulSoup(response.content, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    text = " ".join(soup.get_text(separator=" ").split())

    if not text:
        return f"The page at {url} contains no readable text."

    if len(text) > FETCH_PAGE_MAX_CHARS:
        return (
            text[:FETCH_PAGE_MAX_CHARS]
            + f"\n\n[Content truncated at {FETCH_PAGE_MAX_CHARS} characters.]"
        )
    return text


fetch_page_tool = Tool(
    name="fetch_page",
    description=(
        "Downloads a web page and returns its readable text content. Use it "
        "to read documentation, articles or references found with "
        "web_search, so answers can be based on the actual source."
    ),
    parameters={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": (
                    "The full URL to fetch, e.g. "
                    "'https://docs.python.org/3/library/ast.html'"
                )
            }
        },
        "required": ["url"]
    },
    callback=fetch_page
)
