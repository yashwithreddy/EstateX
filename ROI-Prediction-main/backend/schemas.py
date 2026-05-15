"""
schemas.py
----------
Pydantic models for the FastAPI request / response payloads.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ── Request ───────────────────────────────────────────────────────────────────

class PropertyInput(BaseModel):
    location:      str   = Field(..., example="Banjara Hills, Hyderabad")
    property_type: str   = Field(..., example="apartment")
    bhk:           int   = Field(..., ge=0, le=10, example=3)
    area:          float = Field(..., gt=0, example=1500.0)
    price:         float = Field(..., gt=0, example=8500000.0)
    rent:          float = Field(..., ge=0, example=25000.0)
    property_age:  float = Field(5.0,  ge=0,  example=5.0)
    floor:         int   = Field(1,    ge=0,  example=3)
    furnishing:    str   = Field("semi-furnished",
                                  example="semi-furnished")

    # Optional — computed if not supplied
    price_per_sqft: Optional[float] = Field(None, example=5667.0)
    rent_per_sqft:  Optional[float] = Field(None, example=16.67)

    class Config:
        json_schema_extra = {
            "example": {
                "location":      "Banjara Hills, Hyderabad",
                "property_type": "apartment",
                "bhk":           3,
                "area":          1500,
                "price":         8500000,
                "rent":          25000,
                "property_age":  5,
                "floor":         3,
                "furnishing":    "semi-furnished",
            }
        }


# ── Sub-models ────────────────────────────────────────────────────────────────

class InputSummary(BaseModel):
    purchase_price:   float
    monthly_rent:     float
    market_adj_price: float
    market_adj_rent:  float
    location:         Optional[str]
    property_type:    Optional[str]
    bhk:              Optional[int]
    area_sqft:        Optional[float]


class MLEstimates(BaseModel):
    predicted_price: float
    predicted_rent:  float


class FiveYearSummary(BaseModel):
    future_property_price: float
    total_rent_earned:     float
    roi_pct:               float
    investment_rating:     str
    price_growth_rate_pct: float   # location/feature-specific price growth %/yr
    rent_growth_rate_pct:  float   # location/feature-specific rent growth %/yr
    forecast_years:        int
    rate_source:           str     # "location" | "city" | "global"


class YearlyForecastItem(BaseModel):
    year:              int
    property_price:    float
    monthly_rent:      float
    annual_rent:       float
    total_rent_earned: float
    roi_pct:           float
    investment_rating: str


# ── Response ──────────────────────────────────────────────────────────────────

class ROIPredictionResponse(BaseModel):
    status:           str = "success"
    input_summary:    InputSummary
    ml_estimates:     MLEstimates
    five_year_summary: FiveYearSummary
    applied_adjustments: Dict[str, Any]
    yearly_forecast:  List[YearlyForecastItem]


class RiskPredictionRequest(BaseModel):
    location:      str   = Field(..., example="Banjara Hills, Hyderabad")
    property_type: str   = Field(..., example="apartment")
    bhk:           int   = Field(..., ge=0, le=10, example=3)
    area:          float = Field(..., gt=0, example=1500.0)
    price:         float = Field(..., gt=0, example=8500000.0)
    rent:          float = Field(..., ge=0, example=25000.0)
    property_age:  float = Field(5.0, ge=0, example=5.0)
    floor:         int   = Field(1, ge=0, example=3)
    furnishing:    str   = Field("semi-furnished", example="semi-furnished")

    # Optional risk-specific fields.
    bath: Optional[int] = Field(None, ge=1, le=10, example=3)
    maintenance_cost: Optional[float] = Field(None, ge=0, example=2500.0)
    investment_years: int = Field(5, ge=1, le=30, example=5)

    class Config:
        json_schema_extra = {
            "example": {
                "location": "Banjara Hills, Hyderabad",
                "property_type": "apartment",
                "bhk": 3,
                "area": 1500,
                "price": 8500000,
                "rent": 25000,
                "property_age": 5,
                "floor": 3,
                "furnishing": "semi-furnished",
                "bath": 3,
                "maintenance_cost": 2500,
                "investment_years": 5,
            }
        }


class RiskPredictionResponse(BaseModel):
    status: str = "success"
    risk_level: str
    risk_code: int
    model: str = "RandomForestClassifier"
    inputs_used: Dict[str, Any]
