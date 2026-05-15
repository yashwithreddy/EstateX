from fastapi import HTTPException, status
from pathlib import Path
from pymongo.database import Database
from typing import Optional

from app.blockchain.service import blockchain_service
from app.db.mongo import serialize_doc, serialize_docs
from app.models import DocumentType, ListingStatus

REQUIRED_DOC_COUNT = len(list(DocumentType))


def pending_documents(db: Database) -> list[dict]:
    docs = list(db.documents.find({"is_verified": False}).sort("created_at", 1))
    return serialize_docs(docs)


def pending_properties(db: Database) -> list[dict]:
    props = list(db.properties.find({"listing_status": ListingStatus.PENDING.value}).sort("created_at", 1))
    return serialize_docs(props)


def verify_document(
    db: Database,
    document_id: int,
    admin_id: int,
    approve: bool,
    rejection_reason: Optional[str] = None,
) -> dict:
    document = db.documents.find_one({"_id": document_id})
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    db.documents.update_one(
        {"_id": document_id},
        {"$set": {"is_verified": bool(approve), "verified_by_admin_id": admin_id}},
    )

    prop = db.properties.find_one({"_id": document["property_id"]})
    if prop:
        docs = list(db.documents.find({"property_id": prop["_id"]}))
        all_verified = len(docs) >= REQUIRED_DOC_COUNT and all(d.get("is_verified") for d in docs)
        if all_verified:
            db.properties.update_one(
                {"_id": prop["_id"]},
                {"$set": {"is_verified": True, "listing_status": ListingStatus.APPROVED.value, "rejection_reason": None}},
            )
            blockchain_service.register_property(prop["_id"], prop["total_shares"])
        elif not approve:
            db.properties.update_one(
                {"_id": prop["_id"]},
                {
                    "$set": {
                        "is_verified": False,
                        "listing_status": ListingStatus.REJECTED.value,
                        "rejection_reason": rejection_reason or "Document verification rejected",
                    }
                },
            )

    return serialize_doc(db.documents.find_one({"_id": document_id}))


def approve_property_listing(
    db: Database,
    property_id: int,
    approve: bool,
    rejection_reason: Optional[str] = None,
) -> dict:
    prop = db.properties.find_one({"_id": property_id})
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if approve:
        docs = list(db.documents.find({"property_id": property_id}))
        all_verified = len(docs) >= REQUIRED_DOC_COUNT and all(d.get("is_verified") for d in docs)
        if not all_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All required documents must be verified before approving a property",
            )
        db.properties.update_one(
            {"_id": property_id},
            {"$set": {"is_verified": True, "listing_status": ListingStatus.APPROVED.value, "rejection_reason": None}},
        )
        blockchain_service.register_property(prop["_id"], prop["total_shares"])
    else:
        db.properties.update_one(
            {"_id": property_id},
            {"$set": {"listing_status": ListingStatus.REJECTED.value, "rejection_reason": rejection_reason or "Rejected by admin"}},
        )

    return serialize_doc(db.properties.find_one({"_id": property_id}))


def delete_property_listing(db: Database, property_id: int) -> dict:
    prop = db.properties.find_one({"_id": property_id})
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    docs = list(db.documents.find({"property_id": property_id}))
    deleted_files = 0
    for doc in docs:
        file_path = doc.get("file_path")
        if file_path:
            try:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    deleted_files += 1
            except OSError:
                # Best effort cleanup; keep deletion moving even if file removal fails.
                pass

    delete_counts = {
        "documents": db.documents.delete_many({"property_id": property_id}).deleted_count,
        "ownerships": db.ownerships.delete_many({"property_id": property_id}).deleted_count,
        "share_listings": db.share_listings.delete_many({"property_id": property_id}).deleted_count,
        "investment_transactions": db.investment_transactions.delete_many({"property_id": property_id}).deleted_count,
        "investor_payouts": db.investor_payouts.delete_many({"property_id": property_id}).deleted_count,
    }

    db.properties.delete_one({"_id": property_id})

    return {
        "property_id": property_id,
        "deleted": True,
        "deleted_files": deleted_files,
        "deleted_records": delete_counts,
    }
