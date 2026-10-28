import hashlib
import math
import time
from typing import List
import httpx
from src.config import GEMINI_API_KEY, GEMINI_EMBED_MODEL


class EmbeddingClient:
    """Handles text embeddings via Gemini Embeddings API with deterministic fallback."""

    def __init__(self, api_key: str = GEMINI_API_KEY, dimension: int = 768):
        self.api_key = api_key
        self.dimension = dimension
        self.model = GEMINI_EMBED_MODEL

    def embed_text(self, text: str) -> List[float]:
        """Generates embedding vector for a single string."""
        vectors = self.embed_batch([text])
        return vectors[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of strings."""
        if not texts:
            return []

        if self.api_key:
            try:
                vectors = []
                for t in texts:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:embedContent?key={self.api_key}"
                    payload = {
                        "model": f"models/{self.model}",
                        "content": {"parts": [{"text": t}]},
                    }
                    resp = httpx.post(url, json=payload, timeout=8.0)
                    if resp.status_code == 200:
                        raw_vec = resp.json()["embedding"]["values"]
                        # Truncate or pad to self.dimension
                        if len(raw_vec) > self.dimension:
                            vec = raw_vec[:self.dimension]
                        else:
                            vec = raw_vec + [0.0] * (self.dimension - len(raw_vec))
                        # L2 normalize
                        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
                        vectors.append([x / norm for x in vec])
                    else:
                        # Fallback for this text
                        vectors.append(self._deterministic_hash_vector(t))
                return vectors
            except Exception:
                # Network or API issue fallback
                return [self._deterministic_hash_vector(t) for t in texts]

        # Offline / no API key fallback
        return [self._deterministic_hash_vector(t) for t in texts]

    def _deterministic_hash_vector(self, text: str) -> List[float]:
        """Fast, robust deterministic pseudo-semantic vector representation

        for offline execution and zero-dependency testing.
        """
        vec = [0.0] * self.dimension
        words = text.lower().split()
        if not words:
            vec[0] = 1.0
            return vec

        for word in words:
            # Hash word and character ngrams
            h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if ((h >> 8) & 1) else -1.0
            weight = math.log(1.0 + len(word))
            vec[idx] += sign * weight

            # Bigrams
            for i in range(len(word) - 1):
                bg = word[i:i+2]
                h_bg = int(hashlib.md5(bg.encode("utf-8")).hexdigest(), 16)
                idx_bg = h_bg % self.dimension
                vec[idx_bg] += 0.5 * (1.0 if ((h_bg >> 4) & 1) else -1.0)

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]
