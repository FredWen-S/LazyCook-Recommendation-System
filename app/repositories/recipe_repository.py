import json
from pathlib import Path
from typing import Any

from app.models.recipe import Recipe


class RecipeRepository:
    def __init__(self, data_dir: Path | None = None) -> None:
        project_root = Path(__file__).resolve().parents[2]
        self.data_dir = data_dir or project_root / "data"

    def list_recipes(self) -> list[Recipe]:
        recipes_path = self.data_dir / "recipes.json"
        raw_recipes = self._read_json_list(recipes_path)

        recipes: list[Recipe] = []
        for index, item in enumerate(raw_recipes, start=1):
            recipes.append(
                Recipe(
                    id=str(item.get("id") or index),
                    name=str(item["name"]),
                    ingredients=list(item.get("ingredients", [])),
                    cook_time=item.get("cook_time") or item.get("time"),
                    tags=list(item.get("tags", [])),
                    steps=list(item.get("steps", [])),
                )
            )

        return recipes

    def load_aliases(self) -> dict[str, str]:
        aliases_path = self.data_dir / "aliases.json"
        if not aliases_path.exists():
            return {}

        raw_aliases = self._read_json_dict(aliases_path)
        return {str(key).strip(): str(value).strip() for key, value in raw_aliases.items()}

    @staticmethod
    def _read_json_list(path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8") as file:
            value = json.load(file)

        if not isinstance(value, list):
            raise ValueError(f"{path} must contain a JSON array")

        return value

    @staticmethod
    def _read_json_dict(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as file:
            value = json.load(file)

        if not isinstance(value, dict):
            raise ValueError(f"{path} must contain a JSON object")

        return value
