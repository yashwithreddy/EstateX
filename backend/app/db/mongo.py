from __future__ import annotations

from datetime import datetime
from typing import Iterable

from pymongo import ReturnDocument
from pymongo.database import Database


def get_next_sequence(db: Database, name: str) -> int:
    result = db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(result["seq"])


def serialize_doc(doc: dict | None) -> dict | None:
    if not doc:
        return None
    payload = dict(doc)
    payload["id"] = int(payload.pop("_id"))
    return payload


def serialize_docs(docs: Iterable[dict]) -> list[dict]:
    return [serialize_doc(doc) for doc in docs if doc is not None]


def utc_now() -> datetime:
    return datetime.utcnow()


def ensure_indexes(db: Database) -> None:
    db.users.create_index("email", unique=True)
    db.users.create_index("role")
    db.users.create_index("is_active")

    db.properties.create_index("owner_id")
    db.properties.create_index("listing_status")
    db.properties.create_index("is_verified")
    db.properties.create_index("created_at")

    db.documents.create_index("property_id")
    db.documents.create_index("document_type")
    db.documents.create_index("is_verified")
    db.documents.create_index("created_at")

    db.ownerships.create_index([("property_id", 1), ("investor_id", 1)], unique=True)
    db.share_listings.create_index("property_id")
    db.share_listings.create_index("seller_id")
    db.share_listings.create_index("is_active")
    db.share_listings.create_index("created_at")

    db.investment_transactions.create_index("property_id")
    db.investment_transactions.create_index("buyer_id")
    db.investment_transactions.create_index("seller_id")
    db.investment_transactions.create_index("created_at")

    db.investor_payouts.create_index(
        [("investor_id", 1), ("property_id", 1), ("payout_month", 1)],
        unique=True,
    )
    db.investor_payouts.create_index("created_at")
