import json
from pathlib import Path

import pytest

from app.repositories.recipe_repository import RecipeRepository
from app.schemas.recommendation import RecommendRequest
from app.services.recommendation_service import RecommendationService


EVAL_CASES_PATH = Path("data/eval_cases.json")


def load_eval_cases() -> list[dict[str, object]]:
    with EVAL_CASES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture(scope="module")
def recipe_tags_by_name() -> dict[str, set[str]]:
    recipes = RecipeRepository().list_recipes()
    return {recipe.name: set(recipe.tags) for recipe in recipes}


@pytest.mark.parametrize("case", load_eval_cases())
def test_recommendation_eval_cases(case: dict[str, object], recipe_tags_by_name: dict[str, set[str]]) -> None:
    service = RecommendationService()
    request = RecommendRequest(
        fridge=case["ingredients"],
        k=5,
        time_limit=case.get("time_limit"),
    )

    response = service.recommend(request)
    names = [item.name for item in response.recommendations]
    top_three = names[:3]

    assert any(name in names for name in case["expected_contains"])
    assert not any(name in top_three for name in case["expected_not_contains"])

    returned_tags = set()
    for name in top_three:
        returned_tags.update(recipe_tags_by_name[name])

    assert any(tag in returned_tags for tag in case["expected_tags"])
