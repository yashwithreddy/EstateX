from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AdminApprovalRequest(BaseModel):
    approve: bool
    rejection_reason: Optional[str] = None


class PendingDocumentOut(BaseModel):
    document_id: int
    property_id: int
    property_title: str
    document_type: str
    sha256_hash: str
    uploaded_at: datetime
    verification_status: str
