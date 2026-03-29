from datetime import datetime
from typing import Optional

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


class PayoutRunRequest(BaseModel):
    payout_month: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}$")


class InvestorPayoutOut(BaseModel):
    id: int
    investor_id: int
    property_id: int
    payout_month: str
    amount: float
    onchain_tx_hash: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PayoutRunResponse(BaseModel):
    payout_month: str
    total_investors: int
    total_amount: float
    payouts: list[InvestorPayoutOut]
