import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.repositories.recipe_repository import RecipeRepository
from app.schemas.recommendation import RecommendRequest
from app.services.recommendation_service import RecommendationService


DEFAULT_EVAL_CASES_PATH = PROJECT_ROOT / "data" / "eval_cases.json"


@dataclass
class CaseResult:
    index: int
    label: str
    difficulty: str
    is_hard_negative: bool
    hit_at_3: bool
    bad_at_3: bool
    hard_negative_at_3: bool
    tag_match: bool
    top_names: list[str]
    matched_expected: list[str]
    bad_matches: list[str]
    matched_tags: list[str]


def load_eval_cases(path: Path = DEFAULT_EVAL_CASES_PATH) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        value = json.load(file)

    if not isinstance(value, list):
        raise ValueError(f"{path} must contain a JSON array")
    return value


def evaluate_cases(cases: list[dict[str, Any]]) -> tuple[list[CaseResult], dict[str, float]]:
    service = RecommendationService()
    recipe_tags_by_name = {
        recipe.name: set(recipe.tags) for recipe in RecipeRepository().list_recipes()
    }

    results: list[CaseResult] = []
    for index, case in enumerate(cases, start=1):
        request = RecommendRequest(
            fridge=case["ingredients"],
            k=5,
            time_limit=case.get("time_limit"),
            preferences=case.get("preferences"),
        )
        response = service.recommend(request)
        top_names = [item.name for item in response.recommendations[:3]]

        expected_contains = set(case["expected_contains"])
        expected_not_contains = set(case["expected_not_contains"])
        expected_tags = set(case["expected_tags"])
        returned_tags = set()
        for name in top_names:
            returned_tags.update(recipe_tags_by_name.get(name, set()))

        matched_expected = sorted(expected_contains.intersection(top_names))
        bad_matches = sorted(expected_not_contains.intersection(top_names))
        matched_tags = sorted(expected_tags.intersection(returned_tags))
        is_hard_negative = bool(case.get("hard_negative", False))

        results.append(
            CaseResult(
                index=index,
                label=str(case.get("label", f"case {index}")),
                difficulty=str(case.get("difficulty", "basic")),
                is_hard_negative=is_hard_negative,
                hit_at_3=bool(matched_expected),
                bad_at_3=bool(bad_matches),
                hard_negative_at_3=is_hard_negative and bool(bad_matches),
                tag_match=bool(matched_tags),
                top_names=top_names,
                matched_expected=matched_expected,
                bad_matches=bad_matches,
                matched_tags=matched_tags,
            )
        )

    metrics = summarize_results(results)
    return results, metrics


def summarize_results(results: list[CaseResult]) -> dict[str, float]:
    if not results:
        return {
            "hit_at_3": 0.0,
            "bad_at_3": 0.0,
            "hard_negative_at_3": 0.0,
            "tag_match": 0.0,
            "non_basic_ratio": 0.0,
        }

    total = len(results)
    hard_negative_results = [result for result in results if result.is_hard_negative]
    return {
        "hit_at_3": sum(result.hit_at_3 for result in results) / total,
        "bad_at_3": sum(result.bad_at_3 for result in results) / total,
        "hard_negative_at_3": (
            sum(result.hard_negative_at_3 for result in hard_negative_results)
            / len(hard_negative_results)
            if hard_negative_results
            else 0.0
        ),
        "tag_match": sum(result.tag_match for result in results) / total,
        "non_basic_ratio": sum(result.difficulty != "basic" for result in results) / total,
    }


def main() -> int:
    cases = load_eval_cases()
    results, metrics = evaluate_cases(cases)

    print("LazyCook recommendation evaluation")
    for result in results:
        print(
            f"case {result.index:02d}: "
            f"[{result.difficulty}] {result.label} "
            f"Hit@3={'yes' if result.hit_at_3 else 'no'} "
            f"Bad@3={'yes' if result.bad_at_3 else 'no'} "
            f"HardNeg@3={'yes' if result.hard_negative_at_3 else 'no'} "
            f"Tag match={'yes' if result.tag_match else 'no'} "
            f"top3={result.top_names} "
            f"expected={result.matched_expected or '-'} "
            f"bad={result.bad_matches or '-'} "
            f"tags={result.matched_tags or '-'}"
        )

    failures = [
        result
        for result in results
        if not result.hit_at_3 or result.bad_at_3 or not result.tag_match
    ]
    print("Failure cases:")
    if failures:
        for result in failures:
            print(
                f"- case {result.index:02d} [{result.difficulty}] {result.label}: "
                f"Hit@3={result.hit_at_3} Bad@3={result.bad_at_3} "
                f"Tag match={result.tag_match} top3={result.top_names}"
            )
    else:
        print("- none")

    print("Overall metrics:")
    print(f"- Hit@3: {metrics['hit_at_3']:.3f}")
    print(f"- Bad@3: {metrics['bad_at_3']:.3f}")
    print(f"- Hard negative Bad@3: {metrics['hard_negative_at_3']:.3f}")
    print(f"- Tag match: {metrics['tag_match']:.3f}")
    print(f"- Non-basic case ratio: {metrics['non_basic_ratio']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
