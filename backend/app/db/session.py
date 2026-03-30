from pymongo import MongoClient
from pymongo.database import Database

from app.core.config import settings

_client = MongoClient(settings.mongo_url, serverSelectionTimeoutMS=5000)
_db = _client[settings.mongo_db]


def get_database() -> Database:
    return _db


def get_db():
    yield _db
