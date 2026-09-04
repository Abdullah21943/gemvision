"""Wrapper around the trained gemstone-type CNN (EfficientNetB0 / MobileNetV2).

Loading is lazy and failure-tolerant: if the trained artifacts are not present
yet (they are produced by ml/train_cnn.py and are gitignored), the API stays
up and reports model_loaded=False instead of crashing on import/startup.
"""

from __future__ import annotations

import io
import json
import logging

import numpy as np
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)


class GemstoneCNN:
    def __init__(self) -> None:
        self._model = None
        self._class_names: list[str] | None = None
        self._load_error: str | None = None
        self._load()

    def _load(self) -> None:
        try:
            if not settings.cnn_model_path.exists() or not settings.class_indices_path.exists():
                self._load_error = (
                    f"Model artifacts not found at {settings.cnn_model_path} / "
                    f"{settings.class_indices_path}. Run ml/train_cnn.py first."
                )
                logger.warning(self._load_error)
                return

            import tensorflow as tf  # deferred: heavy import

            self._model = tf.keras.models.load_model(settings.cnn_model_path)

            with open(settings.class_indices_path, "r", encoding="utf-8") as f:
                class_indices: dict[str, int] = json.load(f)
            # class_indices maps class_name -> index; invert to index -> name
            self._class_names = [None] * len(class_indices)
            for name, idx in class_indices.items():
                self._class_names[idx] = name

            logger.info("Loaded gemstone CNN with %d classes", len(self._class_names))
        except Exception as exc:  # noqa: BLE001 - swallow, report via is_loaded()
            self._load_error = str(exc)
            logger.exception("Failed to load gemstone CNN")

    @property
    def is_loaded(self) -> bool:
        return self._model is not None and self._class_names is not None

    @property
    def load_error(self) -> str | None:
        return self._load_error

    def _preprocess(self, image_bytes: bytes) -> np.ndarray:
        size = settings.cnn_image_size
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((size, size))
        arr = np.asarray(img, dtype=np.float32)
        arr = arr / 255.0
        return np.expand_dims(arr, axis=0)

    def predict(self, image_bytes: bytes, top_k: int = 3) -> list[tuple[str, float]]:
        if not self.is_loaded:
            raise RuntimeError(self._load_error or "Model not loaded")

        batch = self._preprocess(image_bytes)
        probs = self._model.predict(batch, verbose=0)[0]

        top_k = min(top_k, len(probs))
        top_indices = np.argsort(probs)[::-1][:top_k]
        return [(self._class_names[i], float(probs[i])) for i in top_indices]


gemstone_cnn = GemstoneCNN()
