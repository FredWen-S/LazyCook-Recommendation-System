import pytest
import builtins

from app.nlp import providers
from app.nlp.providers import (
    DEFAULT_EMBEDDING_PROVIDER,
    EMBEDDING_MODEL_ENV,
    EMBEDDING_PROVIDER_ENV,
    HashingEmbeddingProvider,
    create_embedding_provider,
)


def test_default_embedding_provider_is_hashing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(EMBEDDING_PROVIDER_ENV, raising=False)

    provider = create_embedding_provider()

    assert isinstance(provider, HashingEmbeddingProvider)
    assert provider.name == DEFAULT_EMBEDDING_PROVIDER
    assert provider.embed_ingredients(["番茄", "鸡蛋"]) == provider.embed_ingredients(["番茄", "鸡蛋"])


def test_embedding_provider_can_be_selected_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(EMBEDDING_PROVIDER_ENV, "hashing")

    provider = create_embedding_provider()

    assert isinstance(provider, HashingEmbeddingProvider)


def test_unknown_embedding_provider_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported embedding provider"):
        create_embedding_provider("unknown")


def test_sentence_transformer_missing_dependency_has_clear_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "sentence_transformers":
            raise ImportError("missing optional dependency")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError, match="pip install -r requirements-ml.txt"):
        create_embedding_provider("sentence-transformers")


def test_sentence_transformer_model_name_comes_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSentenceTransformerProvider:
        name = "sentence-transformers"

        def __init__(self, model_name: str | None = None) -> None:
            self.model_name = model_name or "default-model"

        def embed_ingredients(self, ingredients: list[str]) -> list[float]:
            return [1.0]

    monkeypatch.setenv(EMBEDDING_PROVIDER_ENV, "sentence-transformers")
    monkeypatch.setenv(EMBEDDING_MODEL_ENV, "local-test-model")
    monkeypatch.setattr(providers, "SentenceTransformerProvider", FakeSentenceTransformerProvider)

    provider = providers.create_embedding_provider()

    assert provider.name == "sentence-transformers"
    assert provider.model_name == "local-test-model"
