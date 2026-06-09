import pytest

from app.models.recipe import Recipe
from app.schemas.recommendation import RecommendRequest
from app.services.recommendation_service import (
    INGREDIENT_COVERAGE_WEIGHT,
    SIMILARITY_SCORE_WEIGHT,
    TIME_SCORE_WEIGHT,
    RecommendationService,
    combined_score,
    ingredient_coverage,
    missing_items,
    normalize_ingredients,
)


class FakeRepository:
    def __init__(self, recipes: list[Recipe], aliases: dict[str, str] | None = None) -> None:
        self.recipes = recipes
        self.aliases = aliases or {}

    def list_recipes(self) -> list[Recipe]:
        return self.recipes

    def load_aliases(self) -> dict[str, str]:
        return self.aliases


class CountingEmbedder:
    name = "counting"
    model_name = "counting-test"

    def __init__(self) -> None:
        self.ingredients_calls: list[tuple[str, ...]] = []

    def embed_ingredients(self, ingredients: list[str]) -> list[float]:
        self.ingredients_calls.append(tuple(ingredients))
        return [1.0, 0.0] if "番茄" in ingredients else [0.0, 1.0]


def test_aliases_normalize_ingredients() -> None:
    aliases = {"西红柿": "番茄", "蛋": "鸡蛋"}

    assert normalize_ingredients([" 西红柿 ", "蛋", "番茄"], aliases) == ["番茄", "鸡蛋"]


def test_request_rejects_blank_ingredients_and_deduplicates() -> None:
    request = RecommendRequest(fridge=["番茄", " 番茄 ", "鸡蛋"])
    assert request.fridge == ["番茄", "鸡蛋"]

    with pytest.raises(ValueError):
        RecommendRequest(fridge=["番茄", " "])


def test_time_limit_filters_recipes() -> None:
    service = RecommendationService(
        repository=FakeRepository(
            [
                Recipe(id="fast", name="快菜", ingredients=["番茄"], cook_time=5),
                Recipe(id="slow", name="慢菜", ingredients=["番茄"], cook_time=30),
            ]
        )
    )

    response = service.recommend(RecommendRequest(fridge=["番茄"], k=10, time_limit=10))

    assert [item.id for item in response.recommendations] == ["fast"]
    assert response.meta["candidate_count"] == 1


def test_missing_ingredients_are_calculated() -> None:
    assert missing_items({"番茄", "鸡蛋"}, ["番茄", "鸡蛋", "盐"]) == ["盐"]

    service = RecommendationService(
        repository=FakeRepository(
            [Recipe(id="soup", name="番茄蛋汤", ingredients=["番茄", "鸡蛋", "盐"], cook_time=8)]
        )
    )

    response = service.recommend(RecommendRequest(fridge=["番茄", "鸡蛋"], k=1))

    assert response.recommendations[0].missing_ingredients == ["盐"]


def test_ingredient_coverage_calculation() -> None:
    assert ingredient_coverage({"番茄", "鸡蛋"}, ["番茄", "鸡蛋", "盐"]) == pytest.approx(2 / 3)
    assert ingredient_coverage({"番茄"}, []) == 0.0


def test_recommendation_sorting_is_stable_for_equal_scores() -> None:
    service = RecommendationService(
        repository=FakeRepository(
            [
                Recipe(id="first", name="第一道", ingredients=["番茄"], cook_time=5),
                Recipe(id="second", name="第二道", ingredients=["番茄"], cook_time=5),
            ]
        )
    )

    response = service.recommend(RecommendRequest(fridge=["番茄"], k=2))

    assert [item.id for item in response.recommendations] == ["first", "second"]


