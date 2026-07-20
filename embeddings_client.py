import json
import logging

import requests

from config import EMBEDDINGS_MODEL, EMBEDDINGS_ENDPOINT, API_KEY, SIMILARITY_THRESHOLD, TOP_N, EMBEDDINGS_FILE

logger = logging.getLogger(__name__)


class EmbeddingsClient:
    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if "azure.com" in EMBEDDINGS_ENDPOINT:
            headers["api-key"] = API_KEY
        else:
            headers["Authorization"] = f"Bearer {API_KEY}"
        return headers
    def get_embedding(self, text: str) -> list[float]:
        try:
            response = requests.post(
                EMBEDDINGS_ENDPOINT,
                json={
                    "model": EMBEDDINGS_MODEL,
                    "input": text
                },
                headers=self._headers(),
                timeout=60
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Could not connect to the embeddings server at "
                f"{EMBEDDINGS_ENDPOINT}. Is Ollama running? Start it and try again."
            )
        except requests.exceptions.Timeout:
            raise ConnectionError(
                "The embeddings server did not answer in time (timeout)."
            )
        except requests.exceptions.HTTPError:
            raise ConnectionError(
                f"The embeddings server returned an error: "
                f"HTTP {response.status_code} - {response.text[:200]}"
            )

        return response.json()["embeddings"][0]

    def cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """
        Computes the cosine similarity between two embedding vectors.

        Returns a float in the range [-1, 1]:
        1.0 - vectors are semantically identical
        0.0 - vectors are unrelated
        -1.0 - vectors are semantically opposite

        General interpretation:
        > 0.9      very similar
        0.7 - 0.9  similar
        0.5 - 0.7  somewhat related
        < 0.5      likely unrelated

        A zero vector has no direction, so its similarity is undefined.
        We return 0.0 (unrelated) instead of raising ZeroDivisionError.
        """
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a ** 2 for a in vec1) ** 0.5
        magnitude2 = sum(b ** 2 for b in vec2) ** 0.5
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)
    
    def semantic_search(self, user_question: str):
        try:
            question_embedding = self.get_embedding(user_question)
        except ConnectionError as error:
            logger.error("Semantic search skipped: %s", error)
            return []

        try:
            with open(EMBEDDINGS_FILE, 'r', encoding="utf-8") as f:
                emb_json = json.load(f)
        except FileNotFoundError:
            logger.error(
                "Semantic search skipped: '%s' does not exist. "
                "Restart the application to generate it.", EMBEDDINGS_FILE
            )
            return []
        except json.JSONDecodeError:
            logger.error(
                "Semantic search skipped: '%s' is corrupted. Delete it and "
                "restart the application to regenerate it.", EMBEDDINGS_FILE
            )
            return []

        results_with_similarity = []
        for item in emb_json:
            similarity = self.cosine_similarity(question_embedding, item["embedding"])
            results_with_similarity.append({
                "document_id": item["document_id"],
                "chunk_index": item["chunk_index"],
                "similarity": similarity,
                "content": item["content"]
            })
        sorted_list = sorted(
            results_with_similarity,
            key=lambda r: r["similarity"],
            reverse=True
        )
        final_list = [item for item in sorted_list if item["similarity"] > SIMILARITY_THRESHOLD]
        logger.debug(
            "Found %d relevant chunks for: '%s'", len(final_list), user_question
        )

        return final_list[:TOP_N]
