from fastapi import APIRouter

from app.schemas.recommendation import RecommendRequest, RecommendResponse
from app.services.recommendation_service import RecommendationService


router = APIRouter()
recommendation_service = RecommendationService()


@router.post("/recommend", response_model=RecommendResponse)
def recommend(payload: RecommendRequest) -> RecommendResponse:
    return recommendation_service.recommend(payload)
