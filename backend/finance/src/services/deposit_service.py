import hashlib
import hmac
import json
import random
from datetime import datetime, timezone

import httpx
from core.config import settings
from core.database import db_client
from fastapi import HTTPException, Response
from loguru import logger
from src.schemas.wallet_schema import Transaction, TransactionType


class DepositService:

    @staticmethod
    def _generate_payos_signature(data: dict, db=None) -> str:
        sorted_keys = sorted(data.keys())
        raw = "&".join((f"{k}={data[k]}" for k in sorted_keys))
        return hmac.new(
            settings.PAYOS_CHECKSUM_KEY.encode("utf-8"),
            raw.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    async def create_deposit_link(req, current_user, db=None):
        if req.amount < 1000:
            raise HTTPException(
                status_code=400, detail="The minimum deposit amount is 1,000 VND"
            )

        if db is None:
            db = db_client.mongodb.get_default_database()

        while True:
            order_code = random.randint(100000000, 2147483647)
            if not await db["orders"].find_one({"order_code": order_code}):
                break

        description = f"DL{order_code}"
        if len(description) > 25:
            description = description[:25]

        frontend_url = getattr(settings, "PAYOS_RETURN_URL", "").rstrip("/")
        return_url = f"{frontend_url}/?orderCode={order_code}"
        cancel_url = f"{frontend_url}/?orderCode={order_code}&cancel=true"

        signature_data = {
            "amount": req.amount,
            "cancelUrl": cancel_url,
            "description": description,
            "orderCode": order_code,
            "returnUrl": return_url,
        }
        signature = DepositService._generate_payos_signature(signature_data)

        payload = {
            "orderCode": order_code,
            "amount": req.amount,
            "description": description,
            "items": [
                {
                    "name": f"Deposit {req.amount} VND into wallet",
                    "quantity": 1,
                    "price": req.amount,
                }
            ],
            "cancelUrl": cancel_url,
            "returnUrl": return_url,
            "signature": signature,
        }

        await db["orders"].insert_one(
            {
                "order_code": order_code,
                "user_id": str(current_user.id),
                "amount": req.amount,
                "dl": req.amount // 1000,
                "gateway": "PAYOS",
                "status": "INIT",
                "payment_link_id": None,
                "created_at": datetime.now(timezone.utc),
            }
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.PAYOS_API_URL,
                    json=payload,
                    headers={
                        "x-client-id": settings.PAYOS_CLIENT_ID,
                        "x-api-key": settings.PAYOS_API_KEY,
                        "Content-Type": "application/json",
                    },
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
            res_data = response.json()
            if res_data.get("code") == "00":
                checkout_url = res_data["data"]["checkoutUrl"]
                await db["orders"].update_one(
                    {"order_code": order_code},
                    {
                        "$set": {
                            "status": "pending",
                            "payment_link_id": res_data["data"].get("paymentLinkId"),
                        }
                    },
                )
                return {"checkout_url": checkout_url, "order_code": order_code}
            else:
                logger.error("Failed to generate payment link")
                await db["orders"].update_one(
                    {"order_code": order_code}, {"$set": {"status": "FAILED"}}
                )
                raise HTTPException(
                    status_code=400,
                    detail=res_data.get("desc", "Failed to initialize payment gateway"),
                )
        except HTTPException:
            raise
        except Exception as e:
            await db["orders"].update_one(
                {"order_code": order_code}, {"$set": {"status": "FAILED"}}
            )
            logger.exception("Failed to connect to the payment gateway")
            raise HTTPException(
                status_code=500, detail="Payment gateway connection failed"
            )

    @staticmethod
    async def deposit_webhook(request, db=None):
        data = await request.json()
        logger.info("Received notification from payment gateway")
        if data.get("code") == "00" and data.get("data"):
            webhook_data = data["data"]
            order_code = webhook_data.get("orderCode")
            signature_data = {
                "amount": webhook_data.get("amount"),
                "cancelUrl": webhook_data.get("cancelUrl", ""),
                "description": webhook_data.get("description", ""),
                "orderCode": order_code,
                "returnUrl": webhook_data.get("returnUrl", ""),
            }
            try:
                received_signature = data.get("signature", "")
                if not received_signature:
                    logger.warning("Missing authentication signature in notification")
                    raise HTTPException(
                        status_code=400, detail="Missing digital signature for authentication"
                    )

                expected_signature = DepositService._generate_payos_signature(
                    signature_data
                )
                if received_signature != expected_signature:
                    logger.warning("Authentication signature mismatch")
                    raise HTTPException(
                        status_code=400, detail="Invalid digital signature"
                    )

                paid_amount = webhook_data.get("amount", 0)
                await DepositService.process_success_order(order_code, paid_amount)
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Failed to process payment gateway notification")
        return Response(
            content=json.dumps({"code": "00", "desc": "success"}),
            media_type="application/json",
            status_code=200,
        )

    @staticmethod
    async def verify_deposit(order_code: int, current_user, db=None):
        if db is None:
            db = db_client.mongodb.get_default_database()

        order = await db["orders"].find_one({"order_code": order_code})
        if not order:
            raise HTTPException(status_code=404, detail="The specified transaction could not be found")
        if order.get("user_id") != str(current_user.id):
            raise HTTPException(
                status_code=403, detail="You do not have permission to view this transaction"
            )

        if getattr(db_client, "redis", None):
            rl_key = f"rl:verify_deposit:{current_user.id}"
            try:
                attempts = await db_client.redis.incr(rl_key)
                if attempts == 1:
                    await db_client.redis.expire(rl_key, 60)
                if attempts > 10:
                    raise HTTPException(
                        status_code=429,
                        detail="Too many requests. Please try again in 1 minute",
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Rate limit exceeded. Please try again later")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.PAYOS_API_URL}/{order_code}",
                    headers={
                        "x-client-id": settings.PAYOS_CLIENT_ID,
                        "x-api-key": settings.PAYOS_API_KEY,
                    },
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
            res_data = response.json()
            if res_data.get("code") == "00":
                payment_data = res_data.get("data", {})
                status = payment_data.get("status", "UNKNOWN")
                if status == "PAID":
                    await DepositService.process_success_order(
                        order_code, payment_data.get("amountPaid", 0)
                    )
                return {
                    "order_code": order_code,
                    "status": status,
                    "amount": payment_data.get("amount", 0),
                    "amount_paid": payment_data.get("amountPaid", 0),
                }
            else:
                raise HTTPException(
                    status_code=400, detail="Failed to verify payment status"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Failed to verify transaction")
            raise HTTPException(
                status_code=500, detail="Failed to verify payment status"
            )

    @staticmethod
    async def process_success_order(
        order_code: int, paid_amount: int = None, db=None, session=None
    ):
        should_close_session = False
        if db is None:
            db = db_client.mongodb.get_default_database()

        if session is None:
            session = await db_client.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        orders = db["orders"]
        wallets = db["wallets"]
        transactions = db["transactions"]

        order = await orders.find_one(
            {"order_code": order_code, "status": {"$in": ["INIT", "pending"]}}
        )
        if not order:
            logger.warning(f"Order {order_code} could not be found or has already been processed")
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            return

        if paid_amount is not None and paid_amount < order.get("amount", 0):
            logger.warning(
                f"Payment amount {paid_amount} for order {order_code} is insufficient"
            )
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            return

        dl_to_add = order.get("dl", 0)
        user_id = order["user_id"]

        try:
            result = await orders.update_one(
                {"order_code": order_code, "status": {"$in": ["INIT", "pending"]}},
                {
                    "$set": {
                        "status": "success",
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
                session=session,
            )
            if result.modified_count != 1:
                if should_close_session:
                    await session.abort_transaction()
                logger.warning(f"Failed to update the status of order {order_code}")
                return
            await wallets.update_one(
                {"_id": user_id},
                {"$inc": {"balance": dl_to_add}},
                upsert=True,
                session=session,
            )
            tx = Transaction(
                user_id=user_id,
                type=TransactionType.TOPUP,
                amount=dl_to_add,
                note=f"Deposit via payOS: {order['amount']} VND",
            )
            await transactions.insert_one(tx.model_dump(by_alias=True), session=session)

            if should_close_session:
                await session.commit_transaction()

            try:
                import httpx
                from core.config import settings

                if settings.SIGNAL_URL:
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"{settings.SIGNAL_URL}/thong-bao/kich-hoat",
                            json={
                                "target_user_id": user_id,
                                "title": "Deposit processed successfully",
                                "body": f"Account credited with {dl_to_add} dl",
                                "type": "topup",
                            },
                            timeout=settings.DEFAULT_HTTP_TIMEOUT,
                        )
            except Exception as e:
                logger.warning("Failed to dispatch notification")
            logger.info(
                f"Credited {dl_to_add} dl to user {user_id} for order {order_code}"
            )
        except Exception as e:
            if should_close_session:
                await session.abort_transaction()
            logger.exception(f"Failed to process order {order_code}")
            raise HTTPException(status_code=500, detail="Service temporarily unavailable")
        finally:
            if should_close_session:
                await session.end_session()
