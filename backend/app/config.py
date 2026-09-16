"""Central configuration for the GemVision backend.

All paths/settings are defined here (rather than scattered as literals
through the routers/model wrappers) so there's one place to change, e.g.,
where the trained model artifacts live or how many top-k predictions to
return. Any setting can be overridden via an environment variable prefixed
`GEMVISION_` (e.g. `GEMVISION_CORS_ORIGINS`), per `SettingsConfigDict`.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BACKEND_DIR / "models"


class Settings(BaseSettings):
    app_name: str = "GemVision API"
    # Wide open for a prototype talking to Android/iOS/Web from arbitrary
    # dev hosts. Tighten to a specific origin list before any public deploy.
    cors_origins: list[str] = ["*"]

    # Module 3: gemstone-type CNN artifacts (produced by ml/train_cnn.py).
    cnn_model_path: Path = MODELS_DIR / "gemstone_cnn.keras"
    class_indices_path: Path = MODELS_DIR / "class_indices.json"
    cnn_image_size: int = 224

    # Module 4: price regression artifacts (produced by ml/train_price_model.py).
    price_model_path: Path = MODELS_DIR / "price_model.joblib"
    price_encoders_path: Path = MODELS_DIR / "price_encoders.joblib"

    # How many alternative gemstone-type guesses /predict returns alongside
    # the top prediction (shown as "Other possibilities" in the app).
    top_k_predictions: int = 3

    model_config = SettingsConfigDict(env_prefix="GEMVISION_")


settings = Settings()
