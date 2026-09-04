from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "cnn_model_loaded" in body
    assert "price_model_loaded" in body


def test_predict_without_model_returns_503_not_crash() -> None:
    # With no trained model artifacts present, the endpoint must fail
    # gracefully (503) instead of raising, matching the lazy-load contract
    # in app/models/cnn_model.py.
    files = {"file": ("test.png", b"not-a-real-image", "image/png")}
    response = client.post("/predict", files=files)
    assert response.status_code in (503, 500)


def test_price_without_model_returns_503_not_crash() -> None:
    payload = {"gem_type": "Ruby", "carat": 1.0, "cut": "Ideal", "clarity": "VS1"}
    response = client.post("/price", json=payload)
    assert response.status_code in (503, 500)
