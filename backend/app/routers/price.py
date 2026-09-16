"""Module 4: price estimation endpoint.

Takes gem_type/carat/cut/clarity/color (user-supplied -- see the note on
PriceRequest in app/schemas.py) and returns an XGBoost price estimate plus
a display range.
"""

from fastapi import APIRouter, HTTPException

from app.models.price_model import price_model
from app.schemas import PriceRequest, PriceResponse

router = APIRouter(tags=["price"])

# Simple symmetric band around the point estimate to present a range in the
# UI, since a single number reads as false precision for a regression model.
PRICE_RANGE_MARGIN = 0.15


@router.post("/price", response_model=PriceResponse)
async def estimate_price(request: PriceRequest) -> PriceResponse:
    if not price_model.is_loaded:
        raise HTTPException(
            status_code=503,
            detail=f"Price estimation model is not available: {price_model.load_error}",
        )

    try:
        estimated_price = price_model.predict(
            gem_type=request.gem_type,
            carat=request.carat,
            cut=request.cut,
            clarity=request.clarity,
            color=request.color,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Price estimation failed: {exc}") from exc

    return PriceResponse(
        estimated_price=round(estimated_price, 2),
        price_range_low=round(estimated_price * (1 - PRICE_RANGE_MARGIN), 2),
        price_range_high=round(estimated_price * (1 + PRICE_RANGE_MARGIN), 2),
        model_loaded=True,
    )
