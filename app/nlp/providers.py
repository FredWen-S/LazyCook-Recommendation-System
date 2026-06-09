import os
from typing import Protocol

from app.nlp.embedding import HashingTextEmbedder


DEFAULT_EMBEDDING_PROVIDER = "hashing"
DEFAULT_SENTENCE_TRANSFORMER_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_PROVIDER_ENV = "LAZYCOOK_EMBEDDING_PROVIDER"
EMBEDDING_MODEL_ENV = "LAZYCOOK_EMBEDDING_MODEL"


class EmbeddingProvider(Protocol):
    name: str
    model_name: str

    def embed_ingredients(self, ingredients: list[str]) -> list[float]:
        ...


class HashingEmbeddingProvider(HashingTextEmbedder):
    name = "hashing"
    model_name = "hashing-text-128"


class SentenceTransformerProvider:
    name = "sentence-transformers"

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or DEFAULT_SENTENCE_TRANSFORMER_MODEL
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise RuntimeError(
                "sentence-transformers provider requested, but the optional "
                "dependency is not installed. Install it with: "
                "pip install -r requirements-ml.txt"
            ) from error

        self.model = SentenceTransformer(self.model_name)

    def embed_ingredients(self, ingredients: list[str]) -> list[float]:
        text = " ".join(item.strip() for item in ingredients if item.strip())
        embedding = self.model.encode(text, normalize_embeddings=True)
        return [float(value) for value in embedding]


def create_embedding_provider(
    provider_name: str | None = None,
    model_name: str | None = None,
) -> EmbeddingProvider:
    selected_provider = normalize_provider_name(
        provider_name or os.getenv(EMBEDDING_PROVIDER_ENV, DEFAULT_EMBEDDING_PROVIDER)
    )
    selected_model = model_name or os.getenv(EMBEDDING_MODEL_ENV)

    if selected_provider == "hashing":
        return HashingEmbeddingProvider()
    if selected_provider == "sentence-transformers":
        return SentenceTransformerProvider(selected_model)

    raise ValueError(
        f"Unsupported embedding provider {selected_provider!r}. "
        "Use 'hashing' or 'sentence-transformers'."
    )


def normalize_provider_name(value: str) -> str:
    return value.strip().casefold()
