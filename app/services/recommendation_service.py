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
            time_fit_score = time_score(recipe.cook_time, request.time_limit)
            matched_ingredients = matched_items(fridge_set, recipe_ingredients)
            missing_ingredients = missing_items(fridge_set, recipe_ingredients)

            score = combined_score(
                semantic_score=semantic_score,
                coverage_score=coverage_score,
                time_score=time_fit_score,
            )
            candidates.append(
                ScoredRecipe(
                    recipe=recipe,
                    score=score,
                    semantic_score=semantic_score,
                    coverage_score=coverage_score,
                    time_score=time_fit_score,
                    matched_ingredients=matched_ingredients,
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
        time_score: float,
        matched_ingredients: list[str],
        missing_ingredients: list[str],
    ) -> None:
        self.recipe = recipe
        self.score = score
        self.semantic_score = semantic_score
        self.coverage_score = coverage_score
        self.time_score = time_score
        self.matched_ingredients = matched_ingredients
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


def time_score(cook_time: int | None, time_limit: int | None) -> float:
    if cook_time is None or time_limit is None:
        return 1.0
    if cook_time > time_limit:
        return 0.0
    return round(max(0.0, min(1.0, 1 - (cook_time / time_limit) * 0.2)), 4)


def matched_items(fridge_set: set[str], recipe_ingredients: list[str]) -> list[str]:
    return [ingredient for ingredient in recipe_ingredients if ingredient in fridge_set]


def missing_items(fridge_set: set[str], recipe_ingredients: list[str]) -> list[str]:
    return [ingredient for ingredient in recipe_ingredients if ingredient not in fridge_set]


def combined_score(
    semantic_score: float,
    coverage_score: float,
    time_score: float,
) -> float:
    score = 0.55 * coverage_score + 0.35 * semantic_score + 0.10 * time_score
    return round(max(0.0, min(1.0, score)), 4)


def to_schema(candidate: ScoredRecipe) -> RecipeRecommendation:
    recipe = candidate.recipe
    reason = build_reason(candidate)
    return RecipeRecommendation(
        id=recipe.id,
        name=recipe.name,
        ingredients=recipe.ingredients,
        missing_ingredients=candidate.missing_ingredients,
        cook_time=recipe.cook_time,
        score=candidate.score,
        similarity_score=round(candidate.semantic_score, 4),
        ingredient_coverage=round(candidate.coverage_score, 4),
        time_score=candidate.time_score,
        reason=reason,
    )


def build_reason(candidate: ScoredRecipe) -> str:
    recipe = candidate.recipe
    matched = "、".join(candidate.matched_ingredients[:3]) or "当前食材"
    missing = "、".join(candidate.missing_ingredients[:3]) if candidate.missing_ingredients else "基本不缺"
    cook_time = f"预计 {recipe.cook_time} 分钟" if recipe.cook_time is not None else "用时未知"

    if not candidate.missing_ingredients:
        fit = "食材匹配度很高"
    elif candidate.coverage_score >= 0.5:
        fit = "只需要补少量食材"
    else:
        fit = "和现有食材有一定相似度"

    return f"已匹配 {matched}；缺少 {missing}；{cook_time}。{fit}，适合作为当前推荐。"
