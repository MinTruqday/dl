from core.config import settings
import hmac
import hashlib
import json
import httpx
import os
from datetime import datetime
from fastapi import HTTPException, Response
from core.database import db_client
from models.wallet import Transaction, TransactionType
from loguru import logger

class GatewayService:
    @staticmethod
    async def create_momo_payment(req, current_user):
        partner_code = getattr(settings, "MOMO_PARTNER_CODE", None)
        access_key = getattr(settings, "MOMO_ACCESS_KEY", None)
        secret_key = getattr(settings, "MOMO_SECRET_KEY", None)
        endpoint = getattr(settings, "MOMO_ENDPOINT", None)
        return_url = getattr(settings, "MOMO_RETURN_URL", None)
        notify_url = f"{getattr(settings, 'MOMO_NOTIFY_URL', None)}/api/gateways/momo/ipn"

        if req.amount < 1000:
            raise HTTPException(status_code=400, detail="Số tiền nạp tối thiểu là 1,000 VNĐ.")
            
        order_id = f"{current_user.id}_{int(datetime.now().timestamp())}"
        request_id = order_id
        order_info = f"Nạp {req.amount} VNĐ vào ví DocLib"
        amount = str(req.amount)
        
        raw_signature = (
            f"accessKey={access_key}"
            f"&amount={amount}"
            f"&extraData=" 
            f"&ipnUrl={notify_url}"
            f"&orderId={order_id}"
            f"&orderInfo={order_info}"
            f"&partnerCode={partner_code}"
            f"&redirectUrl={return_url}"
            f"&requestId={request_id}"
            f"&requestType=captureWallet"
        )
        
        signature = hmac.new(
            secret_key.encode("utf-8"),
            raw_signature.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        payload = {
            "partnerCode": partner_code,
            "partnerName": "DocLib",
            "storeId": "DocLibStore",
            "requestId": request_id,
            "amount": req.amount,
            "orderId": order_id,
            "orderInfo": order_info,
            "redirectUrl": return_url,
            "ipnUrl": notify_url,
            "lang": "vi",
            "extraData": "",
            "requestType": "captureWallet",
            "signature": signature
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(endpoint, json=payload, timeout=10)
            res_data = response.json()
            
            if res_data.get("resultCode") == 0:
                db = db_client.mongodb.get_default_database()
                await db["orders"].insert_one({
                    "order_id": order_id,
                    "user_id": current_user.id,
                    "amount": req.amount,
                    "dl": req.amount // 1000,
                    "gateway": "MOMO",
                    "status": "pending",
                    "created_at": datetime.utcnow()
                })
                return {"payUrl": res_data.get("payUrl")}
            else:
                logger.error(f"Failed to create MoMo transaction: {res_data}")
                raise HTTPException(status_code=400, detail=res_data.get("message", "Lỗi từ cổng MoMo"))
                
        except Exception as e:
            logger.error(f"MoMo connection error: {e}")
            raise HTTPException(status_code=500, detail="Không thể kết nối với hệ thống thanh toán MoMo. Vui lòng thử lại sau.")

    @staticmethod
    async def momo_ipn(request):
        data = await request.json()
        logger.info(f"Received MoMo IPN: {data}")
        
        partner_code = getattr(settings, "MOMO_PARTNER_CODE", None)
        access_key = getattr(settings, "MOMO_ACCESS_KEY", None)
        secret_key = getattr(settings, "MOMO_SECRET_KEY", None)

        raw_signature = (
            f"accessKey={access_key}"
            f"&amount={data.get('amount')}"
            f"&extraData={data.get('extraData', '')}"
            f"&message={data.get('message', '')}"
            f"&orderId={data.get('orderId')}"
            f"&orderInfo={data.get('orderInfo', '')}"
            f"&orderType={data.get('orderType', '')}"
            f"&partnerCode={data.get('partnerCode')}"
            f"&payType={data.get('payType', '')}"
            f"&requestId={data.get('requestId', '')}"
            f"&responseTime={data.get('responseTime', '')}"
            f"&resultCode={data.get('resultCode')}"
            f"&transId={data.get('transId')}"
        )
        
        my_signature = hmac.new(
            secret_key.encode("utf-8"),
            raw_signature.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        if my_signature != data.get("signature"):
            logger.error("MoMo IPN signature mismatch detected")
            return Response(content="Invalid Signature", status_code=400)
            
        if data.get("resultCode") == 0:
            await GatewayService.process_success_order(data.get("orderId"))
            
        return Response(status_code=204)

    @staticmethod
    async def process_success_order(order_id: str):
        db = db_client.mongodb.get_default_database()
        orders = db["orders"]
        users = db["users"]
        transactions = db["transactions"]
        
        result = await orders.update_one(
            {"order_id": order_id, "status": "pending"},
            {"$set": {"status": "success", "updated_at": datetime.utcnow()}}
        )
        
        if result.modified_count == 1:
            order = await orders.find_one({"order_id": order_id})
            dl_to_add = order.get("dl", 0)
            user_id = order["user_id"]
            
            await users.update_one(
                {"_id": user_id},
                {"$inc": {"wallet_balance": dl_to_add}}
            )
            
            tx = Transaction(
                user_id=user_id,
                type=TransactionType.TOPUP,
                amount=dl_to_add,
                note=f"Nạp tiền qua {order['gateway']}: {order['amount']} VNĐ"
            )
            await transactions.insert_one(tx.model_dump(by_alias=True))
            
            if getattr(db_client, "redis", None):
                await db_client.redis.publish(
                    f"user_notifications:{user_id}", 
                    json.dumps({
                        "title": "Nạp tiền thành công", 
                        "body": f"Tài khoản vừa được cộng thêm {dl_to_add} dl."
                    })
                )
            logger.info(f"Added {dl_to_add} dl to user {user_id} (Order {order_id})")
