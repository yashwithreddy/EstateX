import logging

from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.deps import require_roles
from app.db.session import get_db
from app.db.mongo import serialize_docs
from app.models import UserRole
from app.schemas.investment import (
    BuySharesRequest,
    ExitSimulateRequest,
    PayoutRunRequest,
    PayoutRunResponse,
    ShareListingCreate,
    ShareListingOut,
    TradeSharesRequest,
)
from app.services.investment_service import (
    buy_primary_shares,
    buy_secondary_shares,
    distribute_monthly_roi,
    list_shares_for_sale,
    simulate_partial_exit,
)

router = APIRouter(prefix="/api/v1/investments", tags=["investments"])
logger = logging.getLogger(__name__)


@router.post("/buy")
def buy_shares(
    payload: BuySharesRequest,
    db: Database = Depends(get_db),
    investor: dict = Depends(require_roles(UserRole.INVESTOR)),
):
    logger.info("buy_shares investor_id=%s property_id=%s shares=%s", investor["id"], payload.property_id, payload.shares)
    tx = buy_primary_shares(db, investor, payload.property_id, payload.shares, payload.wallet_address)
    return {"transaction_id": tx["id"], "tx_hash": tx.get("onchain_tx_hash")}


@router.post("/list", response_model=ShareListingOut)
def create_listing(
    payload: ShareListingCreate,
    db: Database = Depends(get_db),
    investor: dict = Depends(require_roles(UserRole.INVESTOR)),
):
    logger.info(
        "create_listing investor_id=%s property_id=%s shares=%s",
        investor["id"],
        payload.property_id,
        payload.shares_for_sale,
    )
    return list_shares_for_sale(db, investor, payload.property_id, payload.shares_for_sale, payload.price_per_share)


@router.get("/listings", response_model=list[ShareListingOut])
def active_listings(db: Database = Depends(get_db)):
    logger.info("active_listings")
    listings = list(db.share_listings.find({"is_active": True}).sort("created_at", -1))
    return serialize_docs(listings)


@router.post("/trade")
def buy_from_listing(
    payload: TradeSharesRequest,
    db: Database = Depends(get_db),
    investor: dict = Depends(require_roles(UserRole.INVESTOR)),
):
    logger.info(
        "buy_from_listing investor_id=%s listing_id=%s shares=%s",
        investor["id"],
        payload.listing_id,
        payload.shares_to_buy,
    )
    result = buy_secondary_shares(
        db,
        investor,
        payload.listing_id,
        payload.shares_to_buy,
        payload.buyer_wallet_address,
    )
    if result.get("status") == "unlisted":
        return result
    return {"transaction_id": result["id"], "tx_hash": result.get("onchain_tx_hash")}


@router.post("/exit-simulate")
def exit_simulation(
    payload: ExitSimulateRequest,
    db: Database = Depends(get_db),
    investor: dict = Depends(require_roles(UserRole.INVESTOR)),
):
    """Simulate partial exit with ROI, rental income and LTCG tax breakdown (Indian compliance)."""
    logger.info(
        "exit_simulate investor_id=%s property_id=%s shares=%s",
        investor["id"],
        payload.property_id,
        payload.shares_to_exit,
    )
    return simulate_partial_exit(db, investor, payload.property_id, payload.shares_to_exit)


@router.post("/payouts/run", response_model=PayoutRunResponse)
def run_monthly_payouts(
    payload: PayoutRunRequest,
    db: Database = Depends(get_db),
    admin: dict = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info("run_monthly_payouts admin_id=%s payout_month=%s", admin["id"], payload.payout_month)
    return distribute_monthly_roi(db, payload.payout_month)


