from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.cnn_model import gemstone_cnn
from app.models.price_model import price_model
from app.routers import predict, price

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router)
app.include_router(price.router)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "cnn_model_loaded": gemstone_cnn.is_loaded,
        "price_model_loaded": price_model.is_loaded,
    }
