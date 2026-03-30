import secrets
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from pymongo.database import Database

from app.core.config import settings
from app.db.mongo import get_next_sequence, serialize_doc, serialize_docs, utc_now
from app.models import DocumentType, ListingStatus, PropertyType
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


def _hydrate_property(db: Database, prop: dict) -> dict:
    documents = list(db.documents.find({"property_id": prop["id"]}).sort("created_at", -1))
    prop["documents"] = serialize_docs(documents)
    return prop


def create_property_with_documents(
    db: Database,
    owner: dict,
    payload: PropertyCreate,
    sale_deed: UploadFile,
    encumbrance_certificate: UploadFile,
    property_tax_receipt: UploadFile,
    identity_proof: UploadFile,
) -> dict:
    if owner["role"] != "property_owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only property owners can create listings")

    if not all([sale_deed, encumbrance_certificate, property_tax_receipt, identity_proof]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="All mandatory verification documents are required")

    price_per_share = payload.property_price / payload.total_shares

    property_id = get_next_sequence(db, "properties")
    property_doc = {
        "_id": property_id,
        "owner_id": owner["id"],
        "title": payload.title,
        "description": payload.description,
        "city": payload.city,
        "state": payload.state,
        "location": payload.location,
        "property_type": payload.property_type.value,
        "image_url": payload.image_url,
        "property_price": payload.property_price,
        "total_shares": payload.total_shares,
        "available_shares": payload.total_shares,
        "price_per_share": price_per_share,
        "rental_yield": payload.rental_yield,
        "demand_index": payload.demand_index,
        "market_trend": payload.market_trend,
        "ai_predicted_roi": payload.ai_predicted_roi,
        "risk_level": payload.risk_level.value,
        "listing_status": ListingStatus.PENDING.value,
        "is_verified": False,
        "rejection_reason": None,
        "contract_property_id": None,
        "created_at": utc_now(),
    }
    db.properties.insert_one(property_doc)

    file_map = {
        DocumentType.SALE_DEED: sale_deed,
        DocumentType.ENCUMBRANCE_CERTIFICATE: encumbrance_certificate,
        DocumentType.PROPERTY_TAX_RECEIPT: property_tax_receipt,
        DocumentType.IDENTITY_PROOF: identity_proof,
    }

    document_docs = []
    for doc_type, file in file_map.items():
        path, file_hash = _save_pdf(file, property_id, doc_type)
        document_id = get_next_sequence(db, "documents")
        document_docs.append(
            {
                "_id": document_id,
                "property_id": property_id,
                "document_type": doc_type.value,
                "file_name": file.filename or f"{doc_type.value}.pdf",
                "file_path": path,
                "sha256_hash": file_hash,
                "mime_type": file.content_type or "application/pdf",
                "is_verified": False,
                "verified_by_admin_id": None,
                "created_at": utc_now(),
            }
        )

    if document_docs:
        db.documents.insert_many(document_docs)

    return _hydrate_property(db, serialize_doc(property_doc))


def list_properties(
    db: Database,
    city: Optional[str] = None,
    property_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    min_roi: Optional[float] = None,
    max_roi: Optional[float] = None,
    search: Optional[str] = None,
) -> list[dict]:
    query: dict = {"listing_status": ListingStatus.APPROVED.value, "is_verified": True}

    if city:
        city_lower = city.strip().lower()
        if city_lower == "hyderabad":
            query["$or"] = [
                {"city": {"$regex": "hyderabad", "$options": "i"}},
                {"location": {"$regex": "hyderabad", "$options": "i"}},
                {"state": {"$regex": "telangana", "$options": "i"}},
            ]
        else:
            query["city"] = {"$regex": city, "$options": "i"}
    if property_type:
        try:
            query["property_type"] = PropertyType(property_type).value
        except ValueError:
            pass
    if risk_level:
        query["risk_level"] = risk_level
    if min_roi is not None:
        query.setdefault("ai_predicted_roi", {})["$gte"] = min_roi
    if max_roi is not None:
        query.setdefault("ai_predicted_roi", {})["$lte"] = max_roi
    if search:
        query.setdefault("$or", []).extend(
            [
                {"title": {"$regex": search, "$options": "i"}},
                {"location": {"$regex": search, "$options": "i"}},
                {"city": {"$regex": search, "$options": "i"}},
            ]
        )
    docs = list(db.properties.find(query).sort("created_at", -1))
    return [_hydrate_property(db, serialize_doc(doc)) for doc in docs]


def get_property_or_404(db: Database, property_id: int) -> dict:
    property_doc = db.properties.find_one({"_id": property_id})
    if not property_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return _hydrate_property(db, serialize_doc(property_doc))
