import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import Property, PropertyType, User, UserRole
from app.schemas.property import PropertyCreate, PropertyOut
from app.services.property_service import create_property_with_documents, get_property_or_404, list_properties

router = APIRouter(prefix="/api/v1/properties", tags=["properties"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[PropertyOut])
def get_public_properties(
    city: Optional[str] = None,
    property_type: Optional[PropertyType] = None,
    risk_level: Optional[str] = None,
    min_roi: Optional[float] = None,
    max_roi: Optional[float] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    logger.info("get_public_properties city=%s type=%s risk=%s", city, property_type, risk_level)
    return list_properties(db, city, property_type.value if property_type else None, risk_level, min_roi, max_roi, search)


@router.get("/{property_id}", response_model=PropertyOut)
def get_property_detail(property_id: int, db: Session = Depends(get_db)):
    logger.info("get_property_detail property_id=%s", property_id)
    return get_property_or_404(db, property_id)


@router.post("", response_model=PropertyOut)
def create_property(
    title: str = Form(...),
    description: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    location: str = Form(...),
    property_type: PropertyType = Form(...),
    image_url: Optional[str] = Form(None),
    property_price: float = Form(...),
    total_shares: int = Form(...),
    rental_yield: float = Form(...),
    demand_index: float = Form(...),
    market_trend: float = Form(...),
    ai_predicted_roi: float = Form(...),
    risk_level: str = Form(...),
    sale_deed: Optional[UploadFile] = File(None),
    encumbrance_certificate: Optional[UploadFile] = File(None),
    property_tax_receipt: Optional[UploadFile] = File(None),
    identity_proof: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    owner: User = Depends(require_roles(UserRole.PROPERTY_OWNER)),
):
    logger.info("create_property owner_id=%s", owner.id)
    if not all([sale_deed, encumbrance_certificate, property_tax_receipt, identity_proof]):
        raise HTTPException(
            status_code=400,
            detail="All mandatory documents (sale deed, encumbrance certificate, tax receipt, identity proof) are required.",
        )

    payload = PropertyCreate(
        title=title,
        description=description,
        city=city,
        state=state,
        location=location,
        property_type=property_type,
        image_url=image_url,
        property_price=property_price,
        total_shares=total_shares,
        rental_yield=rental_yield,
        demand_index=demand_index,
        market_trend=market_trend,
        ai_predicted_roi=ai_predicted_roi,
        risk_level=risk_level,
    )
    return create_property_with_documents(
        db,
        owner,
        payload,
        sale_deed,
        encumbrance_certificate,
        property_tax_receipt,
        identity_proof,
    )


@router.get("/me/listings", response_model=list[PropertyOut])
def my_listings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    logger.info("my_listings user_id=%s", user.id)
    return db.query(Property).filter(Property.owner_id == user.id).order_by(Property.created_at.desc()).all()
