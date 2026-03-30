from pymongo.database import Database

from app.models import ListingStatus


def investor_dashboard(db: Database, user_id: int) -> dict:
    holdings = list(db.ownerships.find({"investor_id": user_id}))

    total_value = 0.0
    distribution = []
    portfolio = []
    for ownership in holdings:
        prop = db.properties.find_one({"_id": ownership["property_id"]})
        if not prop:
            continue
        holding_value = float(prop["price_per_share"]) * ownership.get("shares", 0)
        total_value += holding_value
        distribution.append(
            {
                "property_id": prop["_id"],
                "property": prop["title"],
                "shares": ownership.get("shares", 0),
                "value": round(holding_value, 2),
            }
        )
        portfolio.append(
            {
                "property_id": prop["_id"],
                "title": prop["title"],
                "city": prop["city"],
                "state": prop["state"],
                "shares": ownership.get("shares", 0),
                "share_price": float(prop["price_per_share"]),
                "estimated_value": round(holding_value, 2),
                "roi_percent": prop["ai_predicted_roi"],
                "risk_level": prop["risk_level"],
            }
        )

    transactions = list(
        db.investment_transactions.find(
            {"$or": [{"buyer_id": user_id}, {"seller_id": user_id}]}
        )
        .sort("created_at", -1)
        .limit(50)
    )

    recent_payouts = list(db.investor_payouts.find({"investor_id": user_id}).sort("created_at", -1).limit(12))

    tx_payload = [
        {
            "id": int(tx["_id"]),
            "property_id": tx["property_id"],
            "shares": tx["shares"],
            "amount": float(tx["amount"]),
            "tx_type": tx["tx_type"],
            "onchain_tx_hash": tx.get("onchain_tx_hash"),
            "created_at": tx["created_at"].isoformat(),
        }
        for tx in transactions
    ]

    hyderabad_properties = list(
        db.properties.find(
            {
                "$or": [
                    {"location": {"$regex": "hyderabad", "$options": "i"}},
                    {"city": {"$regex": "hyderabad", "$options": "i"}},
                    {"state": {"$regex": "telangana", "$options": "i"}},
                ]
            }
        ).sort("created_at", -1)
    )

    hyderabad_payload = [
        {
            "property_id": prop["_id"],
            "title": prop["title"],
            "city": prop["city"],
            "state": prop["state"],
            "location": prop["location"],
            "property_type": prop["property_type"],
            "price_per_share": float(prop["price_per_share"]),
            "available_shares": prop["available_shares"],
            "roi_percent": prop["ai_predicted_roi"],
            "risk_level": prop["risk_level"],
            "listing_status": prop["listing_status"],
            "is_verified": prop["is_verified"],
        }
        for prop in hyderabad_properties
    ]

    user = db.users.find_one({"_id": user_id}) or {}
    return {
        "total_investment_value": round(total_value, 2),
        "wallet_balance": float(user.get("wallet_balance", 0)),
        "ownership_distribution": distribution,
        "portfolio": portfolio,
        "transaction_history": tx_payload,
        "recent_payouts": [
            {
                "id": int(payout["_id"]),
                "property_id": payout["property_id"],
                "payout_month": payout["payout_month"],
                "amount": float(payout["amount"]),
                "onchain_tx_hash": payout.get("onchain_tx_hash"),
                "created_at": payout["created_at"].isoformat(),
            }
            for payout in recent_payouts
        ],
        "hyderabad_property_count": len(hyderabad_payload),
        "hyderabad_properties": hyderabad_payload,
    }


def owner_dashboard(db: Database, owner_id: int) -> dict:
    properties = list(db.properties.find({"owner_id": owner_id}).sort("created_at", -1))
    property_ids = [p["_id"] for p in properties]

    activities = []
    if property_ids:
        txs = list(
            db.investment_transactions.find({"property_id": {"$in": property_ids}})
            .sort("created_at", -1)
            .limit(30)
        )
        activities = [
            {
                "id": int(tx["_id"]),
                "property_id": tx["property_id"],
                "shares": tx["shares"],
                "amount": float(tx["amount"]),
                "tx_type": tx["tx_type"],
                "created_at": tx["created_at"].isoformat(),
            }
            for tx in txs
        ]

    return {
        "properties": [
            {
                "id": p["_id"],
                "title": p["title"],
                "city": p["city"],
                "state": p["state"],
                "verification_status": p["listing_status"],
                "rejection_reason": p.get("rejection_reason"),
                "available_shares": p["available_shares"],
                "total_shares": p["total_shares"],
            }
            for p in properties
        ],
        "investment_activity": activities,
    }


def admin_dashboard(db: Database) -> dict:
    pending_docs = db.documents.count_documents({"is_verified": False})
    approved_props = db.properties.count_documents(
        {"listing_status": ListingStatus.APPROVED.value, "available_shares": {"$gt": 0}}
    )
    pending_props = db.properties.count_documents({"listing_status": ListingStatus.PENDING.value})
    total_investments = db.investment_transactions.count_documents({})
    active_liquidity_listings = db.share_listings.count_documents({"is_active": True})

    return {
        "pending_verifications": pending_docs,
        "pending_properties": pending_props,
        "approved_properties": approved_props,
        "total_investments": total_investments,
        "active_liquidity_listings": active_liquidity_listings,
    }
