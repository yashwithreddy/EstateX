from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from pymongo import ReturnDocument
from pymongo.database import Database

from app.blockchain.service import blockchain_service
from app.db.mongo import get_next_sequence, serialize_doc, serialize_docs, utc_now
from app.models import ListingStatus, TransactionType, UserRole


def _get_or_create_ownership(db: Database, property_id: int, investor_id: int) -> dict:
    ownership = db.ownerships.find_one({"property_id": property_id, "investor_id": investor_id})
    if ownership:
        return serialize_doc(ownership)

    ownership_id = get_next_sequence(db, "ownerships")
    ownership_doc = {
        "_id": ownership_id,
        "property_id": property_id,
        "investor_id": investor_id,
        "shares": 0,
        "updated_at": utc_now(),
    }
    db.ownerships.insert_one(ownership_doc)
    return serialize_doc(ownership_doc)


def buy_primary_shares(db: Database, investor: dict, property_id: int, shares: int, wallet_address: str) -> dict:
    property_item = db.properties.find_one({"_id": property_id})
    if not property_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if property_item.get("listing_status") != ListingStatus.APPROVED.value or not property_item.get("is_verified"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Property is not approved for investment")
    if shares > property_item.get("available_shares", 0):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough shares available")

    property_item = db.properties.find_one_and_update(
        {"_id": property_id, "available_shares": {"$gte": shares}},
        {"$inc": {"available_shares": -shares}},
        return_document=ReturnDocument.AFTER,
    )
    if not property_item:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Share availability changed. Retry.")

    tx_hash = blockchain_service.buy_primary(property_id, wallet_address, shares)

    ownership = _get_or_create_ownership(db, property_id, investor["id"])
    db.ownerships.update_one(
        {"_id": ownership["id"]},
        {"$inc": {"shares": shares}, "$set": {"updated_at": utc_now()}},
    )

    tx_id = get_next_sequence(db, "investment_transactions")
    amount = float(property_item["price_per_share"]) * shares
    tx = {
        "_id": tx_id,
        "property_id": property_id,
        "buyer_id": investor["id"],
        "seller_id": property_item["owner_id"],
        "shares": shares,
        "amount": amount,
        "tx_type": TransactionType.PRIMARY_BUY.value,
        "onchain_tx_hash": tx_hash,
        "created_at": utc_now(),
    }
    db.investment_transactions.insert_one(tx)
    return serialize_doc(tx)


def list_shares_for_sale(
    db: Database,
    seller: dict,
    property_id: int,
    shares_for_sale: int,
    price_per_share: float,
) -> dict:
    ownership = db.ownerships.find_one({"property_id": property_id, "investor_id": seller["id"]})
    if not ownership or ownership.get("shares", 0) < shares_for_sale:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient shares to list")

    listing_id = get_next_sequence(db, "share_listings")
    listing = {
        "_id": listing_id,
        "property_id": property_id,
        "seller_id": seller["id"],
        "shares_for_sale": shares_for_sale,
        "price_per_share": price_per_share,
        "is_active": True,
        "created_at": utc_now(),
    }
    db.share_listings.insert_one(listing)
    return serialize_doc(listing)


def buy_secondary_shares(
    db: Database,
    buyer: dict,
    listing_id: int,
    shares_to_buy: int,
    buyer_wallet_address: str,
) -> dict:
    listing = db.share_listings.find_one({"_id": listing_id, "is_active": True})
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    if shares_to_buy > listing.get("shares_for_sale", 0):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Requested shares exceed listing availability")

    seller_ownership = db.ownerships.find_one(
        {"property_id": listing["property_id"], "investor_id": listing["seller_id"]}
    )
    if not seller_ownership or seller_ownership.get("shares", 0) < shares_to_buy:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seller does not hold enough shares")

    seller = db.users.find_one({"_id": listing["seller_id"]})
    from_wallet = seller.get("wallet_address") if seller else ""
    tx_hash = blockchain_service.transfer_secondary(listing["property_id"], from_wallet, buyer_wallet_address, shares_to_buy)

    db.ownerships.update_one(
        {"_id": seller_ownership["_id"]},
        {"$inc": {"shares": -shares_to_buy}, "$set": {"updated_at": utc_now()}},
    )
    buyer_ownership = _get_or_create_ownership(db, listing["property_id"], buyer["id"])
    db.ownerships.update_one(
        {"_id": buyer_ownership["id"]},
        {"$inc": {"shares": shares_to_buy}, "$set": {"updated_at": utc_now()}},
    )

    updated_listing = db.share_listings.find_one_and_update(
        {"_id": listing_id, "is_active": True, "shares_for_sale": {"$gte": shares_to_buy}},
        {"$inc": {"shares_for_sale": -shares_to_buy}},
        return_document=ReturnDocument.AFTER,
    )
    if updated_listing and updated_listing.get("shares_for_sale", 0) == 0:
        db.share_listings.update_one({"_id": listing_id}, {"$set": {"is_active": False}})

    tx_id = get_next_sequence(db, "investment_transactions")
    amount = float(listing["price_per_share"]) * shares_to_buy
    tx = {
        "_id": tx_id,
        "property_id": listing["property_id"],
        "buyer_id": buyer["id"],
        "seller_id": listing["seller_id"],
        "shares": shares_to_buy,
        "amount": amount,
        "tx_type": TransactionType.SECONDARY_BUY.value,
        "onchain_tx_hash": tx_hash,
        "created_at": utc_now(),
    }
    db.investment_transactions.insert_one(tx)

    sell_log_id = get_next_sequence(db, "investment_transactions")
    db.investment_transactions.insert_one(
        {
            "_id": sell_log_id,
            "property_id": listing["property_id"],
            "buyer_id": buyer["id"],
            "seller_id": listing["seller_id"],
            "shares": shares_to_buy,
            "amount": amount,
            "tx_type": TransactionType.SECONDARY_SELL.value,
            "onchain_tx_hash": tx_hash,
            "created_at": utc_now(),
        }
    )

    return serialize_doc(tx)


def simulate_partial_exit(db: Database, investor: dict, property_id: int, shares_to_exit: int) -> dict:
    """Simulate a partial exit scenario with tax and returns estimations (Indian fintech compliance)."""
    property_item = db.properties.find_one({"_id": property_id})
    if not property_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    ownership = db.ownerships.find_one({"property_id": property_id, "investor_id": investor["id"]})
    owned_shares = ownership.get("shares", 0) if ownership else 0

    if shares_to_exit > owned_shares:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You own {owned_shares} shares. Cannot exit {shares_to_exit}.",
        )

    share_price = float(property_item["price_per_share"])
    roi_rate = float(property_item["ai_predicted_roi"]) / 100
    rental_yield_rate = float(property_item["rental_yield"]) / 100

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
        "property_title": property_item["title"],
        "city": property_item["city"],
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


