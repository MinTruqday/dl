import pymongo
from datetime import datetime, timezone
import uuid

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://mongodb:27017/")
db = client["doclib"]
users = db["users"]
messages = db["messages"]

# Fetch users
user1 = users.find_one()
if not user1:
    print("No users found in database.")
    exit()

# We need two users. Let's just create a dummy one if there's only one.
user2 = users.find_one({"_id": {"$ne": user1["_id"]}})
if not user2:
    user2_id = str(uuid.uuid4())
    users.insert_one({
        "_id": user2_id,
        "username": "tester_bot",
        "email": "tester@example.com",
        "full_name": "QA Tester",
        "role": "user"
    })
    user2 = users.find_one({"_id": user2_id})

u1_id = user1["_id"]
u2_id = user2["_id"]

# Seed some messages
msgs = [
    {
        "_id": str(uuid.uuid4()),
        "sender_id": u2_id,
        "receiver_id": u1_id,
        "content": "Chào bạn, mình test giao diện chat tí nhé!",
        "is_read": True,
        "is_pinned": False,
        "reactions": [],
        "created_at": datetime.now(timezone.utc)
    },
    {
        "_id": str(uuid.uuid4()),
        "sender_id": u1_id,
        "receiver_id": u2_id,
        "content": "Ok, thấy giao diện này ổn chưa?",
        "is_read": True,
        "is_pinned": False,
        "reactions": [],
        "created_at": datetime.now(timezone.utc)
    },
    {
        "_id": str(uuid.uuid4()),
        "sender_id": u2_id,
        "receiver_id": u1_id,
        "content": "Quá tuyệt vời, rất đúng với thiết kế phẳng và bo góc!",
        "is_read": False,
        "is_pinned": False,
        "reactions": [],
        "created_at": datetime.now(timezone.utc)
    }
]

messages.insert_many(msgs)
print(f"Seeded 3 messages between {user1.get('full_name')} and {user2.get('full_name')}")
