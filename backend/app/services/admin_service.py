from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.blockchain.service import blockchain_service
from app.models import Document, DocumentType, ListingStatus, Property

REQUIRED_DOC_COUNT = len(list(DocumentType))


def pending_documents(db: Session) -> list[Document]:
    return db.query(Document).filter(Document.is_verified.is_(False)).order_by(Document.created_at.asc()).all()


def pending_properties(db: Session) -> list[Property]:
    return db.query(Property).filter(Property.listing_status == ListingStatus.PENDING).order_by(Property.created_at.asc()).all()


def verify_document(
    db: Session,
    document_id: int,
    admin_id: int,
    approve: bool,
    rejection_reason: Optional[str] = None,
) -> Document:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    document.is_verified = bool(approve)
    document.verified_by_admin_id = admin_id

    prop = db.query(Property).filter(Property.id == document.property_id).first()
    if prop:
        docs = db.query(Document).filter(Document.property_id == prop.id).all()
        all_verified = len(docs) >= REQUIRED_DOC_COUNT and all(d.is_verified for d in docs)
        if all_verified:
            prop.is_verified = True
            prop.listing_status = ListingStatus.APPROVED
            prop.rejection_reason = None
            blockchain_service.register_property(prop.id, prop.total_shares)
        elif not approve:
            prop.is_verified = False
            prop.listing_status = ListingStatus.REJECTED
            prop.rejection_reason = rejection_reason or "Document verification rejected"

    db.commit()
    db.refresh(document)
    return document


def approve_property_listing(
    db: Session,
    property_id: int,
    approve: bool,
    rejection_reason: Optional[str] = None,
) -> Property:
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    if approve:
        # Force approval: also mark all associated documents as verified and set is_verified = True.
        docs = db.query(Document).filter(Document.property_id == property_id).all()
        for doc in docs:
            doc.is_verified = True
        prop.is_verified = True
        prop.listing_status = ListingStatus.APPROVED
        prop.rejection_reason = None
        blockchain_service.register_property(prop.id, prop.total_shares)
    else:
        prop.listing_status = ListingStatus.REJECTED
        prop.rejection_reason = rejection_reason or "Rejected by admin"

    db.commit()
    db.refresh(prop)
    return prop
