"""Request/response models for the two ML endpoints.

These are the API contract the Flutter app codes against directly
(mobile/lib/models/gem_prediction.dart mirrors GemPrediction/PredictResponse/
PriceResponse; PriceRequest is mirrored by the price form's request body) --
changing a field name here means updating the Dart side too.
"""

from pydantic import BaseModel, ConfigDict, Field


class GemPrediction(BaseModel):
    """A single gemstone-type guess: one of the CNN's softmax outputs."""

    label: str
    confidence: float


class PredictResponse(BaseModel):
    # `model_loaded` starting with "model_" collides with Pydantic v2's own
    # reserved "model_" namespace; this opts the class out of that check
    # rather than renaming the clearest field name available.
    model_config = ConfigDict(protected_namespaces=())

    top_prediction: GemPrediction
    top_k: list[GemPrediction]
    model_loaded: bool


class PriceRequest(BaseModel):
    """Inputs to the price model. Note gem_type/carat/cut/clarity/color are
    all user-supplied (possibly pre-filled from a PredictResponse's
    top_prediction) -- the CNN does not itself estimate carat/cut/clarity;
    see docs discussion on the classification->price pipeline."""

    gem_type: str = Field(..., description="Gemstone type, e.g. 'Ruby'")
    carat: float = Field(..., gt=0, le=50)
    cut: str = Field(..., description="Cut quality, e.g. 'Ideal', 'Good', 'Fair'")
    clarity: str = Field(..., description="Clarity grade, e.g. 'IF', 'VVS1', 'SI2'")
    color: str | None = Field(None, description="Color grade, e.g. 'D'..'J'")


class PriceResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    estimated_price: float
    # +/-15% band around the point estimate, computed in routers/price.py --
    # a single number reads as false precision for a regression model.
    price_range_low: float
    price_range_high: float
    currency: str = "USD"
    model_loaded: bool
