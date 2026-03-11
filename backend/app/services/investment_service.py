from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.blockchain.service import blockchain_service
from app.models import InvestmentTransaction, ListingStatus, Ownership, Property, ShareListing, TransactionType, User


def _get_or_create_ownership(db: Session, property_id: int, investor_id: int) -> Ownership:
    ownership = (
        db.query(Ownership)
        .filter(Ownership.property_id == property_id, Ownership.investor_id == investor_id)
        .first()
    )
    if ownership:
        return ownership

    ownership = Ownership(property_id=property_id, investor_id=investor_id, shares=0)
    db.add(ownership)
    db.flush()
    return ownership


def buy_primary_shares(db: Session, investor: User, property_id: int, shares: int, wallet_address: str) -> InvestmentTransaction:
    property_item = db.query(Property).filter(Property.id == property_id).first()
    if not property_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if property_item.listing_status != ListingStatus.APPROVED or not property_item.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Property is not approved for investment")

    if shares > property_item.available_shares:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough shares available")

    tx_hash = blockchain_service.buy_primary(property_item.id, wallet_address, shares)

    property_item.available_shares -= shares
    ownership = _get_or_create_ownership(db, property_item.id, investor.id)
    ownership.shares += shares

    tx = InvestmentTransaction(
        property_id=property_item.id,
        buyer_id=investor.id,
        seller_id=property_item.owner_id,
        shares=shares,
        amount=float(property_item.price_per_share) * shares,
        tx_type=TransactionType.PRIMARY_BUY,
        onchain_tx_hash=tx_hash,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def list_shares_for_sale(db: Session, seller: User, property_id: int, shares_for_sale: int, price_per_share: float) -> ShareListing:
    ownership = (
        db.query(Ownership)
        .filter(Ownership.property_id == property_id, Ownership.investor_id == seller.id)
        .first()
    )
    if not ownership or ownership.shares < shares_for_sale:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient shares to list")

    listing = ShareListing(
        property_id=property_id,
        seller_id=seller.id,
        shares_for_sale=shares_for_sale,
        price_per_share=price_per_share,
        is_active=True,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


def buy_secondary_shares(
    db: Session,
    buyer: User,
    listing_id: int,
    shares_to_buy: int,
    buyer_wallet_address: str,
) -> InvestmentTransaction:
    listing = db.query(ShareListing).filter(ShareListing.id == listing_id, ShareListing.is_active.is_(True)).first()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    if shares_to_buy > listing.shares_for_sale:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Requested shares exceed listing availability")

    seller_ownership = (
        db.query(Ownership)
        .filter(Ownership.property_id == listing.property_id, Ownership.investor_id == listing.seller_id)
        .first()
    )
    if not seller_ownership or seller_ownership.shares < shares_to_buy:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seller does not hold enough shares")

    seller = db.query(User).filter(User.id == listing.seller_id).first()
    from_wallet = seller.wallet_address if seller else ""
    tx_hash = blockchain_service.transfer_secondary(listing.property_id, from_wallet, buyer_wallet_address, shares_to_buy)

    seller_ownership.shares -= shares_to_buy
    buyer_ownership = _get_or_create_ownership(db, listing.property_id, buyer.id)
    buyer_ownership.shares += shares_to_buy

    listing.shares_for_sale -= shares_to_buy
    if listing.shares_for_sale == 0:
        listing.is_active = False

    tx = InvestmentTransaction(
        property_id=listing.property_id,
        buyer_id=buyer.id,
        seller_id=listing.seller_id,
        shares=shares_to_buy,
        amount=float(listing.price_per_share) * shares_to_buy,
        tx_type=TransactionType.SECONDARY_BUY,
        onchain_tx_hash=tx_hash,
    )
    db.add(tx)

    sell_log = InvestmentTransaction(
        property_id=listing.property_id,
        buyer_id=buyer.id,
        seller_id=listing.seller_id,
        shares=shares_to_buy,
        amount=float(listing.price_per_share) * shares_to_buy,
        tx_type=TransactionType.SECONDARY_SELL,
        onchain_tx_hash=tx_hash,
    )
    db.add(sell_log)

    db.commit()
    db.refresh(tx)
    return tx


def simulate_partial_exit(db: Session, investor: User, property_id: int, shares_to_exit: int) -> dict:
    """Simulate a partial exit scenario with tax and returns estimations (Indian fintech compliance)."""
    property_item = db.query(Property).filter(Property.id == property_id).first()
    if not property_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    ownership = (
        db.query(Ownership)
        .filter(Ownership.property_id == property_id, Ownership.investor_id == investor.id)
        .first()
    )
    owned_shares = ownership.shares if ownership else 0

    if shares_to_exit > owned_shares:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You own {owned_shares} shares. Cannot exit {shares_to_exit}.",
        )

    share_price = float(property_item.price_per_share)
    roi_rate = float(property_item.ai_predicted_roi) / 100
    rental_yield_rate = float(property_item.rental_yield) / 100

    cost_basis = share_price * shares_to_exit
    # Estimate appreciated value using AI-predicted ROI (annual)
    appreciated_value = cost_basis * (1 + roi_rate)
    capital_gain = max(0.0, appreciated_value - cost_basis)

    # Indian LTCG tax: 20% with indexation (simplified)
    ltcg_tax = round(capital_gain * 0.20, 2)

    # Annual rental income estimate for held shares
    estimated_rental_income = round(cost_basis * rental_yield_rate, 2)

    net_proceeds = round(appreciated_value - ltcg_tax, 2)
    absolute_gain = round(net_proceeds - cost_basis, 2)

    return {
        "property_id": property_id,
        "property_title": property_item.title,
        "city": property_item.city,
        "total_shares_owned": owned_shares,
        "shares_to_exit": shares_to_exit,
        "shares_retained": owned_shares - shares_to_exit,
        "cost_basis": round(cost_basis, 2),
        "current_market_value": round(appreciated_value, 2),
        "capital_gain": round(capital_gain, 2),
        "ltcg_tax_estimate": ltcg_tax,
        "estimated_annual_rental_income": estimated_rental_income,
        "net_proceeds_after_tax": net_proceeds,
        "absolute_gain": absolute_gain,
        "roi_percent": round(roi_rate * 100, 2),
        "rental_yield_percent": round(rental_yield_rate * 100, 2),
    }
