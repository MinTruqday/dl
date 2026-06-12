from core.config import settings
import base64
import json
from webauthn import generate_registration_options, verify_registration_response, generate_authentication_options, verify_authentication_response, options_to_json
from webauthn.helpers.structs import RegistrationCredential, AuthenticationCredential, AuthenticatorSelectionCriteria, UserVerificationRequirement, AuthenticatorAttachment, PublicKeyCredentialDescriptor, PublicKeyCredentialType
from webauthn.helpers.exceptions import InvalidRegistrationResponse, InvalidAuthenticationResponse
from fastapi import HTTPException
from core.database import db_client
from src.schemas.user import UserInDB
from datetime import datetime, timezone
import os
import uuid
from loguru import logger
RP_ID = getattr(settings, 'PASSKEY_RP_ID')
RP_NAME = getattr(settings, 'PASSKEY_RP_NAME')
ORIGIN = getattr(settings, 'PASSKEY_ALLOWED_ORIGINS')

class PasskeyService:

    @staticmethod
    async def register_begin(email: str, db=None):
        if db is None:
            db = db_client.mongodb[settings.MONGODB_DB_NAME]
        user = await db['auth_credentials'].find_one({'email': email})
        if not user:
            raise HTTPException(status_code=404, detail='Không tìm thấy người dùng này')
        user_id = str(user['_id'])
        options = generate_registration_options(rp_id=RP_ID, rp_name=RP_NAME, user_id=user_id.encode('utf-8'), user_name=email, user_display_name=email, authenticator_selection=AuthenticatorSelectionCriteria(user_verification=UserVerificationRequirement.PREFERRED))
        if db_client.redis:
            try:
                await db_client.redis.setex(f'passkey_reg_challenge:{email}', 300, options.challenge)
            except Exception as e:
                logger.warning(f'Không thể lưu thử thách vào Redis: {e}')
        await db['passkey_challenges'].update_one({'_id': f'reg:{email}'}, {'$set': {'challenge': options.challenge, 'created_at': datetime.now(timezone.utc)}}, upsert=True)
        return json.loads(options_to_json(options))

    @staticmethod
    async def register_finish(email: str, credential_data: dict, db=None):
        if db is None:
            db = db_client.mongodb[settings.MONGODB_DB_NAME]
        user = await db['auth_credentials'].find_one({'email': email})
        if not user:
            raise HTTPException(status_code=404, detail='Không tìm thấy người dùng này')
        challenge = None
        if db_client.redis:
            try:
                challenge = await db_client.redis.get(f'passkey_reg_challenge:{email}')
            except Exception as e:
                logger.warning(f'Không thể lấy thử thách từ Redis: {e}')
        if not challenge:
            chal_doc = await db['passkey_challenges'].find_one({'_id': f'reg:{email}'})
            if chal_doc:
                age = (datetime.now(timezone.utc) - chal_doc['created_at'].replace(tzinfo=timezone.utc)).total_seconds()
                if age < 300:
                    challenge = chal_doc['challenge']
        if not challenge:
            raise HTTPException(status_code=400, detail='Challenge không hợp lệ hoặc đã hết hạn')
        try:
            verification = verify_registration_response(credential=credential_data, expected_challenge=challenge, expected_origin=ORIGIN, expected_rp_id=RP_ID)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f'Xác thực Passkey gặp sự cố: {str(e)}')
        new_passkey = {'credential_id': base64.b64encode(verification.credential_id).decode('utf-8'), 'public_key': base64.b64encode(verification.credential_public_key).decode('utf-8'), 'sign_count': verification.sign_count, 'transports': credential_data.get('response', {}).get('transports', []), 'created_at': datetime.now(timezone.utc)}
        await db['auth_credentials'].update_one({'_id': user['_id']}, {'$push': {'passkeys': new_passkey}})
        await db['passkey_challenges'].delete_one({'_id': f'reg:{email}'})
        if db_client.redis:
            try:
                await db_client.redis.delete(f'passkey_reg_challenge:{email}')
            except Exception as e:
                logger.error(f'Không thể xóa khóa thử thách đăng ký Redis của {email}: {e}')
        return {'message': 'Đăng ký Passkey hoàn tất'}

    @staticmethod
    async def login_begin(email: str, db=None):
        if db is None:
            db = db_client.mongodb[settings.MONGODB_DB_NAME]
        user = await db['auth_credentials'].find_one({'email': email})
        if not user:
            raise HTTPException(status_code=404, detail='Không tìm thấy người dùng này')
        passkeys = user.get('passkeys', [])
        if not passkeys:
            raise HTTPException(status_code=400, detail='Tài khoản này chưa đăng ký Passkey')
        options = generate_authentication_options(rp_id=RP_ID, allow_credentials=[PublicKeyCredentialDescriptor(id=base64.b64decode(p['credential_id']), type=PublicKeyCredentialType.PUBLIC_KEY, transports=p.get('transports')) for p in passkeys], user_verification=UserVerificationRequirement.PREFERRED)
        if db_client.redis:
            try:
                await db_client.redis.setex(f'passkey_auth_challenge:{email}', 300, options.challenge)
            except Exception as e:
                logger.warning(f'Không thể lưu thử thách xác thực vào Redis: {e}')
        await db['passkey_challenges'].update_one({'_id': f'auth:{email}'}, {'$set': {'challenge': options.challenge, 'created_at': datetime.now(timezone.utc)}}, upsert=True)
        return json.loads(options_to_json(options))

    @staticmethod
    async def login_finish(email: str, credential_data: dict, db=None):
        if db is None:
            db = db_client.mongodb[settings.MONGODB_DB_NAME]
        user = await db['auth_credentials'].find_one({'email': email})
        if not user:
            raise HTTPException(status_code=404, detail='Không tìm thấy người dùng này')
        challenge = None
        if db_client.redis:
            try:
                challenge = await db_client.redis.get(f'passkey_auth_challenge:{email}')
            except Exception as e:
                logger.warning(f'Không thể lấy thử thách xác thực từ Redis: {e}')
        if not challenge:
            chal_doc = await db['passkey_challenges'].find_one({'_id': f'auth:{email}'})
            if chal_doc:
                age = (datetime.now(timezone.utc) - chal_doc['created_at'].replace(tzinfo=timezone.utc)).total_seconds()
                if age < 300:
                    challenge = chal_doc['challenge']
        if not challenge:
            raise HTTPException(status_code=400, detail='Challenge không hợp lệ hoặc đã hết hạn')
        credential_id_b64 = credential_data.get('id')
        passkey = next((p for p in user.get('passkeys', []) if p['credential_id'] == credential_id_b64), None)
        if not passkey:
            raise HTTPException(status_code=400, detail='Passkey không hợp lệ')
        try:
            verification = verify_authentication_response(credential=credential_data, expected_challenge=challenge, expected_origin=ORIGIN, expected_rp_id=RP_ID, credential_public_key=base64.b64decode(passkey['public_key']), credential_current_sign_count=passkey['sign_count'])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f'Xác thực đăng nhập gặp sự cố: {str(e)}')
        await db['auth_credentials'].update_one({'_id': user['_id'], 'passkeys.credential_id': credential_id_b64}, {'$set': {'passkeys.$.sign_count': verification.new_sign_count}})
        await db['passkey_challenges'].delete_one({'_id': f'auth:{email}'})
        if db_client.redis:
            try:
                await db_client.redis.delete(f'passkey_auth_challenge:{email}')
            except Exception as e:
                logger.error(f'Không thể xóa khóa thử thách xác thực Redis của {email}: {e}')
        import httpx
        user_doc = None
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{settings.PROVISION_URL}/nguoi-dung/noi-bo/email/{email}", timeout=3.0)
                if resp.status_code == 200:
                    user_doc = resp.json().get('data')
        except Exception:
            pass

        if not user_doc:
            raise HTTPException(status_code=401, detail='Tài khoản không tồn tại trên hệ thống')
            
        from src.services.authentication import AuthenticationService
        return await AuthenticationService.issue_token_for_user(user_doc, 'passkey_login')
