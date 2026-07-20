"""
Web Search Tool.

Searches the internet using DuckDuckGo (no API key required)
so the professor can look up recent information, libraries,
or documentation that is not in the knowledge base.
"""

try:
    from .tool import Tool
except ImportError:
    from tool import Tool

try:
    from config import WEB_SEARCH_MAX_RESULTS
except ImportError:
    from ..config import WEB_SEARCH_MAX_RESULTS


def web_search(query: str) -> str:
    """
    Search the web and return the top results as formatted text.

    Parameters:
        query (str): The search query.

    Returns:
        str: Formatted list of results (title, URL, snippet),
             or an error message if the search failed.
    """
    try:
        from ddgs import DDGS
    except ImportError:
        return (
            "Web search is unavailable: the 'ddgs' package is not "
            "installed. Install it with: pip install ddgs"
        )

    try:
        results = DDGS().text(query, max_results=WEB_SEARCH_MAX_RESULTS)
    except Exception as error:
        return f"Web search failed: {error}"

    if not results:
        return f"No web results found for: '{query}'"

    lines = []
    for index, result in enumerate(results, start=1):
        lines.append(
            f"{index}. {result.get('title', 'No title')}\n"
            f"   URL: {result.get('href', 'N/A')}\n"
            f"   {result.get('body', '')}"
        )
    return "\n\n".join(lines)


web_search_tool = Tool(
    name="web_search",
    description=(
        "Searches the internet with DuckDuckGo and returns the top results "
        "(title, URL, snippet). Use it when the knowledge base does not "
        "cover a question, or when up-to-date information is needed "
        "(new library versions, recent documentation, current events in "
        "software engineering)."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query, e.g. 'Python 3.13 new features'"
            }
        },
        "required": ["query"]
    },
    callback=web_search
)
