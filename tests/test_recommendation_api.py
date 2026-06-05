from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


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
        assert "score" in item
        assert "similarity_score" in item
        assert "ingredient_coverage" in item
        assert "time_score" in item
        assert "missing_ingredients" in item


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
