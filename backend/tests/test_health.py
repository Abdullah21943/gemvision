import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "cnn_model_loaded" in body
    assert "price_model_loaded" in body


def test_predict_with_invalid_bytes_returns_500() -> None:
    # Not a decodable image -> PIL raises inside GemstoneCNN.predict(),
    # which the router turns into a 500 rather than propagating the
    # exception, regardless of whether a model is loaded.
    files = {"file": ("test.png", b"not-a-real-image", "image/png")}
    response = client.post("/predict", files=files)
    assert response.status_code == 500


def test_predict_with_real_image_returns_prediction() -> None:
    buf = io.BytesIO()
    Image.new("RGB", (224, 224), color=(180, 30, 30)).save(buf, format="JPEG")
    files = {"file": ("gem.jpg", buf.getvalue(), "image/jpeg")}

    response = client.post("/predict", files=files)
    assert response.status_code == 200
    body = response.json()
    assert body["model_loaded"] is True
    assert 0.0 <= body["top_prediction"]["confidence"] <= 1.0
    assert len(body["top_k"]) == 3


def test_price_with_valid_payload_returns_estimate() -> None:
    payload = {"gem_type": "Ruby", "carat": 1.0, "cut": "Ideal", "clarity": "VS1", "color": "E"}
    response = client.post("/price", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["model_loaded"] is True
    assert body["estimated_price"] > 0
    assert body["price_range_low"] <= body["estimated_price"] <= body["price_range_high"]
