from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    wallet_address: Optional[str] = Field(default=None, pattern=r"^0x[a-fA-F0-9]{40}$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    wallet_address: Optional[str]

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
