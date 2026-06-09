from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RecommendationPreferences(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    avoid: list[str] = Field(
        default_factory=list,
        description="Terms to avoid in recipe names, tags, or ingredients.",
    )
    meal_type: str | None = Field(
        default=None,
        description="Preferred meal type or recipe tag.",
    )
    diet: list[str] = Field(
        default_factory=list,
        description="Preferred diet tags, such as 素菜 or 无火.",
    )
    max_missing: int | None = Field(
        default=None,
        ge=0,
        le=50,
        description="Maximum number of missing ingredients allowed.",
    )

    @field_validator("avoid", "diet")
    @classmethod
    def validate_optional_terms(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in value:
            term = item.strip()
            if not term:
                raise ValueError("preference lists cannot contain blank terms")

            normalized = term.casefold()
            if normalized not in seen:
                cleaned.append(term)
                seen.add(normalized)

        return cleaned


class RecommendRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "fridge": ["番茄", "鸡蛋", "蒜"],
                "k": 3,
                "time_limit": 15,
                "preferences": {"avoid": ["培根"], "diet": ["家常"], "max_missing": 2},
            }
        },
    )

    fridge: list[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Ingredients available in the user's fridge.",
    )
    k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of recipe recommendations to return.",
    )
    time_limit: int | None = Field(
        default=None,
        ge=1,
        le=240,
        description="Maximum acceptable cooking time in minutes.",
    )
    preferences: RecommendationPreferences | None = Field(
        default=None,
        description="Optional rule-based recommendation preferences.",
    )

    @field_validator("fridge")
    @classmethod
    def validate_fridge(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()

        for item in value:
            ingredient = item.strip()

            if not ingredient:
                raise ValueError("fridge cannot contain blank ingredients")

            normalized = ingredient.casefold()
            if normalized not in seen:
                cleaned.append(ingredient)
                seen.add(normalized)

        return cleaned


class RecipeRecommendation(BaseModel):
    id: str = Field(..., description="Recipe identifier.")
    name: str = Field(..., description="Recipe name.")
    ingredients: list[str] = Field(..., description="Ingredients required by the recipe.")
    matched_ingredients: list[str] = Field(
        default_factory=list,
        description="Ingredients from the request that matched this recipe.",
    )
    missing_ingredients: list[str] = Field(
        default_factory=list,
        description="Ingredients missing from the user's fridge.",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Recipe tags.",
    )
    cook_time: int | None = Field(
        default=None,
        ge=1,
        description="Cooking time in minutes.",
    )
    score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Recommendation score normalized to the 0-1 range.",
    )
    similarity_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Debug semantic similarity score normalized to the 0-1 range.",
    )
    ingredient_coverage: float = Field(
        ...,
        ge=0,
        le=1,
        description="Debug ingredient coverage score normalized to the 0-1 range.",
    )
    time_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Debug time fit score normalized to the 0-1 range.",
    )
    reason: str | None = Field(
        default=None,
        description="Human-readable recommendation reason.",
    )


class RecommendResponse(BaseModel):
    query: RecommendRequest
    recommendations: list[RecipeRecommendation]
    meta: dict[str, Any] = Field(
        default_factory=dict,
        description="Recommendation metadata such as algorithm version and latency.",
    )
