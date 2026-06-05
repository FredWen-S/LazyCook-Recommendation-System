import pytest

from app.models.recipe import Recipe
from app.schemas.recommendation import RecommendRequest
from app.services.recommendation_service import (
    RecommendationService,
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

    item = service.recommend(RecommendRequest(fridge=["番茄"], k=1, time_limit=10)).recommendations[0]

    assert item.score >= 0
    assert item.similarity_score >= 0
    assert item.ingredient_coverage == 1.0
    assert item.time_score == 0.9
