import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECIPES_PATH = PROJECT_ROOT / "data" / "recipes.json"


def validate_recipes_file(path: Path = DEFAULT_RECIPES_PATH) -> list[str]:
    errors: list[str] = []

    with path.open("r", encoding="utf-8") as file:
        recipes = json.load(file)

    if not isinstance(recipes, list):
        return [f"{path} must contain a JSON array"]

    seen_ids: set[str] = set()
    seen_names: set[str] = set()

    for index, recipe in enumerate(recipes, start=1):
        location = f"recipe[{index}]"
        if not isinstance(recipe, dict):
            errors.append(f"{location} must be an object")
            continue

        recipe_id = recipe.get("id")
        if recipe_id is not None:
            if not isinstance(recipe_id, str) or not recipe_id.strip():
                errors.append(f"{location}.id must be a non-empty string when present")
            elif recipe_id in seen_ids:
                errors.append(f"{location}.id duplicates {recipe_id!r}")
            else:
                seen_ids.add(recipe_id)

        name = recipe.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append(f"{location}.name must be a non-empty string")
        elif name in seen_names:
            errors.append(f"{location}.name duplicates {name!r}")
        else:
            seen_names.add(name)

        errors.extend(validate_string_list(recipe.get("ingredients"), f"{location}.ingredients"))
        errors.extend(validate_string_list(recipe.get("tags"), f"{location}.tags"))

        cook_time = recipe.get("cook_time", recipe.get("time"))
        if not isinstance(cook_time, int):
            errors.append(f"{location}.cook_time/time must be an integer")
        elif cook_time <= 0 or cook_time > 240:
            errors.append(f"{location}.cook_time/time must be between 1 and 240")

    return errors


def validate_string_list(value: Any, field_name: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, list) or not value:
        return [f"{field_name} must be a non-empty array"]

    seen: set[str] = set()
    for index, item in enumerate(value, start=1):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{field_name}[{index}] must be a non-empty string")
            continue

        normalized = item.strip().casefold()
        if normalized in seen:
            errors.append(f"{field_name}[{index}] duplicates {item!r}")
        seen.add(normalized)

    return errors


def main() -> int:
    errors = validate_recipes_file()
    if errors:
        print("Recipe data validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Recipe data validation passed: {DEFAULT_RECIPES_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