def distribute_monthly_roi(db: Database, payout_month: Optional[str] = None) -> dict:
    if not payout_month:
        payout_month = datetime.utcnow().strftime("%Y-%m")

    ownerships = list(db.ownerships.find({}))
    payouts: list[dict] = []
    total_amount = 0.0
    investors_paid = set()

    for ownership in ownerships:
        if ownership.get("shares", 0) <= 0:
            continue

        investor = db.users.find_one({"_id": ownership["investor_id"], "role": UserRole.INVESTOR.value})
        if not investor:
            continue
        prop = db.properties.find_one({"_id": ownership["property_id"]})
        if not prop:
            continue

        existing = db.investor_payouts.find_one(
            {
                "investor_id": investor["_id"],
                "property_id": prop["_id"],
                "payout_month": payout_month,
            }
        )
        if existing:
            continue

        monthly_rate = (float(prop["ai_predicted_roi"]) / 100) / 12
        amount = round(float(prop["price_per_share"]) * ownership["shares"] * monthly_rate, 2)
        if amount <= 0:
            continue

        tx_hash = None
        if blockchain_service.enabled and investor.get("wallet_address"):
            amount_wei = int(round(amount * 10**18))
            tx_hash = blockchain_service.payout_roi(prop["_id"], investor["wallet_address"], amount_wei)
        else:
            db.users.update_one(
                {"_id": investor["_id"]},
                {"$inc": {"wallet_balance": amount}},
            )

        payout_id = get_next_sequence(db, "investor_payouts")
        payout = {
            "_id": payout_id,
            "investor_id": investor["_id"],
            "property_id": prop["_id"],
            "payout_month": payout_month,
            "amount": amount,
            "onchain_tx_hash": tx_hash or "wallet_credit",
            "created_at": utc_now(),
        }
        db.investor_payouts.insert_one(payout)
        payouts.append(payout)
        total_amount += amount
        investors_paid.add(investor["_id"])
    return {
        "payout_month": payout_month,
        "total_investors": len(investors_paid),
        "total_amount": round(total_amount, 2),
        "payouts": serialize_docs(payouts),
    }
