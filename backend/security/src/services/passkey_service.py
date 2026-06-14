import base64
import json
import os
import uuid
from datetime import datetime, timezone

from core.config import settings
from core.database import db_client
from core.schemas.user import UserInDB
from fastapi import HTTPException
from loguru import logger
from src.repositories.auth_repository import AuthRepository
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

RP_ID = settings.PASSKEY_RP_ID
RP_NAME = settings.PASSKEY_RP_NAME
ORIGIN = settings.PASSKEY_ALLOWED_ORIGINS


class PasskeyService:

    @staticmethod
    async def login_begin(email: str, db=None):
        user = await AuthRepository.get_auth_credential_by_email(email, db=db)
        if not user:
            raise HTTPException(status_code=404, detail="The system was unable to locate a user profile matching the provided information")
        passkeys = user.get("passkeys", [])
        if not passkeys:
            raise HTTPException(
                status_code=400, detail="The specified account has not been configured to support secure passkey authentication"
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
            await AuthRepository.set_redis_passkey_challenge(email, options.challenge)
        except Exception:
            logger.warning("The system encountered an issue while attempting to persist the authentication challenge to the temporary cache storage")
        await AuthRepository.upsert_passkey_challenge(email, options.challenge, db=db)
        return json.loads(options_to_json(options))

    @staticmethod
    async def login_finish(email: str, credential_data: dict, db=None):
        user = await AuthRepository.get_auth_credential_by_email(email, db=db)
        if not user:
            raise HTTPException(status_code=404, detail="The system was unable to locate a user profile matching the provided information")
        challenge = None
        try:
            challenge = await AuthRepository.get_redis_passkey_challenge(email)
        except Exception:
            logger.warning("The system could not retrieve the active authentication challenge from the temporary cache storage")
        if not challenge:
            chal_doc = await AuthRepository.get_passkey_challenge(email, db=db)
            if chal_doc:
                age = (
                    datetime.now(timezone.utc)
                    - chal_doc["created_at"].replace(tzinfo=timezone.utc)
                ).total_seconds()
                if age < 300:
                    challenge = chal_doc["challenge"]
        if not challenge:
            raise HTTPException(
                status_code=400, detail="The cryptographic challenge required for authentication is either invalid or has exceeded its permissible time window"
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
            raise HTTPException(status_code=400, detail="The submitted security credential does not match the registered hardware or software token for this account")
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
            raise HTTPException(status_code=400, detail="The cryptographic signature verification process failed to validate the provided security token")
        await AuthRepository.update_passkey_sign_count(
            user["_id"], credential_id_b64, verification.new_sign_count, db=db
        )
        await AuthRepository.delete_passkey_challenge(email, db=db)
        try:
            await AuthRepository.delete_redis_passkey_challenge(email)
        except Exception:
            logger.error(f"The system was unable to clear the consumed authentication challenge for the account {email} from the cache")
        import httpx

        user_doc = None
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.PROVISION_URL}/users/by-email/{email}",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    user_doc = resp.json().get("data")
        except Exception:
            pass

        if not user_doc:
            raise HTTPException(status_code=401, detail="The system could not verify the existence of the account associated with the authentication request")

        from src.services.auth_service import AuthService

        return await AuthService.issue_token_for_user(user_doc, "passkey_login")