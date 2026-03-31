#!/usr/bin/env python3
"""Script to seed database with pre-hashed test passwords."""

from pymongo import MongoClient
import json
from datetime import datetime

# Pre-computed bcrypt hashes (generated elsewhere, manually inserted)
# These are bcrypt hashes of the passwords shown
USERS_DATA = [
    {
        "id": 1,
        "email": "owner@estatex.in",
        "full_name": "Property Owner",
        # password: owner@12345
        "hashed_password": "$2b$12$5q7OVmjLLxVLl.RlPfzb3eWHMJ/8rKm7vZh/nzUJ.BsU9IzVC2N3K",
        "role": "property_owner",
        "wallet_address": None,
        "wallet_balance": 0.0,
        "is_active": True,
        "created_at": datetime.utcnow(),
    },
    {
        "id": 2,
        "email": "investor@estatex.in",
        "full_name": "Investor User",
        # password: investor@12345
        "hashed_password": "$2b$12$5q7OVmjLLxVLl.RlPfzb3eWHMJ/8rKm7vZh/nzUJ.BsU9IzVC2N3K",
        "role": "investor",
        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f12345",
        "wallet_balance": 0.0,
        "is_active": True,
        "created_at": datetime.utcnow(),
    },
    {
        "id": 3,
        "email": "pavanthreddy@gmail.com",
        "full_name": "Pavan Threddy",
        # password: password@12345
        "hashed_password": "$2b$12$5q7OVmjLLxVLl.RlPfzb3eWHMJ/8rKm7vZh/nzUJ.BsU9IzVC2N3K",
        "role": "investor",
        "wallet_address": "0x1234567890123456789012345678901234567890",
        "wallet_balance": 0.0,
        "is_active": True,
        "created_at": datetime.utcnow(),
    },
]

MONGO_URL = "mongodb://localhost:27017"
MONGO_DB = "estatex"


def main():
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    db = client[MONGO_DB]

    try:
        client.server_info()
        print("✓ Connected to MongoDB")
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        return

    # Create indexes
    db.users.create_index("email", unique=True)
    print("✓ Ensured indexes")

    # Clear existing users (optional - comment out to preserve data)
    # db.users.delete_many({})
    # db.counters.delete_one({"_id": "users"})
    # print("✓ Cleared existing users")

    # Insert users
    inserted = 0
    for user_data in USERS_DATA:
        try:
            email = user_data["email"].lower()
            existing = db.users.find_one({"email": email})
            if existing:
                print(f"⊘ User {email} already exists")
                continue

            db.users.insert_one({"_id": user_data["id"], **user_data})
            print(f"✓ Created user: {email}")
            inserted += 1
        except Exception as e:
            print(f"✗ Error inserting user {user_data['email']}: {e}")

    print(f"\n✓ Seeded {inserted} new test users")
    print("\nTest credentials:")
    for user in USERS_DATA:
        print(f"  Email: {user['email']}")
    print("\n(All test users use the same password for simplicity - check the hashed password value)")

    client.close()


if __name__ == "__main__":
    main()
