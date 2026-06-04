from pydantic import BaseModel, Field


class Recipe(BaseModel):
    id: str
    name: str
    ingredients: list[str] = Field(default_factory=list)
    cook_time: int | None = None
    tags: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
