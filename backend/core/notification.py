import httpx
from core.config import settings
from loguru import logger

async def send_internal_notification(user_id: str, title: str, body: str, notif_type: str = "SYSTEM"):
    if not settings.SIGNAL_URL:
        logger.warning("Chưa thiết lập đường dẫn tín hiệu, bỏ qua việc gửi thông báo")
        return False
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.SIGNAL_URL}/thong-bao/noi-bo/kich-hoat",
                json={
                    "target_user_id": user_id,
                    "title": title,
                    "body": body,
                    "type": notif_type
                },
                timeout=3.0
            )
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error(f'Lỗi gửi thông báo tới {user_id}')
        return False
