import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import require_roles
from app.db.session import get_db
from app.models import ShareListing, User, UserRole
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
    db: Session = Depends(get_db),
    investor: User = Depends(require_roles(UserRole.INVESTOR)),
):
    logger.info("buy_shares investor_id=%s property_id=%s shares=%s", investor.id, payload.property_id, payload.shares)
    tx = buy_primary_shares(db, investor, payload.property_id, payload.shares, payload.wallet_address)
    return {"transaction_id": tx.id, "tx_hash": tx.onchain_tx_hash}


@router.post("/list", response_model=ShareListingOut)
def create_listing(
    payload: ShareListingCreate,
    db: Session = Depends(get_db),
    investor: User = Depends(require_roles(UserRole.INVESTOR)),
):
    logger.info(
        "create_listing investor_id=%s property_id=%s shares=%s",
        investor.id,
        payload.property_id,
        payload.shares_for_sale,
    )
    return list_shares_for_sale(db, investor, payload.property_id, payload.shares_for_sale, payload.price_per_share)


@router.get("/listings", response_model=list[ShareListingOut])
def active_listings(db: Session = Depends(get_db)):
    logger.info("active_listings")
    return db.query(ShareListing).filter(ShareListing.is_active.is_(True)).order_by(ShareListing.created_at.desc()).all()


@router.post("/trade")
def buy_from_listing(
    payload: TradeSharesRequest,
    db: Session = Depends(get_db),
    investor: User = Depends(require_roles(UserRole.INVESTOR)),
):
    logger.info("buy_from_listing investor_id=%s listing_id=%s shares=%s", investor.id, payload.listing_id, payload.shares_to_buy)
    tx = buy_secondary_shares(db, investor, payload.listing_id, payload.shares_to_buy, payload.buyer_wallet_address)
    return {"transaction_id": tx.id, "tx_hash": tx.onchain_tx_hash}


@router.post("/exit-simulate")
def exit_simulation(
    payload: ExitSimulateRequest,
    db: Session = Depends(get_db),
    investor: User = Depends(require_roles(UserRole.INVESTOR)),
):
    """Simulate partial exit with ROI, rental income and LTCG tax breakdown (Indian compliance)."""
    logger.info("exit_simulate investor_id=%s property_id=%s shares=%s", investor.id, payload.property_id, payload.shares_to_exit)
    return simulate_partial_exit(db, investor, payload.property_id, payload.shares_to_exit)


@router.post("/payouts/run", response_model=PayoutRunResponse)
def run_monthly_payouts(
    payload: PayoutRunRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info("run_monthly_payouts admin_id=%s payout_month=%s", admin.id, payload.payout_month)
    return distribute_monthly_roi(db, payload.payout_month)


@router.post("/buy")
def buy_shares(
    payload: BuySharesRequest,
    db: Session = Depends(get_db),
    investor: User = Depends(require_roles(UserRole.INVESTOR)),
):
    logger.info("buy_shares investor_id=%s property_id=%s shares=%s", investor.id, payload.property_id, payload.shares)
    tx = buy_primary_shares(db, investor, payload.property_id, payload.shares, payload.wallet_address)
    return {"transaction_id": tx.id, "tx_hash": tx.onchain_tx_hash}


@router.post("/list", response_model=ShareListingOut)
def create_listing(
    payload: ShareListingCreate,
    db: Session = Depends(get_db),
    investor: User = Depends(require_roles(UserRole.INVESTOR)),
):
    logger.info(
        "create_listing investor_id=%s property_id=%s shares=%s",
        investor.id,
        payload.property_id,
        payload.shares_for_sale,
    )
    return list_shares_for_sale(db, investor, payload.property_id, payload.shares_for_sale, payload.price_per_share)


@router.get("/listings", response_model=list[ShareListingOut])
def active_listings(db: Session = Depends(get_db)):
    logger.info("active_listings")
    return db.query(ShareListing).filter(ShareListing.is_active.is_(True)).order_by(ShareListing.created_at.desc()).all()


@router.post("/trade")
def buy_from_listing(
    payload: TradeSharesRequest,
    db: Session = Depends(get_db),
    investor: User = Depends(require_roles(UserRole.INVESTOR)),
):
    logger.info("buy_from_listing investor_id=%s listing_id=%s shares=%s", investor.id, payload.listing_id, payload.shares_to_buy)
    tx = buy_secondary_shares(db, investor, payload.listing_id, payload.shares_to_buy, payload.buyer_wallet_address)
    return {"transaction_id": tx.id, "tx_hash": tx.onchain_tx_hash}
