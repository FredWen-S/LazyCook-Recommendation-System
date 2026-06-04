from fastapi import APIRouter

from app.api.v1.routes.recommend import router as recommend_router


router = APIRouter()
router.include_router(recommend_router, tags=["recommendations"])
