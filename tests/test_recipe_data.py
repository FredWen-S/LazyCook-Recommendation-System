from pathlib import Path

from scripts.validate_recipes import validate_recipes_file


def test_recipe_data_passes_quality_checks() -> None:
    errors = validate_recipes_file(Path("data/recipes.json"))

    assert errors == []
