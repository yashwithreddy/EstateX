import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import require_roles
from app.db.session import get_db
from app.models import Property, User, UserRole
from app.schemas.admin import AdminApprovalRequest
from app.services.admin_service import approve_property_listing, pending_documents, pending_properties, verify_document

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.get("/documents/pending")
def get_pending_documents(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    docs = pending_documents(db)
    return [
        {
            "document_id": doc.id,
            "property_id": doc.property_id,
            "property_title": doc.property.title,
            "document_type": doc.document_type.value,
            "sha256_hash": doc.sha256_hash,
            "uploaded_at": doc.created_at,
            "verification_status": "verified" if doc.is_verified else "pending",
        }
        for doc in docs
    ]


@router.get("/properties/pending")
def get_pending_properties(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    props = pending_properties(db)
    return [
        {
            "property_id": p.id,
            "title": p.title,
            "city": p.city,
            "state": p.state,
            "verification_status": p.listing_status.value,
            "is_verified": p.is_verified,
            "owner_id": p.owner_id,
            "document_count": len(p.documents),
            "verified_doc_count": sum(1 for d in p.documents if d.is_verified),
        }
        for p in props
    ]


@router.patch("/documents/{document_id}/verify")
def verify_uploaded_document(
    document_id: int,
    payload: AdminApprovalRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info("verify_uploaded_document admin_id=%s document_id=%s approve=%s", admin.id, document_id, payload.approve)
    doc = verify_document(db, document_id, admin.id, payload.approve, payload.rejection_reason)
    return {"document_id": doc.id, "is_verified": doc.is_verified}


@router.patch("/properties/{property_id}/approve")
def approve_listing(
    property_id: int,
    payload: AdminApprovalRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    prop = approve_property_listing(db, property_id, payload.approve, payload.rejection_reason)
    return {
        "property_id": prop.id,
        "listing_status": prop.listing_status.value,
        "rejection_reason": prop.rejection_reason,
    }


@router.get("/properties/{property_id}/documents")
def property_documents(
    property_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        return []
    return [
        {
            "document_id": d.id,
            "document_type": d.document_type.value,
            "file_name": d.file_name,
            "file_path": d.file_path,
            "sha256_hash": d.sha256_hash,
            "is_verified": d.is_verified,
        }
        for d in prop.documents
    ]


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """List all registered users for admin management."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "is_active": u.is_active,
            "wallet_address": u.wallet_address,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.patch("/users/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Enable or disable a user account (cannot disable another admin)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Cannot modify an admin account")
    if user.id == admin.id:
        raise HTTPException(status_code=403, detail="Cannot disable your own account")
    user.is_active = not user.is_active
    db.commit()
    logger.info("toggle_user_active admin_id=%s user_id=%s is_active=%s", admin.id, user.id, user.is_active)
    return {"user_id": user.id, "is_active": user.is_active}


@router.get("/documents/pending")
def get_pending_documents(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    docs = pending_documents(db)
    return [
        {
            "document_id": doc.id,
            "property_id": doc.property_id,
            "property_title": doc.property.title,
            "document_type": doc.document_type.value,
            "sha256_hash": doc.sha256_hash,
            "uploaded_at": doc.created_at,
            "verification_status": "verified" if doc.is_verified else "pending",
        }
        for doc in docs
    ]


@router.get("/properties/pending")
def get_pending_properties(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    props = pending_properties(db)
    return [
        {
            "property_id": p.id,
            "title": p.title,
            "city": p.city,
            "state": p.state,
            "verification_status": p.listing_status.value,
            "owner_id": p.owner_id,
        }
        for p in props
    ]


@router.patch("/documents/{document_id}/verify")
def verify_uploaded_document(
    document_id: int,
    payload: AdminApprovalRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info("verify_uploaded_document admin_id=%s document_id=%s approve=%s", admin.id, document_id, payload.approve)
    doc = verify_document(db, document_id, admin.id, payload.approve, payload.rejection_reason)
    return {"document_id": doc.id, "is_verified": doc.is_verified}


@router.patch("/properties/{property_id}/approve")
def approve_listing(
    property_id: int,
    payload: AdminApprovalRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    prop = approve_property_listing(db, property_id, payload.approve, payload.rejection_reason)
    return {
        "property_id": prop.id,
        "listing_status": prop.listing_status.value,
        "rejection_reason": prop.rejection_reason,
    }


@router.get("/properties/{property_id}/documents")
def property_documents(
    property_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        return []
    return [
        {
            "document_id": d.id,
            "document_type": d.document_type.value,
            "file_name": d.file_name,
            "file_path": d.file_path,
            "sha256_hash": d.sha256_hash,
            "is_verified": d.is_verified,
        }
        for d in prop.documents
    ]
