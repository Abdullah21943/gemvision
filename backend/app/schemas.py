from pydantic import BaseModel, ConfigDict, Field


class GemPrediction(BaseModel):
    label: str
    confidence: float


class PredictResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    top_prediction: GemPrediction
    top_k: list[GemPrediction]
    model_loaded: bool


class PriceRequest(BaseModel):
    gem_type: str = Field(..., description="Gemstone type, e.g. 'Ruby'")
    carat: float = Field(..., gt=0, le=50)
    cut: str = Field(..., description="Cut quality, e.g. 'Ideal', 'Good', 'Fair'")
    clarity: str = Field(..., description="Clarity grade, e.g. 'IF', 'VVS1', 'SI2'")
    color: str | None = Field(None, description="Color grade, e.g. 'D'..'J'")


class PriceResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    estimated_price: float
    price_range_low: float
    price_range_high: float
    currency: str = "USD"
    model_loaded: bool
