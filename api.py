from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from recommend import recommend

# api.py 顶部添加
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LazyCook Toy API", version="0.1.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段先放开，生产再收紧
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecRequest(BaseModel):
    fridge: List[str]
    k: int = Field(5, ge=1, le=20)
    time_limit: Optional[int] = Field(None, ge=1, le=120)
    must_tags: Optional[List[str]] = None
    ban_tags: Optional[List[str]] = None
    only_few_ings: bool = Field(False, description="只推荐 ≤3 种食材的菜谱")

@app.get("/")
def root():
    return {"message": "LazyCook API running. See /docs"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/v1/recommend")
def recommend_api(req: RecRequest):
    items = recommend(
        fridge_items=req.fridge,
        k=req.k,
        time_limit=req.time_limit,
        must_tags=req.must_tags,
        ban_tags=req.ban_tags,
        only_few_ings=req.only_few_ings,  # 新增传参
    )
    return {"items": items}


