import asyncio
import os
import secrets
from datetime import datetime, timezone
from src.services.interaction import InteractionService

class DummyUser:
    def __init__(self, uid, name):
        self.id = uid
        self.full_name = name

async def run_phase2_tests():
    print("=" * 60)
    print(" BẮT ĐẦU CHẠY THỰC TẾ SMOKE TEST MESSAGING PHASE 2 ")
    print("=" * 60)

    from src.core.infrastructure.database import init_db
    await init_db()

    user1 = DummyUser("u1_test_phase2", "User One")
    user2 = DummyUser("u2_test_phase2", "User Two")

    # TEST 1: Save to Cloud
    cloud_res = await InteractionService.save_to_cloud(
        message_id="msg-101",
        content="Ghi chú cá nhân quan trọng",
        attachments=[{"url": "http://example.com/file.pdf"}],
        current_user=user1
    )
    print("▶ 1. Save to Cloud:", cloud_res)
    assert cloud_res["status"] == "saved"

    # TEST 2: Update Chat Theme
    theme_res = await InteractionService.update_theme(
        other_user_id=user2.id,
        theme_id="obsidian",
        current_user=user1
    )
    print("▶ 2. Update Theme:", theme_res)
    assert theme_res["theme_id"] == "obsidian"

    print("=" * 60)
    print(" MESSAGING PHASE 2 PASSED 100% ")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_phase2_tests())
