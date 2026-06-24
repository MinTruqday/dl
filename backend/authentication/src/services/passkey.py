import base64
import json
import os
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException
from loguru import logger
from src.repositories.authentication import AuthenticationRepository
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.exceptions import (
    InvalidAuthenticationResponse,
    InvalidRegistrationResponse,
)
from webauthn.helpers.structs import (
    AuthenticationCredential,
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    PublicKeyCredentialType,
    RegistrationCredential,
    UserVerificationRequirement,
)

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.schemas.authentication import UserInDB

RP_ID = settings.PASSKEY_RP_ID
RP_NAME = settings.PASSKEY_RP_NAME
ORIGIN = settings.PASSKEY_ALLOWED_ORIGINS


class PasskeyService:

    @staticmethod
    async def login_begin(email: str, db=None):
        user = await AuthenticationRepository.get_auth_credential_by_email(email, db=db)
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
        passkeys = user.get("passkeys", [])
        if not passkeys:
            raise HTTPException(
                status_code=400, detail="Tài khoản chưa thiết lập khóa truy cập"
            )
        options = generate_authentication_options(
            rp_id=RP_ID,
            allow_credentials=[
                PublicKeyCredentialDescriptor(
                    id=base64.b64decode(p["credential_id"]),
                    type=PublicKeyCredentialType.PUBLIC_KEY,
                    transports=p.get("transports"),
                )
                for p in passkeys
            ],
            user_verification=UserVerificationRequirement.PREFERRED,
        )
        try:
            await AuthenticationRepository.set_redis_passkey_challenge(email, options.challenge)
        except Exception as e:
            logger.warning(f"Lỗi lưu trữ tạm thời mã xác thực: {e}")
        await AuthenticationRepository.upsert_passkey_challenge(email, options.challenge, db=db)
        return json.loads(options_to_json(options))

    @staticmethod
    async def login_finish(email: str, credential_data: dict, db=None):
        user = await AuthenticationRepository.get_auth_credential_by_email(email, db=db)
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
        challenge = None
        try:
            challenge = await AuthenticationRepository.get_redis_passkey_challenge(email)
        except Exception as e:
            logger.warning(f"Lỗi tải thông tin xác thực: {e}")
        if not challenge:
            chal_doc = await AuthenticationRepository.get_passkey_challenge(email, db=db)
            if chal_doc:
                age = (
                    datetime.now(timezone.utc)
                    - chal_doc["created_at"].replace(tzinfo=timezone.utc)
                ).total_seconds()
                if age < 300:
                    challenge = chal_doc["challenge"]
        if not challenge:
            raise HTTPException(
                status_code=400, detail="Mã xác thực không hợp lệ hoặc đã hết hạn"
            )
        credential_id_b64 = credential_data.get("id")
        passkey = next(
            (
                p
                for p in user.get("passkeys", [])
                if p["credential_id"] == credential_id_b64
            ),
            None,
        )
        if not passkey:
            raise HTTPException(status_code=400, detail="Khóa bảo mật không chính xác")
        try:
            verification = verify_authentication_response(
                credential=credential_data,
                expected_challenge=challenge,
                expected_origin=ORIGIN,
                expected_rp_id=RP_ID,
                credential_public_key=base64.b64decode(passkey["public_key"]),
                credential_current_sign_count=passkey["sign_count"],
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Lỗi xác minh mã bảo mật: {e}")
        await AuthenticationRepository.update_passkey_sign_count(
            user["_id"], credential_id_b64, verification.new_sign_count, db=db
        )
        await AuthenticationRepository.delete_passkey_challenge(email, db=db)
        try:
            await AuthenticationRepository.delete_redis_passkey_challenge(email)
        except Exception as e:
            logger.error(f"Lỗi xóa mã xác thực khỏi bộ nhớ: {e}")
        user_doc = None
        try:
            async with httpx.AsyncClient(timeout=settings.DEFAULT_HTTP_TIMEOUT) as client:
                resp = await client.get(
                    f"{settings.MANAGEMENT_URL}/nguoi-dung/email/{email}",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    user_doc = resp.json().get("data")
        except Exception:
            pass

        if not user_doc:
            raise HTTPException(status_code=401, detail="Không thể xác minh tài khoản")

        from src.services.passkey import SessionService

        return await SessionService.issue_token_for_user(user_doc, "passkey_login")

    @staticmethod
    async def register_begin(email: str, db=None):
        user = await AuthenticationRepository.get_auth_credential_by_email(email, db=db)
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

        passkeys = user.get("passkeys", [])
        
        options = generate_registration_options(
            rp_id=RP_ID,
            rp_name=RP_NAME,
            user_id=str(user["_id"]).encode("utf-8"),
            user_name=email,
            user_display_name=email,
            exclude_credentials=[
                PublicKeyCredentialDescriptor(
                    id=base64.b64decode(p["credential_id"]),
                    type=PublicKeyCredentialType.PUBLIC_KEY,
                )
                for p in passkeys
            ],
            authenticator_selection=AuthenticatorSelectionCriteria(
                authenticator_attachment=AuthenticatorAttachment.PLATFORM,
                user_verification=UserVerificationRequirement.REQUIRED,
            ),
        )

        try:
            await AuthenticationRepository.set_redis_passkey_challenge(email, options.challenge)
        except Exception as e:
            logger.warning(f"Lỗi lưu trữ tạm thời mã xác thực: {e}")
            
        await AuthenticationRepository.upsert_passkey_challenge(email, options.challenge, db=db)

        return json.loads(options_to_json(options))

    @staticmethod
    async def register_finish(email: str, credential_data: dict, db=None):
        user = await AuthenticationRepository.get_auth_credential_by_email(email, db=db)
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

        challenge = None
        try:
            challenge = await AuthenticationRepository.get_redis_passkey_challenge(email)
        except Exception as e:
            logger.warning(f"Lỗi tải thông tin xác thực: {e}")
            
        if not challenge:
            chal_doc = await AuthenticationRepository.get_passkey_challenge(email, db=db)
            if chal_doc:
                age = (
                    datetime.now(timezone.utc)
                    - chal_doc["created_at"].replace(tzinfo=timezone.utc)
                ).total_seconds()
                if age < 300:
                    challenge = chal_doc["challenge"]

        if not challenge:
            raise HTTPException(
                status_code=400, detail="Mã xác thực không hợp lệ hoặc đã hết hạn"
            )

        try:
            verification = verify_registration_response(
                credential=credential_data,
                expected_challenge=challenge,
                expected_origin=ORIGIN,
                expected_rp_id=RP_ID,
            )
        except InvalidRegistrationResponse as e:
            raise HTTPException(status_code=400, detail=f"Lỗi xác minh mã bảo mật: {e}")

        new_passkey = {
            "credential_id": base64.b64encode(verification.credential_id).decode("utf-8"),
            "public_key": base64.b64encode(verification.credential_public_key).decode("utf-8"),
            "sign_count": verification.sign_count,
            "created_at": datetime.now(timezone.utc)
        }

        if db is None:
            db = database.mongodb.get_default_database()
        await db["auth_credentials"].update_one(
            {"_id": user["_id"]},
            {"$push": {"passkeys": new_passkey}}
        )

        await AuthenticationRepository.delete_passkey_challenge(email, db=db)
        try:
            await AuthenticationRepository.delete_redis_passkey_challenge(email)
        except Exception as e:
            logger.error(f"Lỗi xóa mã xác thực khỏi bộ nhớ: {e}")

        return {"message": "Đăng ký Passkey thành công"}
