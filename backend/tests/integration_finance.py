import asyncio
import os
import secrets
from datetime import datetime, timezone

import httpx
import jwt
import redis.asyncio as redis_async
from motor.motor_asyncio import AsyncIOMotorClient

from src.services.deposit import DepositService


async def run():
    suffix = secrets.token_hex(5)
    buyer_id = f"finance-buyer-{suffix}"
    seller_id = f"finance-seller-{suffix}"
    admin_id = f"finance-admin-{suffix}"
    document_id = f"finance-document-{suffix}"
    order_code = secrets.randbelow(1_000_000_000) + 1_000_000_000
    secret = os.environ["SECRET_KEY"]
    mongo = AsyncIOMotorClient(os.environ["MONGODB_URI"])
    finance_db = mongo[os.getenv("FINANCE_DB_NAME", "doclib_finance")]
    content_db = mongo[os.getenv("CONTENT_DB_NAME", "doclib_content")]
    humanity_db = mongo[os.getenv("HUMANITY_DB_NAME", "doclib_humanity")]
    usage_db = mongo[os.getenv("USAGE_DB_NAME", "doclib_usage")]
    notification_db = mongo[os.getenv("NOTIFICATION_DB_NAME", "doclib_notification")]
    redis_client = redis_async.from_url(os.environ["REDIS_URI"], decode_responses=True)

    def token(user_id, email, role, session_id):
        return jwt.encode(
            {
                "sub": email,
                "uid": user_id,
                "sid": session_id,
                "role": role,
                "permissions": [],
                "ai_tier": "BASIC",
                "exp": datetime.now(timezone.utc).timestamp() + 1800,
            },
            secret,
            algorithm="HS256",
        )

    sessions = {
        buyer_id: f"session-{buyer_id}",
        seller_id: f"session-{seller_id}",
        admin_id: f"session-{admin_id}",
    }
    for user_id, session_id in sessions.items():
        await redis_client.sadd(f"user_sessions:{user_id}", session_id)
    await humanity_db.users.insert_many(
        [
            {"_id": buyer_id, "email": f"{buyer_id}@example.com", "full_name": "Finance Buyer", "slug": buyer_id, "role": "reader", "is_active": True},
            {"_id": seller_id, "email": f"{seller_id}@example.com", "full_name": "Finance Seller", "slug": seller_id, "role": "author", "is_active": True},
            {"_id": admin_id, "email": f"{admin_id}@example.com", "full_name": "Finance Admin", "slug": admin_id, "role": "admin", "is_active": True},
        ]
    )
    await content_db.documents.insert_one(
        {
            "_id": document_id,
            "title": "Finance Integration Document",
            "slug": f"finance-integration-{suffix}",
            "creator_id": seller_id,
            "status": "published",
            "visibility": "public",
            "is_deleted": False,
            "price_dl": 100,
        }
    )
    await finance_db.wallets.insert_many(
        [
            {"_id": buyer_id, "balance": 1000, "withdrawable_balance": 0},
            {"_id": seller_id, "balance": 0, "withdrawable_balance": 0},
        ]
    )
    buyer_headers = {"Authorization": f"Bearer {token(buyer_id, f'{buyer_id}@example.com', 'reader', sessions[buyer_id])}"}
    seller_headers = {"Authorization": f"Bearer {token(seller_id, f'{seller_id}@example.com', 'author', sessions[seller_id])}"}
    admin_headers = {"Authorization": f"Bearer {token(admin_id, f'{admin_id}@example.com', 'admin', sessions[admin_id])}"}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            unauthorized_notification = await client.post(
                "http://notification:8000/thong-bao/gui-di",
                json={"target_user_id": buyer_id, "title": "Blocked", "body": "Blocked request", "type": "test"},
            )
            assert unauthorized_notification.status_code == 403, unauthorized_notification.text

            purchases = await asyncio.gather(
                client.post(
                    "http://finance:8000/kiem-tien/mua/tai-lieu",
                    json={"document_id": document_id},
                    headers=buyer_headers,
                ),
                client.post(
                    "http://finance:8000/kiem-tien/mua/tai-lieu",
                    json={"document_id": document_id},
                    headers=buyer_headers,
                ),
            )
            assert all(response.status_code == 200 for response in purchases), [response.text for response in purchases]
            statuses = sorted(response.json()["data"]["status"] for response in purchases)
            assert statuses == ["owned", "purchased"], statuses
            buyer_wallet = await finance_db.wallets.find_one({"_id": buyer_id})
            seller_wallet = await finance_db.wallets.find_one({"_id": seller_id})
            assert buyer_wallet["balance"] == 900, buyer_wallet
            assert seller_wallet["balance"] == 100, seller_wallet
            assert seller_wallet["withdrawable_balance"] == 100, seller_wallet
            assert await finance_db.purchases.count_documents({"user_id": buyer_id, "document_id": document_id, "status": "ACTIVE"}) == 1

            membership = await client.post(
                "http://finance:8000/kiem-tien/thanh-vien",
                json={"tier": "PRO"},
                headers=buyer_headers,
            )
            assert membership.status_code == 200, membership.text
            subscription = await usage_db.subscriptions.find_one({"user_id": buyer_id})
            assert subscription["ai_tier"] == "PRO", subscription
            buyer_wallet = await finance_db.wallets.find_one({"_id": buyer_id})
            assert buyer_wallet["balance"] == 150, buyer_wallet

            await finance_db.orders.insert_one(
                {
                    "order_code": order_code,
                    "user_id": buyer_id,
                    "amount": 5000,
                    "dl": 5,
                    "gateway": "PAYOS",
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc),
                }
            )
            webhook_data = {
                "orderCode": order_code,
                "amount": 5000,
                "description": f"DL{order_code}",
                "accountNumber": "12345678",
                "reference": f"REF{suffix}",
                "transactionDateTime": "2026-07-23 10:00:00",
                "currency": "VND",
                "paymentLinkId": f"link-{suffix}",
                "code": "00",
                "desc": "Thành công",
                "counterAccountBankId": "",
                "counterAccountBankName": "",
                "counterAccountName": "",
                "counterAccountNumber": "",
                "virtualAccountName": "",
                "virtualAccountNumber": "",
            }
            signature = DepositService._generate_payos_signature(webhook_data)
            webhook = await client.post(
                "http://finance:8000/nap-tien/webhook/payos",
                json={"code": "00", "desc": "success", "success": True, "data": webhook_data, "signature": signature},
            )
            assert webhook.status_code == 200, webhook.text
            repeated = await client.post(
                "http://finance:8000/nap-tien/webhook/payos",
                json={"code": "00", "desc": "success", "success": True, "data": webhook_data, "signature": signature},
            )
            assert repeated.status_code == 200, repeated.text
            buyer_wallet = await finance_db.wallets.find_one({"_id": buyer_id})
            assert buyer_wallet["balance"] == 155, buyer_wallet

            withdrawal = await client.post(
                "http://finance:8000/rut-tien",
                json={"amount": 50, "bank_info": "BANK-1234567890", "note": "Integration withdrawal"},
                headers=seller_headers,
            )
            assert withdrawal.status_code == 201, withdrawal.text
            withdrawal_id = withdrawal.json()["data"]["withdrawal_id"]
            cancelled = await client.post(
                f"http://finance:8000/rut-tien/{withdrawal_id}/huy",
                headers=seller_headers,
            )
            assert cancelled.status_code == 200, cancelled.text
            seller_wallet = await finance_db.wallets.find_one({"_id": seller_id})
            assert seller_wallet["balance"] == 100 and seller_wallet["withdrawable_balance"] == 100, seller_wallet

            second_withdrawal = await client.post(
                "http://finance:8000/rut-tien",
                json={"amount": 50, "bank_info": "BANK-1234567890"},
                headers=seller_headers,
            )
            assert second_withdrawal.status_code == 201, second_withdrawal.text
            second_id = second_withdrawal.json()["data"]["withdrawal_id"]
            rejected = await client.post(
                f"http://finance:8000/rut-tien/{second_id}/xac-minh",
                params={"action": "reject", "reason": "Thông tin ngân hàng chưa hợp lệ"},
                headers=admin_headers,
            )
            assert rejected.status_code == 200, rejected.text
            seller_wallet = await finance_db.wallets.find_one({"_id": seller_id})
            assert seller_wallet["balance"] == 100 and seller_wallet["withdrawable_balance"] == 100, seller_wallet

            await asyncio.sleep(3)
            notifications = await notification_db.notifications.count_documents(
                {"target_user_id": {"$in": [buyer_id, seller_id]}}
            )
            assert notifications == 3, notifications
            assert await finance_db.outbox_events.count_documents({"status": "done"}) >= 3
            print("finance integration passed")
    finally:
        await finance_db.wallets.delete_many({"_id": {"$in": [buyer_id, seller_id, admin_id]}})
        await finance_db.transactions.delete_many({"user_id": {"$in": [buyer_id, seller_id, admin_id]}})
        await finance_db.purchases.delete_many({"user_id": buyer_id})
        await finance_db.orders.delete_many({"user_id": buyer_id})
        await finance_db.withdrawal_requests.delete_many({"user_id": seller_id})
        outbox = await finance_db.outbox_events.find({"payload.target_user_id": {"$in": [buyer_id, seller_id]}}).to_list(length=None)
        await finance_db.outbox_events.delete_many({"_id": {"$in": [row["_id"] for row in outbox]}})
        await content_db.documents.delete_one({"_id": document_id})
        await humanity_db.users.delete_many({"_id": {"$in": [buyer_id, seller_id, admin_id]}})
        await usage_db.subscriptions.delete_one({"user_id": buyer_id})
        await notification_db.notifications.delete_many({"target_user_id": {"$in": [buyer_id, seller_id]}})
        for user_id in sessions:
            await redis_client.delete(f"user_sessions:{user_id}")
        await redis_client.aclose()
        mongo.close()


asyncio.run(run())
