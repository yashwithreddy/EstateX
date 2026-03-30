from datetime import datetime

from fastapi import HTTPException, status
from pymongo import ReturnDocument
from pymongo.database import Database

from app.core.security import create_access_token, hash_password, verify_password
from app.db.mongo import get_next_sequence, serialize_doc
from app.models import UserRole
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, WalletUpdateRequest


def _user_out(doc: dict) -> dict:
    return {
        "id": doc["id"],
        "email": doc["email"],
        "full_name": doc["full_name"],
        "role": doc["role"],
        "wallet_address": doc.get("wallet_address"),
        "wallet_balance": float(doc.get("wallet_balance", 0)),
    }


def register_user(db: Database, payload: UserCreate) -> TokenResponse:
    if payload.role == UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role cannot be self-registered")

    existing = db.users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user_id = get_next_sequence(db, "users")
    user_doc = {
        "_id": user_id,
        "email": payload.email.lower(),
        "full_name": payload.full_name,
        "hashed_password": hash_password(payload.password),
        "role": payload.role.value,
        "wallet_address": payload.wallet_address,
        "wallet_balance": 0.0,
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    db.users.insert_one(user_doc)

    token = create_access_token(subject=str(user_id), role=payload.role.value)
    return TokenResponse(access_token=token, user=_user_out(serialize_doc(user_doc)))


def login_user(db: Database, payload: LoginRequest) -> TokenResponse:
    user_doc = db.users.find_one({"email": payload.email.lower(), "is_active": True})
    if not user_doc or not verify_password(payload.password, user_doc["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user_doc = serialize_doc(user_doc)
    token = create_access_token(subject=str(user_doc["id"]), role=user_doc["role"])
    return TokenResponse(access_token=token, user=_user_out(user_doc))


def update_wallet_address(db: Database, user: dict, payload: WalletUpdateRequest) -> dict:
    updated = db.users.find_one_and_update(
        {"_id": user["id"]},
        {"$set": {"wallet_address": payload.wallet_address}},
        return_document=ReturnDocument.AFTER,
    )
    return serialize_doc(updated)
