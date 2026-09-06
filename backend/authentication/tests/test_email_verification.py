import asyncio
from datetime import datetime, timezone

from fastapi import HTTPException

from src.repositories.identity import IdentityRepository
from src.services.email import EmailService
from src.services.session import SessionService


async def run_test():
    captured = {}
    audits = []

    async def create_token(document):
        captured.update(document)
        return document["_id"]

    async def send_email(email, token):
        captured["sent_email"] = email
        captured["sent_token"] = token
        return True

    async def insert_audit(document):
        audits.append(document)
        return document

    original_create = IdentityRepository.create_email_verification_token
    original_send = EmailService.send_email_verification
    original_audit = IdentityRepository.insert_audit_log
    original_consume = IdentityRepository.consume_email_verification_token
    original_mark = IdentityRepository.mark_email_verified
    try:
        IdentityRepository.create_email_verification_token = create_token
        EmailService.send_email_verification = send_email
        IdentityRepository.insert_audit_log = insert_audit
        result = await SessionService.issue_email_verification(
            "USER-1", "User@example.com", "127.0.0.1"
        )
        assert result == {"status": "ok", "delivery_status": "SENT"}
        assert captured["user_id"] == "USER-1"
        assert captured["email"] == "User@example.com"
        assert len(captured["token"]) >= 32
        assert captured["sent_token"] == captured["token"]
        assert captured["expires_at"] > datetime.now(timezone.utc)
        token_document = {
            "user_id": "USER-1",
            "email": "user@example.com",
        }

        async def consume_token(token):
            return token_document if token == captured["token"] else None

        async def mark_verified(user_id, email):
            return {"_id": user_id, "email": email, "is_verified": True}

        IdentityRepository.consume_email_verification_token = consume_token
        IdentityRepository.mark_email_verified = mark_verified
        verified = await SessionService.verify_email(captured["token"], "127.0.0.1")
        assert verified == {"verified": True, "email": "user@example.com"}

        async def consume_missing(token):
            return None

        IdentityRepository.consume_email_verification_token = consume_missing
        try:
            await SessionService.verify_email(captured["token"], "127.0.0.1")
        except HTTPException as exc:
            assert exc.status_code == 400
        else:
            raise AssertionError("Mã xác minh đã dùng phải bị từ chối")
        assert [item["action"] for item in audits] == [
            "EMAIL_VERIFICATION_REQUESTED",
            "EMAIL_VERIFIED",
        ]
    finally:
        IdentityRepository.create_email_verification_token = original_create
        EmailService.send_email_verification = original_send
        IdentityRepository.insert_audit_log = original_audit
        IdentityRepository.consume_email_verification_token = original_consume
        IdentityRepository.mark_email_verified = original_mark


if __name__ == "__main__":
    asyncio.run(run_test())
    print("authentication email verification test passed")
