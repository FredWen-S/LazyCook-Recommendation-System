from app.models.recipe import Recipe
from app.nlp.embedding import HashingTextEmbedder
from app.nlp.similarity import cosine_similarity, normalize_cosine
from app.repositories.recipe_repository import RecipeRepository
from app.schemas.recommendation import (
    RecipeRecommendation,
    RecommendRequest,
    RecommendResponse,
)


class RecommendationService:
    def __init__(
        self,
        repository: RecipeRepository | None = None,
        embedder: HashingTextEmbedder | None = None,
    ) -> None:
        self.repository = repository or RecipeRepository()
        self.embedder = embedder or HashingTextEmbedder()

    def recommend(self, request: RecommendRequest) -> RecommendResponse:
        aliases = self.repository.load_aliases()
        fridge = normalize_ingredients(request.fridge, aliases)
        fridge_set = set(fridge)
        fridge_embedding = self.embedder.embed_ingredients(fridge)

        candidates: list[ScoredRecipe] = []
        for recipe in self.repository.list_recipes():
            if request.time_limit is not None and recipe.cook_time is not None:
                if recipe.cook_time > request.time_limit:
                    continue

            recipe_ingredients = normalize_ingredients(recipe.ingredients, aliases)
            recipe_embedding = self.embedder.embed_ingredients(recipe_ingredients)
            semantic_score = normalize_cosine(cosine_similarity(fridge_embedding, recipe_embedding))
            coverage_score = ingredient_coverage(fridge_set, recipe_ingredients)
            missing_ingredients = missing_items(fridge_set, recipe_ingredients)

            score = combined_score(
                semantic_score=semantic_score,
                coverage_score=coverage_score,
                missing_count=len(missing_ingredients),
            )
            candidates.append(
                ScoredRecipe(
                    recipe=recipe,
                    score=score,
                    semantic_score=semantic_score,
                    coverage_score=coverage_score,
                    missing_ingredients=missing_ingredients,
                )
            )

        candidates.sort(
            key=lambda item: (
                item.score,
                item.coverage_score,
                -(item.recipe.cook_time or 10_000),
            ),
            reverse=True,
        )

        recommendations = [to_schema(candidate) for candidate in candidates[: request.k]]
        return RecommendResponse(
            query=request,
            recommendations=recommendations,
            meta={
                "algorithm": "hashing-embedding-cosine-v1",
                "candidate_count": len(candidates),
            },
        )


class ScoredRecipe:
    def __init__(
        self,
        recipe: Recipe,
        score: float,
        semantic_score: float,
        coverage_score: float,
        missing_ingredients: list[str],
    ) -> None:
        self.recipe = recipe
        self.score = score
        self.semantic_score = semantic_score
        self.coverage_score = coverage_score
        self.missing_ingredients = missing_ingredients


def normalize_ingredients(items: list[str], aliases: dict[str, str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()

    for item in items:
        ingredient = item.strip()
        if not ingredient:
            continue

        ingredient = aliases.get(ingredient, ingredient)
        key = ingredient.casefold()
        if key not in seen:
            normalized.append(ingredient)
            seen.add(key)

    return normalized


def ingredient_coverage(fridge_set: set[str], recipe_ingredients: list[str]) -> float:
    if not recipe_ingredients:
        return 0.0

    hits = sum(1 for ingredient in recipe_ingredients if ingredient in fridge_set)
    return hits / len(recipe_ingredients)


def missing_items(fridge_set: set[str], recipe_ingredients: list[str]) -> list[str]:
    return [ingredient for ingredient in recipe_ingredients if ingredient not in fridge_set]


def combined_score(
    semantic_score: float,
    coverage_score: float,
    missing_count: int,
) -> float:
    penalty = min(0.25, missing_count * 0.03)
    score = 0.55 * coverage_score + 0.45 * semantic_score - penalty
    return round(max(0.0, min(1.0, score)), 4)


def to_schema(candidate: ScoredRecipe) -> RecipeRecommendation:
    recipe = candidate.recipe
    reason = (
        f"coverage={candidate.coverage_score:.2f}, "
        f"semantic_similarity={candidate.semantic_score:.2f}, "
        f"missing={len(candidate.missing_ingredients)}"
    )
    return RecipeRecommendation(
        id=recipe.id,
        name=recipe.name,
        ingredients=recipe.ingredients,
        missing_ingredients=candidate.missing_ingredients,
        cook_time=recipe.cook_time,
        score=candidate.score,
        reason=reason,
    )