def test_debug_scoring_fields_are_exposed() -> None:
    service = RecommendationService(
        repository=FakeRepository(
            [Recipe(id="dish", name="菜", ingredients=["番茄"], cook_time=5)]
        )
    )

    response = service.recommend(RecommendRequest(fridge=["番茄"], k=1, time_limit=10))
    item = response.recommendations[0]

    assert item.score >= 0
    assert item.similarity_score >= 0
    assert item.ingredient_coverage == 1.0
    assert item.time_score == 0.9
    assert response.meta["score_weights"] == {
        "ingredient_coverage": INGREDIENT_COVERAGE_WEIGHT,
        "similarity_score": SIMILARITY_SCORE_WEIGHT,
        "time_score": TIME_SCORE_WEIGHT,
    }


def test_time_score_contributes_to_combined_score() -> None:
    assert combined_score(
        semantic_score=0.5,
        coverage_score=0.5,
        time_score=1.0,
    ) == 0.55

    assert combined_score(
        semantic_score=0.5,
        coverage_score=0.5,
        time_score=0.0,
    ) == 0.45


def test_reason_is_user_facing_and_mentions_key_factors() -> None:
    service = RecommendationService(
        repository=FakeRepository(
            [Recipe(id="soup", name="番茄蛋汤", ingredients=["番茄", "鸡蛋", "盐"], cook_time=8)]
        )
    )

    item = service.recommend(RecommendRequest(fridge=["番茄", "鸡蛋"], k=1)).recommendations[0]

    assert item.reason is not None
    assert "已匹配：番茄、鸡蛋" in item.reason
    assert "缺少：盐" in item.reason
    assert "预计 8 分钟" in item.reason


def test_recipe_embeddings_are_cached_between_requests() -> None:
    embedder = CountingEmbedder()
    service = RecommendationService(
        repository=FakeRepository(
            [Recipe(id="dish", name="菜", ingredients=["番茄"], cook_time=5)]
        ),
        embedder=embedder,
    )

    service.recommend(RecommendRequest(fridge=["番茄"], k=1))
    service.recommend(RecommendRequest(fridge=["番茄"], k=1))

    assert embedder.ingredients_calls == [
        ("番茄",),
        ("番茄",),
        ("番茄",),
    ]


def test_preferences_avoid_filters_name_tags_and_ingredients() -> None:
    service = RecommendationService(
        repository=FakeRepository(
            [
                Recipe(id="soup", name="番茄蛋汤", ingredients=["番茄", "鸡蛋"], cook_time=6, tags=["汤"]),
                Recipe(id="fry", name="番茄炒蛋", ingredients=["番茄", "鸡蛋"], cook_time=8, tags=["炒"]),
            ]
        )
    )

    response = service.recommend(
        RecommendRequest(fridge=["番茄", "鸡蛋"], preferences={"avoid": ["汤"]})
    )

    assert [item.id for item in response.recommendations] == ["fry"]
    assert response.meta["preference_rules"]["enabled"] is True


def test_preferences_max_missing_filters_recipes() -> None:
    service = RecommendationService(
        repository=FakeRepository(
            [
                Recipe(id="exact", name="番茄蛋汤", ingredients=["番茄", "鸡蛋"], cook_time=6),
                Recipe(id="needs-more", name="番茄炒蛋", ingredients=["番茄", "鸡蛋", "葱"], cook_time=8),
            ]
        )
    )

    response = service.recommend(
        RecommendRequest(fridge=["番茄", "鸡蛋"], preferences={"max_missing": 0})
    )

    assert [item.id for item in response.recommendations] == ["exact"]


def test_preferences_tags_add_small_boost() -> None:
    service = RecommendationService(
        repository=FakeRepository(
            [
                Recipe(id="plain", name="普通菜", ingredients=["番茄", "盐", "葱"], cook_time=5, tags=["家常"]),
                Recipe(id="preferred", name="偏好菜", ingredients=["番茄", "盐", "葱"], cook_time=5, tags=["素菜"]),
            ]
        )
    )

    response = service.recommend(
        RecommendRequest(fridge=["番茄", "盐"], preferences={"diet": ["素菜"]})
    )

    assert response.recommendations[0].id == "preferred"
