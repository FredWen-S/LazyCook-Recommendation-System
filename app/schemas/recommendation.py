from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RecommendRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "fridge": ["番茄", "鸡蛋", "蒜"],
                "k": 3,
                "time_limit": 15,
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
    missing_ingredients: list[str] = Field(
        default_factory=list,
        description="Ingredients missing from the user's fridge.",
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
