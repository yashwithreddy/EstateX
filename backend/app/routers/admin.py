import logging

from fastapi import APIRouter, Depends, HTTPException
from pymongo import ReturnDocument
from pymongo.database import Database

from app.deps import require_roles
from app.db.session import get_db
from app.models import UserRole
from app.schemas.admin import AdminApprovalRequest
from app.services.admin_service import approve_property_listing, pending_documents, pending_properties, verify_document

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.get("/documents/pending")
def get_pending_documents(
    db: Database = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN)),
):
    docs = pending_documents(db)
    if not docs:
        return []
    property_ids = {doc["property_id"] for doc in docs}
    props = list(db.properties.find({"_id": {"$in": list(property_ids)}}))
    prop_map = {p["_id"]: p for p in props}
    return [
        {
            "document_id": doc["id"],
            "property_id": doc["property_id"],
            "property_title": prop_map.get(doc["property_id"], {}).get("title"),
            "document_type": doc["document_type"],
            "sha256_hash": doc["sha256_hash"],
            "uploaded_at": doc["created_at"],
            "verification_status": "verified" if doc.get("is_verified") else "pending",
        }
        for doc in docs
    ]


@router.get("/properties/pending")
def get_pending_properties(
    db: Database = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN)),
):
    props = pending_properties(db)
    if not props:
        return []
    prop_ids = [p["id"] for p in props]
    docs = list(db.documents.find({"property_id": {"$in": prop_ids}}))
    doc_map: dict[int, list[dict]] = {}
    for doc in docs:
        doc_map.setdefault(doc["property_id"], []).append(doc)

    return [
        {
            "property_id": p["id"],
            "title": p["title"],
            "city": p["city"],
            "state": p["state"],
            "verification_status": p["listing_status"],
            "is_verified": p.get("is_verified"),
            "owner_id": p["owner_id"],
            "document_count": len(doc_map.get(p["id"], [])),
            "verified_doc_count": sum(1 for d in doc_map.get(p["id"], []) if d.get("is_verified")),
        }
        for p in props
    ]


@router.patch("/documents/{document_id}/verify")
def verify_uploaded_document(
    document_id: int,
    payload: AdminApprovalRequest,
    db: Database = Depends(get_db),
    admin: dict = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info("verify_uploaded_document admin_id=%s document_id=%s approve=%s", admin["id"], document_id, payload.approve)
    doc = verify_document(db, document_id, admin["id"], payload.approve, payload.rejection_reason)
    return {"document_id": doc["id"], "is_verified": doc.get("is_verified")}


@router.patch("/properties/{property_id}/approve")
def approve_listing(
    property_id: int,
    payload: AdminApprovalRequest,
    db: Database = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN)),
):
    prop = approve_property_listing(db, property_id, payload.approve, payload.rejection_reason)
    return {
        "property_id": prop["id"],
        "listing_status": prop["listing_status"],
        "rejection_reason": prop.get("rejection_reason"),
    }


@router.get("/properties/{property_id}/documents")
def property_documents(
    property_id: int,
    db: Database = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN)),
):
    docs = list(db.documents.find({"property_id": property_id}).sort("created_at", 1))
    return [
        {
            "document_id": d["_id"],
            "document_type": d["document_type"],
            "file_name": d["file_name"],
            "file_path": d["file_path"],
            "sha256_hash": d["sha256_hash"],
            "is_verified": d.get("is_verified"),
        }
        for d in docs
    ]


@router.get("/users")
def list_users(
    db: Database = Depends(get_db),
    _: dict = Depends(require_roles(UserRole.ADMIN)),
):
    """List all registered users for admin management."""
    users = list(db.users.find({}).sort("created_at", -1))
    return [
        {
            "id": u["_id"],
            "email": u["email"],
            "full_name": u["full_name"],
            "role": u["role"],
            "is_active": u.get("is_active", True),
            "wallet_address": u.get("wallet_address"),
            "created_at": u["created_at"].isoformat(),
        }
        for u in users
    ]


@router.patch("/users/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    db: Database = Depends(get_db),
    admin: dict = Depends(require_roles(UserRole.ADMIN)),
):
    """Enable or disable a user account (cannot disable another admin)."""
    user = db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["role"] == UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Cannot modify an admin account")
    if user["_id"] == admin["id"]:
        raise HTTPException(status_code=403, detail="Cannot disable your own account")
    updated = db.users.find_one_and_update(
        {"_id": user_id},
        {"$set": {"is_active": not user.get("is_active", True)}},
        return_document=ReturnDocument.AFTER,
    )
    logger.info(
        "toggle_user_active admin_id=%s user_id=%s is_active=%s",
        admin["id"],
        user_id,
        updated.get("is_active"),
    )
    return {"user_id": user_id, "is_active": updated.get("is_active")}


