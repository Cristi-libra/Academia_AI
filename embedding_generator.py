import json
import os
import logging
from config import EMBEDDINGS_FILE
from document_chunker import load_n_chunk_docs
from embeddings_client import EmbeddingsClient

logger = logging.getLogger(__name__)


def _knowledge_mtime():
    """Cel mai recent moment de modificare din TOATE fișierele din knowledge/.

    os.path.getmtime('knowledge') vede doar folderul, nu și fișierele din
    subfoldere, așa că mergem recursiv cu os.walk.
    """
    latest = 0.0
    for root, _dirs, files in os.walk("knowledge"):
        for name in files:
            latest = max(latest, os.path.getmtime(os.path.join(root, name)))
    return latest


def embedding_generator():
    if os.path.exists(EMBEDDINGS_FILE):
        if _knowledge_mtime() < os.path.getmtime(EMBEDDINGS_FILE):
            logger.info("Knowledge base unchanged since last run - skipping embedding generation.")
            return

    embedding_list = []
    chunks = load_n_chunk_docs()
    embeddings_client = EmbeddingsClient()
    try:
        for chunk in chunks:
            embedded = embeddings_client.get_embedding(chunk["content"])
            chunk_with_embedding = {
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"],
                "embedding": embedded
            }
            embedding_list.append(chunk_with_embedding)
    except ConnectionError as error:
        logger.error("Could not generate embeddings: %s", error)
        logger.error(
            "The assistant will run WITHOUT knowledge retrieval. "
            "Start Ollama and restart the application to enable it."
        )
        return

    with open(EMBEDDINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(embedding_list, f, ensure_ascii=False, indent=4)
    logger.info("Generated embeddings for %d chunks.", len(embedding_list))
