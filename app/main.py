from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router as v1_router


app = FastAPI(
    title="LazyCook Recommendation API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "null",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/v1")

frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
if frontend_dir.exists():
    app.mount("/demo", StaticFiles(directory=frontend_dir, html=True), name="demo")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "LazyCook Recommendation API",
        "docs": "/docs",
        "demo": "/demo",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
