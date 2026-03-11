from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models import DocumentType, ListingStatus, PropertyType, RiskLevel


class PropertyCreate(BaseModel):
    title: str = Field(min_length=5, max_length=180)
    description: str = Field(min_length=15, max_length=1000)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    location: str = Field(min_length=3, max_length=250)
    property_type: PropertyType
    image_url: Optional[str] = None
    property_price: float = Field(gt=0)
    total_shares: int = Field(gt=0, le=1_000_000)
    rental_yield: float = Field(ge=0, le=30)
    demand_index: float = Field(ge=0, le=1)
    market_trend: float = Field(ge=0, le=1)
    ai_predicted_roi: float = Field(ge=0, le=100)
    risk_level: RiskLevel


class DocumentOut(BaseModel):
    id: int
    document_type: DocumentType
    file_name: str
    sha256_hash: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PropertyOut(BaseModel):
    id: int
    owner_id: int
    title: str
    description: str
    city: str
    state: str
    location: str
    property_type: PropertyType
    image_url: Optional[str]
    property_price: float
    total_shares: int
    available_shares: int
    price_per_share: float
    rental_yield: float
    demand_index: float
    market_trend: float
    ai_predicted_roi: float
    risk_level: RiskLevel
    listing_status: ListingStatus
    is_verified: bool
    rejection_reason: Optional[str]
    created_at: datetime
    documents: list[DocumentOut] = []

    class Config:
        from_attributes = True
