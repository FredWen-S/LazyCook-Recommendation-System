from app.models.recipe import Recipe
from app.nlp.providers import EmbeddingProvider, create_embedding_provider
from app.nlp.similarity import cosine_similarity, normalize_cosine
from app.repositories.recipe_repository import RecipeRepository
from app.schemas.recommendation import (
    RecommendationPreferences,
    RecipeRecommendation,
    RecommendRequest,
    RecommendResponse,
)


INGREDIENT_COVERAGE_WEIGHT = 0.55
SIMILARITY_SCORE_WEIGHT = 0.35
TIME_SCORE_WEIGHT = 0.10
PREFERENCE_TAG_BOOST = 0.03


class RecommendationService:
    def __init__(
        self,
        repository: RecipeRepository | None = None,
        embedder: EmbeddingProvider | None = None,
    ) -> None:
        self.repository = repository or RecipeRepository()
        self.embedder = embedder or create_embedding_provider()
        self._recipe_embedding_cache: dict[tuple[str, tuple[str, ...]], list[float]] = {}

    def recommend(self, request: RecommendRequest) -> RecommendResponse:
        aliases = self.repository.load_aliases()
        fridge = normalize_ingredients(request.fridge, aliases)
        fridge_set = set(fridge)
        fridge_embedding = self.embedder.embed_ingredients(fridge)
        recipes = self.repository.list_recipes()

        candidates: list[ScoredRecipe] = []
        preference_rules = build_preference_rules(request.preferences, aliases)
        for recipe in recipes:
            if request.time_limit is not None and recipe.cook_time is not None:
                if recipe.cook_time > request.time_limit:
                    continue

            recipe_ingredients = normalize_ingredients(recipe.ingredients, aliases)
            if should_filter_for_preferences(recipe, recipe_ingredients, preference_rules):
                continue

            recipe_embedding = self._embed_recipe(recipe, recipe_ingredients)
            semantic_score = normalize_cosine(cosine_similarity(fridge_embedding, recipe_embedding))
            coverage_score = ingredient_coverage(fridge_set, recipe_ingredients)
            time_fit_score = time_score(recipe.cook_time, request.time_limit)
            matched_ingredients = matched_items(fridge_set, recipe_ingredients)
            missing_ingredients = missing_items(fridge_set, recipe_ingredients)
            if preference_rules.max_missing is not None:
                if len(missing_ingredients) > preference_rules.max_missing:
                    continue

            preference_boost = preference_score_boost(recipe, preference_rules)

            score = combined_score(
                semantic_score=semantic_score,
                coverage_score=coverage_score,
                time_score=time_fit_score,
                preference_boost=preference_boost,
            )
            candidates.append(
                ScoredRecipe(
                    recipe=recipe,
                    score=score,
                    semantic_score=semantic_score,
                    coverage_score=coverage_score,
                    time_score=time_fit_score,
                    preference_boost=preference_boost,
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
                "algorithm": "embedding-cosine-v1",
                "candidate_count": len(candidates),
                "total_candidates": len(recipes),
                "embedding_provider": self.embedder.name,
                "embedding_model": self.embedder.model_name,
                "score_weights": {
                    "ingredient_coverage": INGREDIENT_COVERAGE_WEIGHT,
                    "similarity_score": SIMILARITY_SCORE_WEIGHT,
                    "time_score": TIME_SCORE_WEIGHT,
                },
                "preference_rules": {
                    "enabled": preference_rules.enabled,
                    "avoid_filter": bool(preference_rules.avoid_terms),
                    "max_missing": preference_rules.max_missing,
                    "tag_boost": PREFERENCE_TAG_BOOST,
                },
            },
        )

    def _embed_recipe(self, recipe: Recipe, recipe_ingredients: list[str]) -> list[float]:
        cache_key = (recipe.id, tuple(recipe_ingredients))
        if cache_key not in self._recipe_embedding_cache:
            self._recipe_embedding_cache[cache_key] = self.embedder.embed_ingredients(recipe_ingredients)
        return self._recipe_embedding_cache[cache_key]


class ScoredRecipe:
    def __init__(
        self,
        recipe: Recipe,
        score: float,
        semantic_score: float,
        coverage_score: float,
        time_score: float,
        preference_boost: float,
        matched_ingredients: list[str],
        missing_ingredients: list[str],
    ) -> None:
        self.recipe = recipe
        self.score = score
        self.semantic_score = semantic_score
        self.coverage_score = coverage_score
        self.time_score = time_score
        self.preference_boost = preference_boost
        self.matched_ingredients = matched_ingredients
        self.missing_ingredients = missing_ingredients


