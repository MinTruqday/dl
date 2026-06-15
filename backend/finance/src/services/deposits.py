import hashlib
import hmac
import json
import random
import httpx
from datetime import datetime, timezone
from core.config import settings
from core.database import db_client
from fastapi import HTTPException, Response
from loguru import logger
from src.schemas.finance import Transaction, TransactionType

class DepositService:

    @staticmethod
    def _generate_payos_signature(data: dict) -> str:
        sorted_keys = sorted(data.keys())
        raw = "&".join((f"{k}={data[k]}" for k in sorted_keys))
        return hmac.new(
            settings.PAYOS_CHECKSUM_KEY.encode("utf-8"),
            raw.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    async def create_deposit_link(req, current_user, db=None) -> dict:
        if req.amount < 1000:
            raise HTTPException(status_code=400, detail="Requested deposit amount falls below minimum required threshold for processing system")

        target_db = db or db_client.mongodb.get_default_database()

        while True:
            order_code = random.randint(100000000, 2147483647)
            if not await target_db["orders"].find_one({"order_code": order_code}):
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
            "items": [{"name": "Deposit transaction into digital wallet", "quantity": 1, "price": req.amount}],
            "cancelUrl": cancel_url,
            "returnUrl": return_url,
            "signature": signature,
        }

        await target_db["orders"].insert_one(
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
                await target_db["orders"].update_one(
                    {"order_code": order_code},
                    {"$set": {"status": "pending", "payment_link_id": res_data["data"].get("paymentLinkId")}},
                )
                return {"checkout_url": checkout_url, "order_code": order_code}
                
            logger.error("External payment gateway rejected request to generate secure financial transaction link")
            await target_db["orders"].update_one({"order_code": order_code}, {"$set": {"status": "FAILED"}})
            raise HTTPException(status_code=400, detail="Electronic payment gateway failed to initialize requested transaction session")
        except HTTPException:
            raise
        except Exception:
            await target_db["orders"].update_one({"order_code": order_code}, {"$set": {"status": "FAILED"}})
            logger.error("System encountered network failure attempting to communicate with electronic payment gateway")
            raise HTTPException(status_code=500, detail="System unable to establish secure connection with external payment processing provider")

    @staticmethod
    async def deposit_webhook(request, db=None) -> Response:
        data = await request.json()
        logger.info("System successfully received status update notification from external payment gateway")
        
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
                    logger.warning("Incoming gateway notification rejected due to missing cryptographic authentication signature")
                    raise HTTPException(status_code=400, detail="Transaction verification failed because cryptographic signature is missing")

                expected_signature = DepositService._generate_payos_signature(signature_data)
                if received_signature != expected_signature:
                    logger.warning("Incoming gateway notification rejected because cryptographic signature did not match expected value")
                    raise HTTPException(status_code=400, detail="Transaction verification failed because provided cryptographic signature is invalid")

                paid_amount = webhook_data.get("amount", 0)
                await DepositService.process_success_order(order_code, paid_amount)
            except HTTPException:
                raise
            except Exception:
                logger.error("System encountered unexpected structural failure while processing payment gateway callback")
                
        return Response(content=json.dumps({"code": "00", "desc": "success"}), media_type="application/json", status_code=200)

    @staticmethod
    async def verify_deposit(order_code: int, current_user, db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        order = await target_db["orders"].find_one({"order_code": order_code})
        
        if not order:
            raise HTTPException(status_code=404, detail="System unable to locate deposit transaction matching provided gateway reference identifier")
        if order.get("user_id") != str(current_user.id):
            raise HTTPException(status_code=403, detail="Current account lacks required authorization to view details of specific transaction")

        if getattr(db_client, "redis", None):
            rl_key = f"rl:verify_deposit:{current_user.id}"
            try:
                attempts = await db_client.redis.incr(rl_key)
                if attempts == 1:
                    await db_client.redis.expire(rl_key, 60)
                if attempts > 10:
                    raise HTTPException(status_code=429, detail="System temporarily throttled your requests so please wait moment before trying again")
            except HTTPException:
                raise
            except Exception:
                logger.warning("Transaction verification request throttled due to excessive recent inquiries")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.PAYOS_API_URL}/{order_code}",
                    headers={"x-client-id": settings.PAYOS_CLIENT_ID, "x-api-key": settings.PAYOS_API_KEY},
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
            res_data = response.json()
            if res_data.get("code") == "00":
                payment_data = res_data.get("data", {})
                status = payment_data.get("status", "UNKNOWN")
                if status == "PAID":
                    await DepositService.process_success_order(order_code, payment_data.get("amountPaid", 0))
                return {
                    "order_code": order_code,
                    "status": status,
                    "amount": payment_data.get("amount", 0),
                    "amount_paid": payment_data.get("amountPaid", 0),
                }
            raise HTTPException(status_code=400, detail="System unable to successfully verify current status of payment transaction")
        except HTTPException:
            raise
        except Exception:
            logger.error("Unexpected disruption occurred attempting to verify transaction status with external provider")
            raise HTTPException(status_code=500, detail="System unable to successfully verify current status of payment transaction")

    @staticmethod
    async def process_success_order(order_code: int, paid_amount: int = None, db=None, session=None):
        should_close_session = False
        target_db = db or db_client.mongodb.get_default_database()

        if session is None:
            session = await db_client.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        orders = target_db["orders"]
        wallets = target_db["wallets"]
        transactions = target_db["transactions"]

        order = await orders.find_one({"order_code": order_code, "status": {"$in": ["INIT", "pending"]}})
        if not order:
            logger.warning("Designated deposit order could not be located or has already been fully processed")
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            return

        if paid_amount is not None and paid_amount < order.get("amount", 0):
            logger.warning("Verified payment amount is insufficient to fulfill requested deposit order")
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            return

        dl_to_add = order.get("dl", 0)
        user_id = order["user_id"]

        try:
            result = await orders.update_one(
                {"order_code": order_code, "status": {"$in": ["INIT", "pending"]}},
                {"$set": {"status": "success", "updated_at": datetime.now(timezone.utc)}},
                session=session,
            )
            if result.modified_count != 1:
                if should_close_session:
                    await session.abort_transaction()
                logger.warning("Database engine encountered issue attempting to update status of deposit order")
                return
                
            await wallets.update_one({"_id": user_id}, {"$inc": {"balance": dl_to_add}}, upsert=True, session=session)
            tx = Transaction(
                user_id=user_id,
                type=TransactionType.TOPUP,
                amount=dl_to_add,
                note="Deposit successfully processed via electronic payment gateway",
            )
            await transactions.insert_one(tx.model_dump(by_alias=True), session=session)

            if should_close_session:
                await session.commit_transaction()

            try:
                if settings.SIGNAL_URL:
                    async with httpx.AsyncClient() as client:
                        await client.post(
                            f"{settings.SIGNAL_URL}/notifications/dispatch",
                            json={
                                "target_user_id": user_id,
                                "title": "Deposit processed successfully",
                                "body": "Requested deposit funds have been successfully credited to digital wallet",
                                "type": "topup",
                            },
                            timeout=settings.DEFAULT_HTTP_TIMEOUT,
                        )
            except Exception:
                logger.warning("System encountered minor disruption attempting to dispatch deposit success notification")
                
            logger.info("Deposited funds have been successfully verified and credited to designated account wallet")
        except Exception:
            if should_close_session:
                await session.abort_transaction()
            logger.error("Unexpected error occurred attempting to finalize deposit transaction and update digital balance")
            raise HTTPException(status_code=500, detail="Financial service is undergoing routine maintenance and cannot process request")
        finally:
            if should_close_session:
                await session.end_session()