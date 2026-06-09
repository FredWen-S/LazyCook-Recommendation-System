from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_demo_frontend_is_served() -> None:
    response = client.get("/demo/")

    assert response.status_code == 200
    assert "LazyCook Recommendation Demo" in response.text


def test_cors_preflight_allows_local_demo_origin() -> None:
    response = client.options(
        "/v1/recommend",
        headers={
            "Origin": "http://127.0.0.1:8000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:8000"


def test_recommend_endpoint_returns_200() -> None:
    response = client.post(
        "/v1/recommend",
        json={"fridge": ["番茄", "鸡蛋", "蒜"], "k": 3, "time_limit": 15},
    )

    assert response.status_code == 200
    body = response.json()
    assert "recommendations" in body
    assert len(body["recommendations"]) <= 3
    if body["recommendations"]:
        item = body["recommendations"][0]
        assert {
            "id",
            "name",
            "matched_ingredients",
            "missing_ingredients",
            "cook_time",
            "tags",
            "reason",
            "score",
            "similarity_score",
            "ingredient_coverage",
            "time_score",
        }.issubset(item)

    assert {
        "embedding_provider",
        "score_weights",
        "total_candidates",
    }.issubset(body["meta"])


def test_recommend_endpoint_rejects_missing_fridge() -> None:
    response = client.post("/v1/recommend", json={"k": 3})

    assert response.status_code == 422


def test_recommend_endpoint_rejects_empty_fridge() -> None:
    response = client.post("/v1/recommend", json={"fridge": [], "k": 3})

    assert response.status_code == 422


def test_recommend_endpoint_rejects_blank_ingredient() -> None:
    response = client.post("/v1/recommend", json={"fridge": ["番茄", " "]})

    assert response.status_code == 422


def test_recommend_endpoint_k_boundaries() -> None:
    assert client.post("/v1/recommend", json={"fridge": ["番茄"], "k": 1}).status_code == 200
    assert client.post("/v1/recommend", json={"fridge": ["番茄"], "k": 20}).status_code == 200
    assert client.post("/v1/recommend", json={"fridge": ["番茄"], "k": 0}).status_code == 422
    assert client.post("/v1/recommend", json={"fridge": ["番茄"], "k": 21}).status_code == 422


def test_recommend_endpoint_time_limit_boundaries() -> None:
    assert client.post(
        "/v1/recommend", json={"fridge": ["番茄"], "time_limit": 1}
    ).status_code == 200
    assert client.post(
        "/v1/recommend", json={"fridge": ["番茄"], "time_limit": 240}
    ).status_code == 200
    assert client.post(
        "/v1/recommend", json={"fridge": ["番茄"], "time_limit": 0}
    ).status_code == 422
    assert client.post(
        "/v1/recommend", json={"fridge": ["番茄"], "time_limit": 241}
    ).status_code == 422


def test_recommend_endpoint_accepts_preferences() -> None:
    response = client.post(
        "/v1/recommend",
        json={
            "fridge": ["鸡蛋", "盐"],
            "preferences": {"avoid": ["汤"], "max_missing": 2},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["preference_rules"]["enabled"] is True
    assert all("汤" not in item["name"] for item in body["recommendations"])
