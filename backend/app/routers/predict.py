from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.models.cnn_model import gemstone_cnn
from app.schemas import GemPrediction, PredictResponse

router = APIRouter(tags=["predict"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/predict", response_model=PredictResponse)
async def predict_gemstone(file: UploadFile = File(...)) -> PredictResponse:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported content type: {file.content_type}")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    if not gemstone_cnn.is_loaded:
        raise HTTPException(
            status_code=503,
            detail=f"Gemstone classification model is not available: {gemstone_cnn.load_error}",
        )

    try:
        results = gemstone_cnn.predict(image_bytes, top_k=settings.top_k_predictions)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc

    top_k = [GemPrediction(label=label, confidence=confidence) for label, confidence in results]
    return PredictResponse(top_prediction=top_k[0], top_k=top_k, model_loaded=True)
