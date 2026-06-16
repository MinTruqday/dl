import base64
import json
from datetime import datetime, timezone
import httpx
from core.config import settings
from fastapi import HTTPException
from loguru import logger
from src.repositories.auth_repository import AuthRepository
from src.services.auth import AuthService
from webauthn import (
    generate_authentication_options,
    options_to_json,
    verify_authentication_response,
)
from webauthn.helpers.structs import (
    PublicKeyCredentialDescriptor,
    PublicKeyCredentialType,
    UserVerificationRequirement,
)

RP_ID = settings.PASSKEY_RP_ID
ORIGIN = settings.PASSKEY_ALLOWED_ORIGINS

class PasskeyService:

    @staticmethod
    async def login_begin(email: str, db=None):
        user = await AuthRepository.get_auth_credential_by_email(email, db=db)
        if not user:
            raise HTTPException(status_code=404, detail="System unable to locate a user profile matching the provided information")
            
        passkeys = user.get("passkeys", [])
        if not passkeys:
            raise HTTPException(status_code=400, detail="Specified account has not been configured to support secure passkey authentication")
            
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
            await AuthRepository.set_redis_passkey_challenge(email, options.challenge)
        except Exception:
            logger.warning("System encountered issue attempting to persist authentication challenge to cache storage")
            
        await AuthRepository.upsert_passkey_challenge(email, options.challenge, db=db)
        return json.loads(options_to_json(options))

    @staticmethod
    async def login_finish(email: str, credential_data: dict, db=None):
        user = await AuthRepository.get_auth_credential_by_email(email, db=db)
        if not user:
            raise HTTPException(status_code=404, detail="System unable to locate a user profile matching the provided information")
            
        challenge = None
        try:
            challenge = await AuthRepository.get_redis_passkey_challenge(email)
        except Exception:
            logger.warning("System could not retrieve active authentication challenge from temporary cache storage")
            
        if not challenge:
            chal_doc = await AuthRepository.get_passkey_challenge(email, db=db)
            if chal_doc:
                age = (datetime.now(timezone.utc) - chal_doc["created_at"].replace(tzinfo=timezone.utc)).total_seconds()
                if age < 300:
                    challenge = chal_doc["challenge"]
                    
        if not challenge:
            raise HTTPException(status_code=400, detail="Cryptographic challenge required for authentication is invalid or exceeded time window")
            
        credential_id_b64 = credential_data.get("id")
        passkey = next((p for p in user.get("passkeys", []) if p["credential_id"] == credential_id_b64), None)
        
        if not passkey:
            raise HTTPException(status_code=400, detail="Submitted security credential does not match registered hardware or software token")
            
        try:
            verification = verify_authentication_response(
                credential=credential_data,
                expected_challenge=challenge,
                expected_origin=ORIGIN,
                expected_rp_id=RP_ID,
                credential_public_key=base64.b64decode(passkey["public_key"]),
                credential_current_sign_count=passkey["sign_count"],
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Cryptographic signature verification process failed to validate the provided security token")
            
        await AuthRepository.update_passkey_sign_count(user["_id"], credential_id_b64, verification.new_sign_count, db=db)
        await AuthRepository.delete_passkey_challenge(email, db=db)
        
        try:
            await AuthRepository.delete_redis_passkey_challenge(email)
        except Exception:
            logger.error(f"System unable to clear consumed authentication challenge for account {email}")

        user_doc = None
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{settings.MANAGEMENT_URL}/users/email/{email}", timeout=settings.DEFAULT_HTTP_TIMEOUT)
                if resp.status_code == 200:
                    user_doc = resp.json().get("data")
        except Exception:
            pass

        if not user_doc:
            raise HTTPException(status_code=401, detail="System could not verify existence of account associated with authentication request")

        return await AuthService.issue_token_for_user(user_doc, "passkey_login", db=db)