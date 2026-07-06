import asyncio
from src.services.thread import ThreadService
import json
from src.core.infrastructure.redis import redis
import os

class DummyUser:
    def __init__(self, id):
        self.id = id

async def mock():
    from src.core.infrastructure.database import init_db
    await init_db()
    
    sender = DummyUser(id="system-mock-user-12345")
    receiver_id = "11111111-1111-1111-1111-111111111111"
    
    try:
        msg = await ThreadService.send_message(
            receiver_id=receiver_id,
            content="Xin chào! Đây là tin nhắn giả lập (mock) từ hệ thống để bạn xem giao diện hiển thị của trang Tin nhắn nhé. Bạn có thể thử trả lời lại tin nhắn này!",
            current_user=sender
        )
        print("Message saved to DB:", msg)
        
        from fastapi.encoders import jsonable_encoder
        payload = json.dumps(jsonable_encoder({"type": "new_message", "data": msg}))
        await redis.publish(f"message_delivery:{receiver_id}", payload)
        print("Published to websocket via Redis!")
    except Exception as e:
        print("Error:", e)

asyncio.run(mock())
