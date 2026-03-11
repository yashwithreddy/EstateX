import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PROPERTY_OWNER = "property_owner"
    INVESTOR = "investor"


class ListingStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PropertyType(str, enum.Enum):
    COMMERCIAL = "commercial"
    RESIDENTIAL = "residential"
    RETAIL = "retail"
    OFFICE = "office"


class RiskLevel(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class DocumentType(str, enum.Enum):
    SALE_DEED = "sale_deed"
    ENCUMBRANCE_CERTIFICATE = "encumbrance_certificate"
    PROPERTY_TAX_RECEIPT = "property_tax_receipt"
    IDENTITY_PROOF = "identity_proof"


class TransactionType(str, enum.Enum):
    PRIMARY_BUY = "primary_buy"
    SECONDARY_SELL = "secondary_sell"
    SECONDARY_BUY = "secondary_buy"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    wallet_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    properties = relationship("Property", back_populates="owner")
    ownerships = relationship("Ownership", back_populates="investor")


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    property_type: Mapped[PropertyType] = mapped_column(Enum(PropertyType), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    property_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    total_shares: Mapped[int] = mapped_column(Integer, nullable=False)
    available_shares: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_share: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    rental_yield: Mapped[float] = mapped_column(Float, default=6.0)
    demand_index: Mapped[float] = mapped_column(Float, default=0.5)
    market_trend: Mapped[float] = mapped_column(Float, default=0.5)
    ai_predicted_roi: Mapped[float] = mapped_column(Float, default=10.0)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), default=RiskLevel.MEDIUM)

    listing_status: Mapped[ListingStatus] = mapped_column(Enum(ListingStatus), default=ListingStatus.DRAFT)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    contract_property_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="properties")
    documents = relationship("Document", back_populates="property", cascade="all, delete-orphan")
    ownerships = relationship("Ownership", back_populates="property", cascade="all, delete-orphan")
    listings = relationship("ShareListing", back_populates="property", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by_admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="documents")


class Ownership(Base):
    __tablename__ = "ownerships"
    __table_args__ = (UniqueConstraint("property_id", "investor_id", name="uq_property_investor"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)
    investor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    shares: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property = relationship("Property", back_populates="ownerships")
    investor = relationship("User", back_populates="ownerships")


class ShareListing(Base):
    __tablename__ = "share_listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    shares_for_sale: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_share: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="listings")


class InvestmentTransaction(Base):
    __tablename__ = "investment_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), nullable=False)
    buyer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    seller_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    shares: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    tx_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    onchain_tx_hash: Mapped[Optional[str]] = mapped_column(String(66), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
