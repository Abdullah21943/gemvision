"""FastAPI application entry point.

Wires up the two ML endpoints (Modules 3 & 4) and exposes /health, which
reports whether each model actually loaded -- both models load lazily and
tolerate missing artifacts (see app/models/*.py), so this is the one place
to check "is the service actually usable right now" rather than just "is
the process running".

Run with: uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.cnn_model import gemstone_cnn
from app.models.price_model import price_model
from app.routers import predict, price

app = FastAPI(title=settings.app_name, version="0.1.0")

# Permissive CORS: this API is only ever called by our own Flutter app
# (Android/iOS/Web builds, various dev hosts), not by third-party browser
# clients, so a public deployment risk from "*" here is low -- but tighten
# this to a specific origin list (settings.cors_origins) before any public
# demo, since it's currently wide open by default.
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
    """Liveness + model-readiness check, used both by our own manual
    verification and by anything monitoring a deployed instance."""
    return {
        "status": "ok",
        "cnn_model_loaded": gemstone_cnn.is_loaded,
        "price_model_loaded": price_model.is_loaded,
    }
