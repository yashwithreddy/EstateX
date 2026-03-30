import enum
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
