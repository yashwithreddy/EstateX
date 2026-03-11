from datetime import datetime

from pydantic import BaseModel, Field


class BuySharesRequest(BaseModel):
    property_id: int
    shares: int = Field(gt=0)
    wallet_address: str = "0x0000000000000000000000000000000000000000"


class ShareListingCreate(BaseModel):
    property_id: int
    shares_for_sale: int = Field(gt=0)
    price_per_share: float = Field(gt=0)


class TradeSharesRequest(BaseModel):
    listing_id: int
    shares_to_buy: int = Field(gt=0)
    buyer_wallet_address: str = "0x0000000000000000000000000000000000000000"


class ExitSimulateRequest(BaseModel):
    property_id: int
    shares_to_exit: int = Field(gt=0)


class ShareListingOut(BaseModel):
    id: int
    property_id: int
    seller_id: int
    shares_for_sale: int
    price_per_share: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
