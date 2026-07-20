"""
Unit tests for EmbeddingsClient.cosine_similarity().

Only the pure computation is tested here. No network calls are made:
Ollama and Azure are external services and are out of scope for unit tests.
"""

import pytest

from embeddings_client import EmbeddingsClient


client = EmbeddingsClient()


def test_identical_vectors():
    """Identical vectors point the same way -> similarity 1.0."""
    assert client.cosine_similarity([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)


def test_opposite_vectors():
    """Opposite vectors point the other way -> similarity -1.0."""
    assert client.cosine_similarity([1, 2, 3], [-1, -2, -3]) == pytest.approx(-1.0)


def test_orthogonal_vectors():
    """Perpendicular vectors share no direction -> similarity 0.0."""
    assert client.cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)


def test_different_vectors():
    """Different but related vectors land strictly between 0 and 1."""
    similarity = client.cosine_similarity([1, 2, 3], [4, 5, 6])
    assert similarity == pytest.approx(0.9746318, abs=1e-6)
    assert 0 < similarity < 1


def test_zero_first_vector():
    """Covers the `magnitude1 == 0` branch."""
    assert client.cosine_similarity([0, 0, 0], [1, 2, 3]) == 0.0


def test_zero_second_vector():
    """Covers the `magnitude2 == 0` branch."""
    assert client.cosine_similarity([1, 2, 3], [0, 0, 0]) == 0.0
