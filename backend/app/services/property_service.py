import secrets
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Document, DocumentType, ListingStatus, Property, PropertyType, User
from app.schemas.property import PropertyCreate
from app.utils.hash_utils import sha256_file

ALLOWED_PDF = {"application/pdf"}
REQUIRED_DOCS = [
    DocumentType.SALE_DEED,
    DocumentType.ENCUMBRANCE_CERTIFICATE,
    DocumentType.PROPERTY_TAX_RECEIPT,
    DocumentType.IDENTITY_PROOF,
]


def _save_pdf(file: UploadFile, property_id: int, doc_type: DocumentType) -> tuple[str, str]:
    if file.content_type not in ALLOWED_PDF:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")

    upload_dir = Path(settings.uploads_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{property_id}_{doc_type.value}_{secrets.token_hex(6)}.pdf"
    file_path = upload_dir / safe_name
    content = file.file.read()
    file_path.write_bytes(content)
    return str(file_path), sha256_file(file_path)


def create_property_with_documents(
    db: Session,
    owner: User,
    payload: PropertyCreate,
    sale_deed: UploadFile,
    encumbrance_certificate: UploadFile,
    property_tax_receipt: UploadFile,
    identity_proof: UploadFile,
) -> Property:
    if owner.role.value != "property_owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only property owners can create listings")

    if not all([sale_deed, encumbrance_certificate, property_tax_receipt, identity_proof]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="All mandatory verification documents are required")

    price_per_share = payload.property_price / payload.total_shares

    property_item = Property(
        owner_id=owner.id,
        title=payload.title,
        description=payload.description,
        city=payload.city,
        state=payload.state,
        location=payload.location,
        property_type=payload.property_type,
        image_url=payload.image_url,
        property_price=payload.property_price,
        total_shares=payload.total_shares,
        available_shares=payload.total_shares,
        price_per_share=price_per_share,
        rental_yield=payload.rental_yield,
        demand_index=payload.demand_index,
        market_trend=payload.market_trend,
        ai_predicted_roi=payload.ai_predicted_roi,
        risk_level=payload.risk_level,
        listing_status=ListingStatus.PENDING,
        is_verified=False,
    )
    db.add(property_item)
    db.flush()

    file_map = {
        DocumentType.SALE_DEED: sale_deed,
        DocumentType.ENCUMBRANCE_CERTIFICATE: encumbrance_certificate,
        DocumentType.PROPERTY_TAX_RECEIPT: property_tax_receipt,
        DocumentType.IDENTITY_PROOF: identity_proof,
    }

    for doc_type, file in file_map.items():
        path, file_hash = _save_pdf(file, property_item.id, doc_type)
        db.add(
            Document(
                property_id=property_item.id,
                document_type=doc_type,
                file_name=file.filename or f"{doc_type.value}.pdf",
                file_path=path,
                sha256_hash=file_hash,
                mime_type=file.content_type or "application/pdf",
            )
        )

    db.commit()
    db.refresh(property_item)
    return property_item


def list_properties(
    db: Session,
    city: Optional[str] = None,
    property_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    min_roi: Optional[float] = None,
    max_roi: Optional[float] = None,
    search: Optional[str] = None,
) -> list[Property]:
    q = db.query(Property).filter(Property.listing_status == ListingStatus.APPROVED, Property.is_verified.is_(True))

    if city:
        city_lower = city.strip().lower()
        if city_lower == "hyderabad":
            q = q.filter(
                (Property.city.ilike("%hyderabad%"))
                | (Property.location.ilike("%hyderabad%"))
                | (Property.state.ilike("%telangana%"))
            )
        else:
            q = q.filter(Property.city.ilike(f"%{city}%"))
    if property_type:
        try:
            q = q.filter(Property.property_type == PropertyType(property_type))
        except ValueError:
            pass
    if risk_level:
        q = q.filter(Property.risk_level == risk_level)
    if min_roi is not None:
        q = q.filter(Property.ai_predicted_roi >= min_roi)
    if max_roi is not None:
        q = q.filter(Property.ai_predicted_roi <= max_roi)
    if search:
        text = f"%{search}%"
        q = q.filter((Property.title.ilike(text)) | (Property.location.ilike(text)) | (Property.city.ilike(text)))

    return q.order_by(Property.created_at.desc()).all()


def get_property_or_404(db: Session, property_id: int) -> Property:
    property_item = db.query(Property).filter(Property.id == property_id).first()
    if not property_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return property_item
