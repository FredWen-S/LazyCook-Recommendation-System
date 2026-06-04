import hashlib
import math
import re
from collections import Counter


class HashingTextEmbedder:
    """Deterministic local text embedder.

    This is a lightweight production-friendly draft: it avoids network calls and
    external model dependencies while keeping the service interface ready for a
    future sentence-transformer or LLM embedding provider.
    """

    def __init__(self, dimensions: int = 128) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def embed_ingredients(self, ingredients: list[str]) -> list[float]:
        return self.embed_text(" ".join(normalize_text(item) for item in ingredients))

    def embed_text(self, text: str) -> list[float]:
        tokens = tokenize(text)
        vector = [0.0] * self.dimensions

        for token, count in Counter(tokens).items():
            index = stable_hash(token) % self.dimensions
            sign = 1.0 if stable_hash(f"{token}:sign") % 2 == 0 else -1.0
            vector[index] += sign * math.log1p(count)

        return l2_normalize(vector)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", value.strip().casefold())


def tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []

    tokens = [normalized]
    tokens.extend(normalized[index : index + 2] for index in range(max(0, len(normalized) - 1)))
    tokens.extend(normalized[index : index + 3] for index in range(max(0, len(normalized) - 2)))
    return tokens


def stable_hash(value: str) -> int:
    digest = hashlib.blake2b(value.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, byteorder="big", signed=False)


def l2_normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]
