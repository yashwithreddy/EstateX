import logging

from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.db.session import get_db
from app.deps import get_current_user
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserOut, WalletUpdateRequest
from app.services.auth_service import login_user, register_user, update_wallet_address

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=TokenResponse)
def register(payload: UserCreate, db: Database = Depends(get_db)):
    logger.info("register email=%s role=%s", payload.email, payload.role)
    return register_user(db, payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Database = Depends(get_db)):
    logger.info("login email=%s", payload.email)
    return login_user(db, payload)


@router.get("/me", response_model=UserOut)
def get_me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user


@router.put("/wallet", response_model=UserOut)
def update_wallet(
    payload: WalletUpdateRequest,
    db: Database = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update the wallet address for the current user."""
    logger.info("update_wallet user_id=%s", current_user["id"])
    return update_wallet_address(db, current_user, payload)
