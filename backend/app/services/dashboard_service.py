from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import InvestmentTransaction, ListingStatus, Ownership, Property, ShareListing, User


def investor_dashboard(db: Session, user_id: int) -> dict:
    holdings = (
        db.query(Ownership, Property)
        .join(Property, Property.id == Ownership.property_id)
        .filter(Ownership.investor_id == user_id)
        .all()
    )

    total_value = 0.0
    distribution = []
    portfolio = []
    for ownership, prop in holdings:
        holding_value = float(prop.price_per_share) * ownership.shares
        total_value += holding_value
        distribution.append(
            {
                "property_id": prop.id,
                "property": prop.title,
                "shares": ownership.shares,
                "value": round(holding_value, 2),
            }
        )
        portfolio.append(
            {
                "property_id": prop.id,
                "title": prop.title,
                "city": prop.city,
                "state": prop.state,
                "shares": ownership.shares,
                "share_price": float(prop.price_per_share),
                "estimated_value": round(holding_value, 2),
                "roi_percent": prop.ai_predicted_roi,
                "risk_level": prop.risk_level.value,
            }
        )

    transactions = (
        db.query(InvestmentTransaction)
        .filter((InvestmentTransaction.buyer_id == user_id) | (InvestmentTransaction.seller_id == user_id))
        .order_by(InvestmentTransaction.created_at.desc())
        .limit(50)
        .all()
    )

    tx_payload = [
        {
            "id": tx.id,
            "property_id": tx.property_id,
            "shares": tx.shares,
            "amount": float(tx.amount),
            "tx_type": tx.tx_type.value,
            "onchain_tx_hash": tx.onchain_tx_hash,
            "created_at": tx.created_at.isoformat(),
        }
        for tx in transactions
    ]

    return {
        "total_investment_value": round(total_value, 2),
        "ownership_distribution": distribution,
        "portfolio": portfolio,
        "transaction_history": tx_payload,
    }


def owner_dashboard(db: Session, owner_id: int) -> dict:
    properties = db.query(Property).filter(Property.owner_id == owner_id).order_by(Property.created_at.desc()).all()
    property_ids = [p.id for p in properties]

    activities = []
    if property_ids:
        txs = (
            db.query(InvestmentTransaction)
            .filter(InvestmentTransaction.property_id.in_(property_ids))
            .order_by(InvestmentTransaction.created_at.desc())
            .limit(30)
            .all()
        )
        activities = [
            {
                "id": tx.id,
                "property_id": tx.property_id,
                "shares": tx.shares,
                "amount": float(tx.amount),
                "tx_type": tx.tx_type.value,
                "created_at": tx.created_at.isoformat(),
            }
            for tx in txs
        ]

    return {
        "properties": [
            {
                "id": p.id,
                "title": p.title,
                "city": p.city,
                "state": p.state,
                "verification_status": p.listing_status.value,
                "rejection_reason": p.rejection_reason,
                "available_shares": p.available_shares,
                "total_shares": p.total_shares,
            }
            for p in properties
        ],
        "investment_activity": activities,
    }


def admin_dashboard(db: Session) -> dict:
    pending_docs = db.query(func.count()).select_from(Property).filter(Property.is_verified.is_(False)).scalar() or 0
    approved_props = (
        db.query(func.count())
        .select_from(Property)
        .filter(Property.listing_status == ListingStatus.APPROVED, Property.available_shares > 0)
        .scalar()
        or 0
    )
    pending_props = (
        db.query(func.count())
        .select_from(Property)
        .filter(Property.listing_status == ListingStatus.PENDING)
        .scalar()
        or 0
    )
    total_investments = db.query(func.count()).select_from(InvestmentTransaction).scalar() or 0
    active_liquidity_listings = (
        db.query(func.count()).select_from(ShareListing).filter(ShareListing.is_active.is_(True)).scalar() or 0
    )

    return {
        "pending_verifications": pending_docs,
        "pending_properties": pending_props,
        "approved_properties": approved_props,
        "total_investments": total_investments,
        "active_liquidity_listings": active_liquidity_listings,
    }
