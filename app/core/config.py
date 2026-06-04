from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "LazyCook Recommendation API"
    api_v1_prefix: str = "/v1"


settings = Settings()
