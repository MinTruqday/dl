import os
from datetime import datetime, timezone
from uuid import uuid5, NAMESPACE_DNS

from pymongo import MongoClient
from redis import Redis

from src.core.security.access import get_password_hash


PASSWORD = "Veriq-E2E-Password-2026"
ACCOUNTS = (
    ("qa-lead", "e2e-qa-lead@example.com", "reader", "QA Lead E2E"),
    ("tester", "e2e-tester@example.com", "reader", "Kiểm thử viên E2E"),
    ("business-analyst", "e2e-ba@example.com", "reader", "Chuyên viên phân tích E2E"),
    ("developer", "e2e-developer@example.com", "reader", "Lập trình viên E2E"),
    ("viewer", "e2e-viewer@example.com", "reader", "Viewer E2E"),
    ("admin", "e2e-admin@example.com", "admin", "Quản trị E2E"),
)
PROJECT_ID = "PRJ-FRONTEND-ROLE-AUDIT"
PROJECT_ROLES = {
    "qa-lead": "QA_LEAD",
    "tester": "TESTER",
    "business-analyst": "BA",
    "developer": "DEVELOPER",
    "viewer": "VIEWER",
}


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
                "system_role": "ADMIN" if role == "admin" else "USER",
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

testing_database = client[os.environ.get("TESTING_DB_NAME", "veriq_testing")]
lead_id = str(uuid5(NAMESPACE_DNS, "e2e-qa-lead@example.com"))
testing_database.projects.update_one(
    {"_id": PROJECT_ID},
    {
        "$set": {
            "key": "ROLEAUDIT",
            "name": "Kiểm thử giao diện theo vai trò",
            "description": "Dự án cục bộ dùng để xác minh quyền và giao diện của từng vai trò",
            "project_type": "web",
            "locale": "vi-VN",
            "timezone": "Asia/Ho_Chi_Minh",
            "settings": {},
            "created_by": lead_id,
            "status": "active",
            "revision": 1,
            "updated_at": now,
        },
        "$setOnInsert": {"created_at": now},
    },
    upsert=True,
)
for slug, email, _, _ in ACCOUNTS:
    if slug not in PROJECT_ROLES:
        continue
    user_id = str(uuid5(NAMESPACE_DNS, email))
    testing_database.project_members.update_one(
        {"project_id": PROJECT_ID, "user_id": user_id},
        {
            "$set": {
                "project_role": PROJECT_ROLES[slug],
                "status": "ACTIVE",
                "membership_revision": 1,
                "created_by": lead_id,
                "updated_at": now,
            },
            "$setOnInsert": {
                "_id": str(uuid5(NAMESPACE_DNS, f"{PROJECT_ID}:{user_id}")),
                "created_at": now,
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
