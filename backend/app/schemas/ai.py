from pydantic import BaseModel, Field


class ROIRequest(BaseModel):
    property_price: float = Field(gt=0)
    rental_yield: float = Field(ge=0, le=30)
    demand_index: float = Field(ge=0, le=1)
    market_trend: float = Field(ge=0, le=1)


class ROIResponse(BaseModel):
    predicted_roi_percent: float
    confidence_interval: list[float]


class RiskRequest(ROIRequest):
    pass


class RiskResponse(BaseModel):
    risk_level: str
    probability_score: float
