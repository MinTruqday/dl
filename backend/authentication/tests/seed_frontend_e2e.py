import os
from datetime import datetime, timezone
from uuid import uuid5, NAMESPACE_DNS

from pymongo import MongoClient
from redis import Redis

from src.core.security.access import get_password_hash


PASSWORD = "DocLib-E2E-Password-2026"
ACCOUNTS = (
    ("teacher", "e2e-teacher@example.com", "author", "Giáo viên E2E"),
    ("student", "e2e-student@example.com", "reader", "Học sinh E2E"),
    ("admin", "e2e-admin@example.com", "admin", "Quản trị E2E"),
)


client = MongoClient(os.environ["MONGODB_URI"])
database = client[os.environ["AUTHENTICATION_DB_NAME"]]
now = datetime.now(timezone.utc)
password_hash = get_password_hash(PASSWORD)
database.auth_credentials.delete_many(
    {
        "$or": [
            {"slug": {"$in": [account[0] for account in ACCOUNTS]}},
            {"email": {"$in": [account[1] for account in ACCOUNTS]}},
        ]
    }
)

for slug, email, role, full_name in ACCOUNTS:
    account_id = str(uuid5(NAMESPACE_DNS, email))
    database.auth_credentials.update_one(
        {"email": email},
        {
            "$set": {
                "email": email,
                "slug": slug,
                "full_name": full_name,
                "role": role,
                "permissions": [],
                "is_active": True,
                "password_hash": password_hash,
                "passkeys": [],
                "updated_at": now,
            },
            "$setOnInsert": {
                "_id": account_id,
                "created_at": now,
                "bio": None,
                "avatar_url": None,
                "social_links": {},
                "pinned_documents": [],
                "bookmarks": [],
                "is_shadowbanned": False,
                "donation_link": None,
                "kyc_status": "NONE",
                "creator_status": "NONE",
                "is_verified": True,
                "storage_limit": 20 * 1024 * 1024 * 1024,
                "tos_accepted_at": now,
                "blocked_users": [],
                "settings": {
                    "mod_notifs": True,
                    "auto_refresh": False,
                    "auto_save": True,
                    "default_visibility": "private",
                },
            },
        },
        upsert=True,
    )

client.close()
redis = Redis.from_url(os.environ["REDIS_URI"])
rate_limit_keys = list(redis.scan_iter("rate_limit:*"))
if rate_limit_keys:
    redis.delete(*rate_limit_keys)
redis.close()
print("Frontend E2E identities are ready")
