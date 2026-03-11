import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import require_roles
from app.db.session import get_db
from app.models import User, UserRole
from app.services.dashboard_service import admin_dashboard, investor_dashboard, owner_dashboard

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])
logger = logging.getLogger(__name__)


@router.get("/investor")
def get_investor_dashboard(
    db: Session = Depends(get_db),
    investor: User = Depends(require_roles(UserRole.INVESTOR)),
):
    logger.info("get_investor_dashboard investor_id=%s", investor.id)
    return investor_dashboard(db, investor.id)


@router.get("/owner")
def get_owner_dashboard(
    db: Session = Depends(get_db),
    owner: User = Depends(require_roles(UserRole.PROPERTY_OWNER)),
):
    logger.info("get_owner_dashboard owner_id=%s", owner.id)
    return owner_dashboard(db, owner.id)


@router.get("/admin")
def get_admin_dashboard(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    logger.info("get_admin_dashboard admin_id=%s", admin.id)
    return admin_dashboard(db)
