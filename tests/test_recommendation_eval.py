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


def test_eval_cases_have_required_shape() -> None:
    cases = load_eval_cases()

    assert len(cases) >= 15
    for index, case in enumerate(cases, start=1):
        assert isinstance(case.get("ingredients"), list), f"case {index} ingredients must be a list"
        assert case["ingredients"], f"case {index} ingredients cannot be empty"
        assert isinstance(case.get("expected_contains"), list), f"case {index} expected_contains must be a list"
        assert case["expected_contains"], f"case {index} expected_contains cannot be empty"
        assert isinstance(case.get("expected_not_contains"), list), (
            f"case {index} expected_not_contains must be a list"
        )
        assert isinstance(case.get("expected_tags"), list), f"case {index} expected_tags must be a list"
        assert case["expected_tags"], f"case {index} expected_tags cannot be empty"
        if "time_limit" in case:
            assert isinstance(case["time_limit"], int), f"case {index} time_limit must be an integer"
        if "preferences" in case:
            assert isinstance(case["preferences"], dict), f"case {index} preferences must be an object"
        if "hard_negative" in case:
            assert isinstance(case["hard_negative"], bool), f"case {index} hard_negative must be a boolean"


def test_eval_cases_include_realistic_inputs() -> None:
    cases = load_eval_cases()

    assert len(cases) >= 33
    assert any(case.get("difficulty") == "alias" for case in cases)
    assert any(case.get("difficulty") == "fuzzy" for case in cases)
    assert any(case.get("difficulty") == "hard_negative" for case in cases)
    assert any("preferences" in case for case in cases)


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
        preferences=case.get("preferences"),
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


@pytest.mark.parametrize("case", [case for case in load_eval_cases() if case.get("hard_negative")])
def test_hard_negative_eval_cases(case: dict[str, object]) -> None:
    service = RecommendationService()
    request = RecommendRequest(
        fridge=case["ingredients"],
        k=5,
        time_limit=case.get("time_limit"),
        preferences=case.get("preferences"),
    )

    response = service.recommend(request)
    top_three = [item.name for item in response.recommendations[:3]]

    assert not any(name in top_three for name in case["expected_not_contains"])
