from pathlib import Path

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Document, DocumentType, ListingStatus, Property, PropertyType, RiskLevel, User, UserRole
from app.utils.hash_utils import sha256_file


def write_sample_pdf(path: Path, title: str) -> None:
    content = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]/Contents 4 0 R>>endobj\n"
        b"4 0 obj<</Length 44>>stream\n"
        + f"BT /F1 12 Tf 10 100 Td ({title}) Tj ET".encode("utf-8")
        + b"\nendstream endobj\n"
        b"xref\n0 5\n0000000000 65535 f \n"
        b"trailer<</Size 5/Root 1 0 R>>\nstartxref\n300\n%%EOF"
    )
    path.write_bytes(content)


def main() -> None:
    db = SessionLocal()
    uploads = Path("uploads")
    uploads.mkdir(exist_ok=True)

    db.query(Document).delete()
    db.query(Property).delete()
    db.query(User).delete()
    db.commit()

    admin = User(
        email="admin@estatex.in",
        full_name="EstateX India Admin",
        hashed_password=hash_password("Admin@123"),
        role=UserRole.ADMIN,
        wallet_address="0x000000000000000000000000000000000000dEaD",
    )
    owner = User(
        email="owner@estatex.in",
        full_name="Priya Property Owner",
        hashed_password=hash_password("Owner@123"),
        role=UserRole.PROPERTY_OWNER,
        wallet_address="0x1111111111111111111111111111111111111111",
    )
    investor = User(
        email="investor@estatex.in",
        full_name="Arjun Investor",
        hashed_password=hash_password("Investor@123"),
        role=UserRole.INVESTOR,
        wallet_address="0x2222222222222222222222222222222222222222",
    )
    db.add_all([admin, owner, investor])
    db.flush()

    properties_data = [
        {"title": "Hyderabad IT Park", "city": "Hyderabad", "state": "Telangana", "type": PropertyType.OFFICE, "price": 185000000, "yield": 8.2, "roi": 14.8, "risk": RiskLevel.LOW, "img": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab"},
        {"title": "Mumbai Commercial Tower", "city": "Mumbai", "state": "Maharashtra", "type": PropertyType.COMMERCIAL, "price": 320000000, "yield": 7.6, "roi": 13.5, "risk": RiskLevel.MEDIUM, "img": "https://images.unsplash.com/photo-1460317442991-0ec209397118"},
        {"title": "Bangalore Tech Plaza", "city": "Bengaluru", "state": "Karnataka", "type": PropertyType.OFFICE, "price": 210000000, "yield": 7.9, "roi": 14.2, "risk": RiskLevel.LOW, "img": "https://images.unsplash.com/photo-1497366216548-37526070297c"},
        {"title": "Pune Co-working Hub", "city": "Pune", "state": "Maharashtra", "type": PropertyType.OFFICE, "price": 98000000, "yield": 8.8, "roi": 15.1, "risk": RiskLevel.MEDIUM, "img": "https://images.unsplash.com/photo-1497366754035-f200968a6e72"},
        {"title": "Chennai Retail Mall", "city": "Chennai", "state": "Tamil Nadu", "type": PropertyType.RETAIL, "price": 270000000, "yield": 7.4, "roi": 12.9, "risk": RiskLevel.MEDIUM, "img": "https://images.unsplash.com/photo-1441986300917-64674bd600d8"},
        {"title": "Delhi Office Complex", "city": "New Delhi", "state": "Delhi", "type": PropertyType.COMMERCIAL, "price": 295000000, "yield": 7.3, "roi": 13.1, "risk": RiskLevel.MEDIUM, "img": "https://images.unsplash.com/photo-1524758631624-e2822e304c36"},
        {"title": "Ahmedabad Industrial Space", "city": "Ahmedabad", "state": "Gujarat", "type": PropertyType.COMMERCIAL, "price": 122000000, "yield": 8.6, "roi": 14.0, "risk": RiskLevel.LOW, "img": "https://images.unsplash.com/photo-1504307651254-35680f356dfd"},
        {"title": "Noida Fintech Tower", "city": "Noida", "state": "Uttar Pradesh", "type": PropertyType.OFFICE, "price": 176000000, "yield": 8.0, "roi": 14.4, "risk": RiskLevel.LOW, "img": "https://images.unsplash.com/photo-1541888946425-d81bb19240f5"},
        {"title": "Gurgaon Business Bay", "city": "Gurugram", "state": "Haryana", "type": PropertyType.COMMERCIAL, "price": 245000000, "yield": 7.7, "roi": 13.6, "risk": RiskLevel.MEDIUM, "img": "https://images.unsplash.com/photo-1518005020951-eccb494ad742"},
        {"title": "Kolkata Riverside Residency", "city": "Kolkata", "state": "West Bengal", "type": PropertyType.RESIDENTIAL, "price": 86000000, "yield": 6.4, "roi": 11.2, "risk": RiskLevel.MEDIUM, "img": "https://images.unsplash.com/photo-1560185007-cde436f6a4d0"},
        {"title": "Jaipur Retail Arcade", "city": "Jaipur", "state": "Rajasthan", "type": PropertyType.RETAIL, "price": 74000000, "yield": 8.9, "roi": 14.9, "risk": RiskLevel.MEDIUM, "img": "https://images.unsplash.com/photo-1577415124269-fc1140a69e91"},
        {"title": "Lucknow Office Suites", "city": "Lucknow", "state": "Uttar Pradesh", "type": PropertyType.OFFICE, "price": 69000000, "yield": 8.1, "roi": 13.8, "risk": RiskLevel.MEDIUM, "img": "https://images.unsplash.com/photo-1479839672679-a46483c0e7c8"},
        {"title": "Indore Logistics Center", "city": "Indore", "state": "Madhya Pradesh", "type": PropertyType.COMMERCIAL, "price": 97000000, "yield": 9.2, "roi": 15.6, "risk": RiskLevel.LOW, "img": "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d"},
        {"title": "Kochi Waterfront Offices", "city": "Kochi", "state": "Kerala", "type": PropertyType.OFFICE, "price": 83000000, "yield": 7.8, "roi": 13.3, "risk": RiskLevel.LOW, "img": "https://images.unsplash.com/photo-1597047084897-51e81819a499"},
        {"title": "Surat Textile Plaza", "city": "Surat", "state": "Gujarat", "type": PropertyType.COMMERCIAL, "price": 101000000, "yield": 8.5, "roi": 14.5, "risk": RiskLevel.MEDIUM, "img": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40"},
        {"title": "Nagpur Metro Residency", "city": "Nagpur", "state": "Maharashtra", "type": PropertyType.RESIDENTIAL, "price": 58000000, "yield": 6.7, "roi": 11.8, "risk": RiskLevel.HIGH, "img": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c"},
        {"title": "Bhopal Office District", "city": "Bhopal", "state": "Madhya Pradesh", "type": PropertyType.OFFICE, "price": 72000000, "yield": 8.0, "roi": 13.1, "risk": RiskLevel.MEDIUM, "img": "https://images.unsplash.com/photo-1497215728101-856f4ea42174"},
        {"title": "Visakhapatnam Port Hub", "city": "Visakhapatnam", "state": "Andhra Pradesh", "type": PropertyType.COMMERCIAL, "price": 93000000, "yield": 8.7, "roi": 14.7, "risk": RiskLevel.LOW, "img": "https://images.unsplash.com/photo-1511818966892-d7d671e672a2"},
        {"title": "Coimbatore Retail Galleria", "city": "Coimbatore", "state": "Tamil Nadu", "type": PropertyType.RETAIL, "price": 66000000, "yield": 8.3, "roi": 13.5, "risk": RiskLevel.MEDIUM, "img": "https://images.unsplash.com/photo-1472851294608-062f824d29cc"},
        {"title": "Patna IT Offices", "city": "Patna", "state": "Bihar", "type": PropertyType.OFFICE, "price": 62000000, "yield": 7.9, "roi": 12.8, "risk": RiskLevel.HIGH, "img": "https://images.unsplash.com/photo-1554435493-93422e8b5f0f"},
        {"title": "Thane Residential Heights", "city": "Thane", "state": "Maharashtra", "type": PropertyType.RESIDENTIAL, "price": 115000000, "yield": 6.9, "roi": 12.2, "risk": RiskLevel.MEDIUM, "img": "https://images.unsplash.com/photo-1568605114967-8130f3a36994"},
        {"title": "Mysuru Business Plaza", "city": "Mysuru", "state": "Karnataka", "type": PropertyType.COMMERCIAL, "price": 81000000, "yield": 8.4, "roi": 13.9, "risk": RiskLevel.LOW, "img": "https://images.unsplash.com/photo-1484154218962-a197022b5858"},
    ]

    for idx, item in enumerate(properties_data):
        total_shares = int(item["price"] / 1000)
        prop = Property(
            owner_id=owner.id,
            title=item["title"],
            description=f"Premium {item['type'].value} asset in {item['city']} with strong rental demand and appreciation potential.",
            city=item["city"],
            state=item["state"],
            location=f"{item['city']}, {item['state']}",
            property_type=item["type"],
            image_url=item["img"] + "?auto=format&fit=crop&w=1200&q=80",
            property_price=item["price"],
            total_shares=total_shares,
            available_shares=int(total_shares * 0.92),
            price_per_share=1000.0,
            rental_yield=item["yield"],
            demand_index=min(0.95, max(0.35, item["yield"] / 10)),
            market_trend=min(0.95, max(0.30, item["roi"] / 20)),
            ai_predicted_roi=item["roi"],
            risk_level=item["risk"],
            listing_status=ListingStatus.APPROVED if idx < 20 else ListingStatus.PENDING,
            is_verified=idx < 20,
        )
        db.add(prop)
        db.flush()

        for doc_type in [
            DocumentType.SALE_DEED,
            DocumentType.ENCUMBRANCE_CERTIFICATE,
            DocumentType.PROPERTY_TAX_RECEIPT,
            DocumentType.IDENTITY_PROOF,
        ]:
            file_path = uploads / f"seed_{prop.id}_{doc_type.value}.pdf"
            write_sample_pdf(file_path, f"{prop.title} {doc_type.value}")
            db.add(
                Document(
                    property_id=prop.id,
                    document_type=doc_type,
                    file_name=file_path.name,
                    file_path=str(file_path),
                    sha256_hash=sha256_file(file_path),
                    mime_type="application/pdf",
                    is_verified=idx < 20,
                    verified_by_admin_id=admin.id if idx < 20 else None,
                )
            )

    db.commit()
    db.close()
    print("Seed data inserted with 20+ Indian properties.")


if __name__ == "__main__":
    main()
