from core.config import settings
import hmac
import hashlib
import json
import httpx
from datetime import datetime, timezone
from fastapi import HTTPException, Response
from core.database import db_client
from models.wallet import Transaction, TransactionType
from loguru import logger


class DepositService:
    @staticmethod
    def _generate_payos_signature(data: dict) -> str:
        sorted_keys = sorted(data.keys())
        raw = "&".join(f"{k}={data[k]}" for k in sorted_keys)
        return hmac.new(
            settings.PAYOS_CHECKSUM_KEY.encode("utf-8"),
            raw.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    async def create_deposit_link(req, current_user):
        if req.amount < 2000:
            raise HTTPException(status_code=400, detail="Số tiền nạp tối thiểu là 2.000 VNĐ")

        order_code = int(datetime.now(timezone.utc).timestamp() * 1000) % 2147483647

        description = f"DL{order_code}"
        if len(description) > 25:
            description = description[:25]

        frontend_url = settings.PAYOS_RETURN_URL.rstrip("/")
        return_url = f"{frontend_url}?orderCode={order_code}"
        cancel_url = f"{frontend_url}?orderCode={order_code}&cancel=true"

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
                    "name": f"Nạp {req.amount} VNĐ vào ví DocLib",
                    "quantity": 1,
                    "price": req.amount,
                }
            ],
            "cancelUrl": cancel_url,
            "returnUrl": return_url,
            "signature": signature,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api-merchant.payos.vn/v2/payment-requests",
                    json=payload,
                    headers={
                        "x-client-id": settings.PAYOS_CLIENT_ID,
                        "x-api-key": settings.PAYOS_API_KEY,
                        "Content-Type": "application/json",
                    },
                    timeout=15,
                )
            res_data = response.json()

            if res_data.get("code") == "00":
                checkout_url = res_data["data"]["checkoutUrl"]
                db = db_client.mongodb.get_default_database()
                await db["orders"].insert_one(
                    {
                        "order_code": order_code,
                        "user_id": str(current_user.id),
                        "amount": req.amount,
                        "dl": req.amount // 1000,
                        "gateway": "PAYOS",
                        "status": "pending",
                        "payment_link_id": res_data["data"].get("paymentLinkId"),
                        "created_at": datetime.now(timezone.utc),
                    }
                )
                return {"checkout_url": checkout_url, "order_code": order_code}
            else:
                logger.error(f"payOS create payment failed: {res_data}")
                raise HTTPException(
                    status_code=400,
                    detail=res_data.get("desc", "Lỗi khởi tạo thanh toán payOS"),
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"payOS connection error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Không thể kết nối với hệ thống thanh toán. Vui lòng thử lại sau.",
            )

    @staticmethod
    async def deposit_webhook(request):
        data = await request.json()
        logger.info(f"Received payOS webhook: {json.dumps(data, default=str)}")

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
                    logger.warning("payOS webhook missing signature")

                await DepositService.process_success_order(order_code)
            except Exception as e:
                logger.error(f"payOS webhook processing error: {e}")

        return Response(
            content=json.dumps({"code": "00", "desc": "success"}),
            media_type="application/json",
            status_code=200,
        )

    @staticmethod
    async def verify_deposit(order_code: int):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api-merchant.payos.vn/v2/payment-requests/{order_code}",
                    headers={
                        "x-client-id": settings.PAYOS_CLIENT_ID,
                        "x-api-key": settings.PAYOS_API_KEY,
                    },
                    timeout=10,
                )
            res_data = response.json()

            if res_data.get("code") == "00":
                payment_data = res_data.get("data", {})
                status = payment_data.get("status", "UNKNOWN")

                if status == "PAID":
                    await DepositService.process_success_order(order_code)

                return {
                    "order_code": order_code,
                    "status": status,
                    "amount": payment_data.get("amount", 0),
                    "amount_paid": payment_data.get("amountPaid", 0),
                }
            else:
                raise HTTPException(status_code=400, detail="Không thể kiểm tra trạng thái thanh toán")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"payOS verify error: {e}")
            raise HTTPException(status_code=500, detail="Lỗi kiểm tra trạng thái thanh toán")

    @staticmethod
    async def process_success_order(order_code: int):
        db = db_client.mongodb.get_default_database()
        orders = db["orders"]
        users = db["users"]
        transactions = db["transactions"]

        order = await orders.find_one({"order_code": order_code, "status": "pending"})
        if not order:
            logger.warning(f"Order {order_code} not found or already processed")
            return

        dl_to_add = order.get("dl", 0)
        user_id = order["user_id"]

        session = await db_client.mongodb.start_session()
        try:
            async with session.start_transaction():
                result = await orders.update_one(
                    {"order_code": order_code, "status": "pending"},
                    {"$set": {"status": "success", "updated_at": datetime.now(timezone.utc)}},
                    session=session,
                )

                if result.modified_count != 1:
                    await session.abort_transaction()
                    logger.warning(f"Order {order_code} status update failed (already processed?)")
                    return

                await users.update_one(
                    {"_id": user_id},
                    {"$inc": {"wallet_balance": dl_to_add}},
                    session=session,
                )

                tx = Transaction(
                    user_id=user_id,
                    type=TransactionType.TOPUP,
                    amount=dl_to_add,
                    note=f"Nạp tiền qua payOS: {order['amount']} VNĐ",
                )
                await transactions.insert_one(tx.model_dump(by_alias=True), session=session)

                await session.commit_transaction()

                if getattr(db_client, "redis", None):
                    await db_client.redis.publish(
                        f"user_notifications:{user_id}",
                        json.dumps(
                            {
                                "title": "Nạp tiền thành công",
                                "body": f"Tài khoản vừa được cộng thêm {dl_to_add} dl.",
                            }
                        ),
                    )
                logger.info(f"Added {dl_to_add} dl to user {user_id} (Order {order_code}) (atomic)")
        except Exception as e:
            await session.abort_transaction()
            logger.error(f"Order processing failed for {order_code}: {e}")
            raise
        finally:
            await session.end_session()
