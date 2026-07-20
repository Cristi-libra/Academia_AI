"""
Knowledge Search Tool.

Exposes the semantic search over the course knowledge base as a
tool, so the professor can actively look up course materials on
demand - not only rely on the automatic per-message retrieval.

Requires the embeddings file to exist and Ollama to be running
(it embeds the query).
"""

try:
    from .tool import Tool
except ImportError:
    from tool import Tool


def search_knowledge_base(query: str) -> str:
    """
    Semantically search the course knowledge base.

    Parameters:
        query (str): What to look for in the course materials.

    Returns:
        str: The relevant chunks (source document, similarity score,
             content), or an explanatory message if nothing was found
             or the search infrastructure is unavailable.
    """
    try:
        from embeddings_client import EmbeddingsClient
    except ImportError:
        from ..embeddings_client import EmbeddingsClient

    try:
        results = EmbeddingsClient().semantic_search(query)
    except FileNotFoundError:
        return (
            "The embeddings file does not exist yet. Restart the "
            "application so it can be generated."
        )
    except Exception as error:
        return (
            f"Knowledge base search failed: {error}. "
            "Check that Ollama is running (it embeds the query)."
        )

    if not results:
        return f"No relevant course material found for: '{query}'"

    lines = []
    for result in results:
        lines.append(
            f"[{result['document_id']} | chunk {result['chunk_index']} | "
            f"similarity {result['similarity']:.2f}]\n{result['content']}"
        )
    return "\n\n".join(lines)


knowledge_search_tool = Tool(
    name="search_knowledge_base",
    description=(
        "Semantically searches the course knowledge base (facts and "
        "procedures) and returns the most relevant passages with their "
        "source document. Use it to look up course materials, grading "
        "rubrics or procedures before answering course-related questions."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "What to search for, e.g. 'complexity of dict lookup' "
                    "or 'code review grading criteria'."
                )
            }
        },
        "required": ["query"]
    },
    callback=search_knowledge_base
)