class PreferenceRules:
    def __init__(
        self,
        avoid_terms: list[str],
        tag_preferences: list[str],
        max_missing: int | None,
    ) -> None:
        self.avoid_terms = avoid_terms
        self.tag_preferences = tag_preferences
        self.max_missing = max_missing

    @property
    def enabled(self) -> bool:
        return bool(self.avoid_terms or self.tag_preferences or self.max_missing is not None)


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
    preference_boost: float = 0.0,
) -> float:
    score = (
        INGREDIENT_COVERAGE_WEIGHT * coverage_score
        + SIMILARITY_SCORE_WEIGHT * semantic_score
        + TIME_SCORE_WEIGHT * time_score
        + preference_boost
    )
    return round(max(0.0, min(1.0, score)), 4)


def build_preference_rules(
    preferences: RecommendationPreferences | None,
    aliases: dict[str, str],
) -> PreferenceRules:
    if preferences is None:
        return PreferenceRules(avoid_terms=[], tag_preferences=[], max_missing=None)

    avoid_terms = normalize_preference_terms(preferences.avoid, aliases)
    tag_preferences = normalize_preference_terms(preferences.diet, aliases)
    if preferences.meal_type:
        tag_preferences.extend(normalize_preference_terms([preferences.meal_type], aliases))

    return PreferenceRules(
        avoid_terms=deduplicate_terms(avoid_terms),
        tag_preferences=deduplicate_terms(tag_preferences),
        max_missing=preferences.max_missing,
    )


def normalize_preference_terms(items: list[str], aliases: dict[str, str]) -> list[str]:
    normalized: list[str] = []
    for item in items:
        term = item.strip()
        if not term:
            continue
        normalized.append(aliases.get(term, term).casefold())
    return normalized


def deduplicate_terms(items: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped


def should_filter_for_preferences(
    recipe: Recipe,
    recipe_ingredients: list[str],
    preference_rules: PreferenceRules,
) -> bool:
    if not preference_rules.avoid_terms:
        return False

    searchable_terms = [recipe.name, *recipe.tags, *recipe_ingredients]
    searchable_text = " ".join(term.casefold() for term in searchable_terms)
    return any(term in searchable_text for term in preference_rules.avoid_terms)


def preference_score_boost(recipe: Recipe, preference_rules: PreferenceRules) -> float:
    if not preference_rules.tag_preferences:
        return 0.0

    recipe_tags = {tag.casefold() for tag in recipe.tags}
    hits = sum(1 for term in preference_rules.tag_preferences if term in recipe_tags)
    return round(min(0.09, hits * PREFERENCE_TAG_BOOST), 4)


def to_schema(candidate: ScoredRecipe) -> RecipeRecommendation:
    recipe = candidate.recipe
    reason = build_reason(candidate)
    return RecipeRecommendation(
        id=recipe.id,
        name=recipe.name,
        ingredients=recipe.ingredients,
        matched_ingredients=candidate.matched_ingredients,
        missing_ingredients=candidate.missing_ingredients,
        cook_time=recipe.cook_time,
        tags=recipe.tags,
        score=candidate.score,
        similarity_score=round(candidate.semantic_score, 4),
        ingredient_coverage=round(candidate.coverage_score, 4),
        time_score=candidate.time_score,
        reason=reason,
    )


def build_reason(candidate: ScoredRecipe) -> str:
    recipe = candidate.recipe
    matched = format_ingredient_list(candidate.matched_ingredients, fallback="暂无直接匹配")
    missing = format_ingredient_list(candidate.missing_ingredients, fallback="基本不缺")
    cook_time = f"预计 {recipe.cook_time} 分钟" if recipe.cook_time is not None else "预计用时未知"

    if not candidate.missing_ingredients:
        fit = "现有食材基本够用"
    elif candidate.coverage_score >= 0.5:
        fit = "只需要补少量食材"
    else:
        fit = "和现有食材有一定相似度"

    return f"已匹配：{matched}；缺少：{missing}；{cook_time}。{fit}，适合作为当前推荐。"


def format_ingredient_list(items: list[str], fallback: str) -> str:
    if not items:
        return fallback

    visible_items = items[:3]
    suffix = "等" if len(items) > len(visible_items) else ""
    return "、".join(visible_items) + suffix
