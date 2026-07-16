import requests
import json

from config import EMBEDDINGS_MODEL, EMBEDDINGS_ENDPOINT, API_KEY, SIMILARITY_THRESHOLD, TOP_N


class EmbeddingsClient:
    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if "azure.com" in EMBEDDINGS_ENDPOINT:
            headers["api-key"] = API_KEY
        else:
            headers["Authorization"] = f"Bearer {API_KEY}"
        return headers
    def get_embedding(self, text: str) -> list[float]:
        response = requests.post(
            EMBEDDINGS_ENDPOINT,
            json={
                "model": EMBEDDINGS_MODEL,
                "input": text
            },
            headers=self._headers()
        )

        if not response.ok:
            print("STATUS:", response.status_code)
            print("BODY:", response.text)

        response.raise_for_status()
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

        """
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a ** 2 for a in vec1) ** 0.5
        magnitude2 = sum(b ** 2 for b in vec2) ** 0.5
        return dot_product / (magnitude1 * magnitude2)
    
    def semantic_search(self, user_question: str):
        question_embedding = self.get_embedding(user_question)
        with open("embeddings.json", 'r', encoding="utf-8") as f:
            emb_json = json.load(f)
        
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
        print(f"Found {len(final_list)} relevant chunks for the question: '{user_question}'")

        return final_list[:TOP_N]
