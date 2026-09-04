from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BACKEND_DIR / "models"


class Settings(BaseSettings):
    app_name: str = "GemVision API"
    cors_origins: list[str] = ["*"]

    cnn_model_path: Path = MODELS_DIR / "gemstone_cnn.keras"
    class_indices_path: Path = MODELS_DIR / "class_indices.json"
    cnn_image_size: int = 224

    price_model_path: Path = MODELS_DIR / "price_model.joblib"
    price_encoders_path: Path = MODELS_DIR / "price_encoders.joblib"

    top_k_predictions: int = 3

    model_config = SettingsConfigDict(env_prefix="GEMVISION_")


settings = Settings()
