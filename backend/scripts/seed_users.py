import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import db_client, init_db, close_db
from core.config import settings
from core.security import get_password_hash
from models.user import UserInDB, RoleEnum

async def seed_users():
    print("Starting user seeding...")
    await init_db()
    
    db = db_client.mongodb[settings.MONGODB_DB_NAME]
    users_col = db["users"]
    
    # Clear existing test users
    test_emails = [
        "admin@doclib.com", 
        "moderator@doclib.com", 
        "author@doclib.com", 
        "reader@doclib.com", 
        "potential@doclib.com"
    ]
    await users_col.delete_many({"email": {"$in": test_emails}})
    print("Cleared existing test users.")

    test_password_hash = get_password_hash("test@123")
    
    users_to_create = [
        {
            "email": "admin@doclib.com",
            "full_name": "DocLib Administrator",
            "slug": "admin",
            "role": RoleEnum.ADMIN,
            "password_hash": test_password_hash,
            "wallet_balance": 1000000,
            "bio": "Hệ thống quản trị DocLib.",
            "is_verified": True
        },
        {
            "email": "moderator@doclib.com",
            "full_name": "Content Moderator",
            "slug": "moderator",
            "role": RoleEnum.MODERATOR,
            "password_hash": test_password_hash,
            "wallet_balance": 50000,
            "bio": "Chuyên viên kiểm duyệt nội dung.",
            "is_verified": True
        },
        {
            "email": "author@doclib.com",
            "full_name": "Creative Author",
            "slug": "author",
            "role": RoleEnum.AUTHOR,
            "password_hash": test_password_hash,
            "wallet_balance": 20000,
            "bio": "Tác giả sáng tạo nội dung tri thức.",
            "is_verified": True
        },
        {
            "email": "reader@doclib.com",
            "full_name": "Active Reader",
            "slug": "reader",
            "role": RoleEnum.READER,
            "password_hash": test_password_hash,
            "wallet_balance": 10000,
            "bio": "Độc giả đam mê tri thức.",
            "is_verified": True
        },
        {
            "email": "potential@doclib.com",
            "full_name": "Potential Author",
            "slug": "potential",
            "role": RoleEnum.POTENTIAL_AUTHOR,
            "password_hash": test_password_hash,
            "wallet_balance": 0,
            "bio": "Người dùng đang chờ xét duyệt làm tác giả.",
            "is_verified": True
        }
    ]
    
    for user_data in users_to_create:
        # Create UserInDB instance to ensure UUID _id is a string
        user_obj = UserInDB(**user_data)
        user_dict = user_obj.model_dump(by_alias=True)
        
        await users_col.insert_one(user_dict)
        print(f"Created user: {user_data['email']} (ID: {user_dict['_id']}, Role: {user_data['role']})")
    
    print("User seeding completed successfully.")
    await close_db()

if __name__ == "__main__":
    asyncio.run(seed_users())
