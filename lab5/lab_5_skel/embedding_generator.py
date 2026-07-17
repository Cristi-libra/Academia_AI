import json
import os
from config import EMBEDDINGS_FILE
from document_chunker import load_n_chunk_docs
from embeddings_client import EmbeddingsClient

def embedding_generator():
    if os.path.exists(EMBEDDINGS_FILE):
        if os.path.getmtime("knowledge") < os.path.getmtime(EMBEDDINGS_FILE):
            print("Knowledge base has not changed since last embedding generation. Skipping generation.")
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
        print(f"Could not generate embeddings: {error}")
        print(
            "The assistant will run WITHOUT knowledge retrieval. "
            "Start Ollama and restart the application to enable it."
        )
        return

    with open(EMBEDDINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(embedding_list, f, ensure_ascii=False, indent=4)
