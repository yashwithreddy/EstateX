import io
import os
from pathlib import Path

from fastapi.testclient import TestClient

# Must be set before importing app modules
SMOKE_DB_PATH = Path("/tmp/estatex_smoke.db")
if SMOKE_DB_PATH.exists():
    SMOKE_DB_PATH.unlink()

os.environ.setdefault("DATABASE_URL", f"sqlite:///{SMOKE_DB_PATH}")
os.environ.setdefault("JWT_SECRET_KEY", "smoke-secret")
os.environ.setdefault("BLOCKCHAIN_ENABLED", "false")
os.environ.setdefault("UPLOADS_DIR", "uploads")

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User, UserRole  # noqa: E402


def ensure_admin_user() -> None:
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@estatex.com").first()
        if admin:
            return
        db.add(
            User(
                email="admin@estatex.com",
                full_name="Admin User",
                hashed_password=hash_password("Admin@123"),
                role=UserRole.ADMIN,
                wallet_address="0x000000000000000000000000000000000000dEaD",
            )
        )
        db.commit()
    finally:
        db.close()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def make_pdf_bytes(label: str) -> bytes:
    return (
        b"%PDF-1.4\n"
        + f"% {label}\n".encode()
        + b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        + b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        + b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]/Contents 4 0 R>>endobj\n"
        + b"4 0 obj<</Length 44>>stream\nBT /F1 12 Tf 10 100 Td (EstateX) Tj ET\nendstream endobj\n"
        + b"xref\n0 5\n0000000000 65535 f \ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n300\n%%EOF"
    )


def run_smoke() -> None:
    ensure_admin_user()

    client = TestClient(app)

    # Register users
    owner_reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "owner.smoke@estatex.com",
            "full_name": "Owner Smoke",
            "password": "Owner@123",
            "role": "owner",
            "wallet_address": "0x1111111111111111111111111111111111111111",
        },
    )
    assert owner_reg.status_code == 200, owner_reg.text
    owner_token = owner_reg.json()["access_token"]

    investor1_reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "investor1.smoke@estatex.com",
            "full_name": "Investor One",
            "password": "Investor@123",
            "role": "investor",
            "wallet_address": "0x2222222222222222222222222222222222222222",
        },
    )
    assert investor1_reg.status_code == 200, investor1_reg.text
    investor1_token = investor1_reg.json()["access_token"]

    investor2_reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "investor2.smoke@estatex.com",
            "full_name": "Investor Two",
            "password": "Investor@123",
            "role": "investor",
            "wallet_address": "0x3333333333333333333333333333333333333333",
        },
    )
    assert investor2_reg.status_code == 200, investor2_reg.text
    investor2_token = investor2_reg.json()["access_token"]

    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@estatex.com", "password": "Admin@123"},
    )
    assert admin_login.status_code == 200, admin_login.text
    admin_token = admin_login.json()["access_token"]

    # Owner uploads property with mandatory PDFs
    files = {
        "title_document": ("title.pdf", io.BytesIO(make_pdf_bytes("title")), "application/pdf"),
        "ownership_document": ("ownership.pdf", io.BytesIO(make_pdf_bytes("ownership")), "application/pdf"),
    }
    data = {
        "title": "Smoke Test Property",
        "description": "Prime asset for smoke testing end-to-end business workflows.",
        "location": "Dallas, TX",
        "property_price": "500000",
        "total_shares": "5000",
        "rental_yield": "7.1",
        "demand_index": "0.74",
        "market_trend": "0.69",
    }
    created = client.post("/api/v1/properties", headers=auth_header(owner_token), data=data, files=files)
    assert created.status_code == 200, created.text
    property_id = created.json()["id"]

    # Should not be public before verification
    public_before = client.get("/api/v1/properties")
    assert public_before.status_code == 200
    assert all(p["id"] != property_id for p in public_before.json())

    # Unauthorized role check
    forbidden_admin = client.get("/api/v1/admin/documents/pending", headers=auth_header(investor1_token))
    assert forbidden_admin.status_code == 403

    # Admin verifies documents (both required)
    pending = client.get("/api/v1/admin/documents/pending", headers=auth_header(admin_token))
    assert pending.status_code == 200, pending.text
    pending_docs = [d for d in pending.json() if d["property_id"] == property_id]
    assert len(pending_docs) == 2, pending.json()

    for doc in pending_docs:
        verified = client.patch(
            f"/api/v1/admin/documents/{doc['document_id']}/verify",
            headers=auth_header(admin_token),
            json={"approve": True},
        )
        assert verified.status_code == 200, verified.text

    # Should now be publicly listed
    public_after = client.get("/api/v1/properties")
    assert public_after.status_code == 200
    assert any(p["id"] == property_id for p in public_after.json())

    # Primary investment
    primary_buy = client.post(
        "/api/v1/investments/buy",
        headers=auth_header(investor1_token),
        json={
            "property_id": property_id,
            "shares": 100,
            "wallet_address": "0x2222222222222222222222222222222222222222",
        },
    )
    assert primary_buy.status_code == 200, primary_buy.text

    # Oversell prevention
    oversell = client.post(
        "/api/v1/investments/buy",
        headers=auth_header(investor1_token),
        json={
            "property_id": property_id,
            "shares": 999999,
            "wallet_address": "0x2222222222222222222222222222222222222222",
        },
    )
    assert oversell.status_code == 400

    # Liquidity listing and secondary buy
    list_for_sale = client.post(
        "/api/v1/investments/list",
        headers=auth_header(investor1_token),
        json={
            "property_id": property_id,
            "shares_for_sale": 10,
            "price_per_share": 125,
        },
    )
    assert list_for_sale.status_code == 200, list_for_sale.text
    listing_id = list_for_sale.json()["id"]

    trade = client.post(
        "/api/v1/investments/trade",
        headers=auth_header(investor2_token),
        json={
            "listing_id": listing_id,
            "shares_to_buy": 5,
            "buyer_wallet_address": "0x3333333333333333333333333333333333333333",
        },
    )
    assert trade.status_code == 200, trade.text

    # AI endpoints
    ai_payload = {
        "property_price": 500000,
        "rental_yield": 7.1,
        "demand_index": 0.74,
        "market_trend": 0.69,
    }
    roi = client.post("/api/v1/ai/roi", json=ai_payload)
    assert roi.status_code == 200, roi.text
    risk = client.post("/api/v1/ai/risk", json=ai_payload)
    assert risk.status_code == 200, risk.text
    explain = client.post("/api/v1/ai/explain", json=ai_payload)
    assert explain.status_code == 200, explain.text

    # Dashboards
    investor_dash = client.get("/api/v1/dashboard/investor", headers=auth_header(investor1_token))
    assert investor_dash.status_code == 200, investor_dash.text

    admin_dash = client.get("/api/v1/dashboard/admin", headers=auth_header(admin_token))
    assert admin_dash.status_code == 200, admin_dash.text

    print("SMOKE TEST PASSED")
    print("Property ID:", property_id)
    print("Primary Tx:", primary_buy.json())
    print("Secondary Tx:", trade.json())
    print("ROI:", roi.json())
    print("Risk:", risk.json())


if __name__ == "__main__":
    run_smoke()
