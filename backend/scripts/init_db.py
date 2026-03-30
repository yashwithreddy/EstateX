from app.db.mongo import ensure_indexes
from app.db.session import get_database


if __name__ == "__main__":
    db = get_database()
    db.command("ping")
    ensure_indexes(db)
    print("MongoDB indexes ensured.")
