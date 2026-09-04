"""Wrapper around the trained XGBoost gemstone price-regression model.

Same lazy/failure-tolerant loading pattern as cnn_model.py — the artifacts
are produced by ml/train_price_model.py and are gitignored.
"""

from __future__ import annotations

import logging

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class PriceModel:
    def __init__(self) -> None:
        self._model = None
        self._encoders: dict | None = None
        self._load_error: str | None = None
        self._load()

    def _load(self) -> None:
        try:
            if not settings.price_model_path.exists() or not settings.price_encoders_path.exists():
                self._load_error = (
                    f"Model artifacts not found at {settings.price_model_path} / "
                    f"{settings.price_encoders_path}. Run ml/train_price_model.py first."
                )
                logger.warning(self._load_error)
                return

            import joblib  # deferred import

            self._model = joblib.load(settings.price_model_path)
            self._encoders = joblib.load(settings.price_encoders_path)

            logger.info("Loaded gemstone price model")
        except Exception as exc:  # noqa: BLE001
            self._load_error = str(exc)
            logger.exception("Failed to load price model")

    @property
    def is_loaded(self) -> bool:
        return self._model is not None and self._encoders is not None

    @property
    def load_error(self) -> str | None:
        return self._load_error

    def _encode(self, column: str, value: str) -> int:
        encoder = self._encoders[column]
        classes = list(encoder.classes_)
        if value not in classes:
            # Unseen category at inference time -> fall back to the most
            # common training category rather than raising a 500.
            logger.warning("Unseen %s value %r, falling back to %r", column, value, classes[0])
            value = classes[0]
        return int(encoder.transform([value])[0])

    def predict(self, gem_type: str, carat: float, cut: str, clarity: str, color: str | None) -> float:
        if not self.is_loaded:
            raise RuntimeError(self._load_error or "Model not loaded")

        color_value = color or self._encoders["color"].classes_[0]

        features = np.array(
            [
                [
                    carat,
                    self._encode("gem_type", gem_type),
                    self._encode("cut", cut),
                    self._encode("clarity", clarity),
                    self._encode("color", color_value),
                ]
            ]
        )
        price = float(self._model.predict(features)[0])
        return max(price, 0.0)


price_model = PriceModel()
