from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.redis import redis
from src.core.infrastructure.mongo import mongo
import hashlib
import hmac
import json
import random
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException, Response
from loguru import logger
from src.schemas.wallet import Transaction, TransactionType

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database

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
    @log_logic_execution
    async def create_deposit_link(req, current_user):
        if req.amount < 1000:
            raise HTTPException(
                status_code=400, detail="Số tiền nạp dưới mức tối thiểu"
            )

        while True:
            order_code = random.randint(100000000, 2147483647)
            if not await mongo.find_one(collection="orders", query={"order_code": order_code}):
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
                    "name": "Deposit transaction into digital wallet",
                    "quantity": 1,
                    "price": req.amount,
                }
            ],
            "cancelUrl": cancel_url,
            "returnUrl": return_url,
            "signature": signature,
        }

        await mongo.insert_one("orders", 
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
            async with httpx.AsyncClient(timeout=settings.DEFAULT_HTTP_TIMEOUT) as client:
                response = await client.post(
                    settings.PAYOS_API_URL,
                    json=payload,
                    headers={
                        "x-client-id": settings.PAYOS_CLIENT_ID,
                        "x-api-key": settings.PAYOS_API_KEY,
                        "Content-Type": "application/json",
                    },
                )
            res_data = response.json()
            if res_data.get("code") == "00":
                checkout_url = res_data["data"]["checkoutUrl"]
                await mongo.update_one("orders", 
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
                logger.warning("Yêu cầu khởi tạo liên kết thanh toán bị từ chối")
                await mongo.update_one("orders", 
                    {"order_code": order_code}, {"$set": {"status": "FAILED"}}
                )
                raise HTTPException(
                    status_code=400,
                    detail="Lỗi khởi tạo phiên thanh toán",
                )
        except HTTPException:
            raise
        except Exception as e:
            await mongo.update_one("orders", 
                {"order_code": order_code}, {"$set": {"status": "FAILED"}}
            )
            logger.exception("Lỗi kết nối mạng tới cổng thanh toán")
            raise HTTPException(status_code=500, detail=f"Lỗi kết nối cổng thanh toán: {e}")

    @staticmethod
    @log_logic_execution
    async def deposit_webhook(request):
        data = await request.json()
        logger.info("Cập nhật trạng thái thanh toán thành công")
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
                    logger.warning(
                        "Từ chối thông báo cổng thanh toán do thiếu chữ ký xác thực"
                    )
                    raise HTTPException(
                        status_code=400,
                        detail="Lỗi xác minh giao dịch do thiếu chữ ký bảo mật",
                    )

                expected_signature = DepositService._generate_payos_signature(
                    signature_data
                )
                if received_signature != expected_signature:
                    logger.warning("Từ chối thông báo cổng thanh toán do sai chữ ký số")
                    raise HTTPException(
                        status_code=400,
                        detail="Xác minh giao dịch thất bại do sai chữ ký số",
                    )

                paid_amount = webhook_data.get("amount", 0)
                await DepositService.process_success_order(order_code, paid_amount)
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Lỗi xử lý phản hồi dữ liệu thanh toán")
        return Response(
            content=json.dumps({"code": "00", "desc": "success"}),
            media_type="application/json",
            status_code=200,
        )

    @staticmethod
    @log_logic_execution
    async def verify_deposit(order_code: int, current_user):
        order = await mongo.find_one(collection="orders", query={"order_code": order_code})
        if not order:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy giao dịch nạp tiền"
            )
        if order.get("user_id") != str(current_user.id):
            raise HTTPException(
                status_code=403, detail="Không có quyền xem chi tiết giao dịch này"
            )

        if getattr(database, "redis", None):
            rl_key = f"rl:verify_deposit:{current_user.id}"
            try:
                attempts = await redis.incr(rl_key)
                if attempts == 1:
                    await redis.expire(rl_key, 60)
                if attempts > 10:
                    raise HTTPException(
                        status_code=429,
                        detail="Đang giới hạn yêu cầu, vui lòng thử lại sau",
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.exception("Quá tải yêu cầu xác minh giao dịch")

        try:
            async with httpx.AsyncClient(timeout=settings.DEFAULT_HTTP_TIMEOUT) as client:
                response = await client.get(
                    f"{settings.PAYOS_API_URL}/{order_code}",
                    headers={
                        "x-client-id": settings.PAYOS_CLIENT_ID,
                        "x-api-key": settings.PAYOS_API_KEY,
                    },
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
                raise HTTPException(status_code=400, detail="Lỗi xác minh giao dịch")
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Lỗi xác minh trạng thái giao dịch trên cổng thanh toán")
            raise HTTPException(status_code=500, detail=f"Lỗi xác minh giao dịch: {e}")

    @staticmethod
    @log_logic_execution
    async def process_success_order(
        order_code: int, paid_amount: int = None, session=None
    ):
        should_close_session = False
        if session is None:
            session = await database.mongodb.start_session()
            session.start_transaction()
            should_close_session = True

        orders = database.mongodb["orders"]
        wallets = database.mongodb["wallets"]
        transactions = database.mongodb["transactions"]

        order = await orders.find_one(
            {"order_code": order_code, "status": {"$in": ["INIT", "pending"]}}
        )
        if not order:
            logger.warning("Đơn nạp tiền không tồn tại hoặc đã xử lý")
            if should_close_session:
                await session.abort_transaction()
                await session.end_session()
            return

        if paid_amount is not None and paid_amount < order.get("amount", 0):
            logger.warning("Số tiền nạp không đủ để hoàn thành yêu cầu")
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
                logger.warning("Lỗi cập nhật trạng thái đơn nạp tiền")
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
                note="Deposit successfully processed via electronic payment gateway",
            )
            await transactions.insert_one(tx.model_dump(by_alias=True), session=session)

            if should_close_session:
                await session.commit_transaction()

            try:
                from src.core.infrastructure.mq import mq

                await mq.publish(
                    "notification_queue",
                    {
                        "target_user_id": user_id,
                        "title": "Deposit processed successfully",
                        "body": "The requested deposit funds have been successfully credited to the digital wallet",
                        "type": "topup",
                    }
                )
            except Exception as e:
                logger.exception("Lỗi đẩy thông báo nạp tiền qua MQ")
            logger.info("Đã xác minh và nạp tiền vào tài khoản")
        except Exception as e:
            if should_close_session:
                await session.abort_transaction()
            logger.exception("Lỗi xử lý hoàn tất giao dịch nạp tiền vào hệ thống")
            raise HTTPException(
                status_code=500, detail=f"Tính năng thanh toán đang bảo trì: {e}"
            )
        finally:
            if should_close_session:
                await session.end_session()
