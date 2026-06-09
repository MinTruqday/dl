from typing import Any
from src.core.response import APIResponse
from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from src.schemas.user import UserCreate, UserInDB, UserResponse, ForgotPasswordRequest, ResetPasswordRequest, VerifyCodeRequest
from src.api.dependency import get_current_user, get_db
from src.services.authentication import AuthenticationService
from src.services.passkey import PasskeyService
from src.schemas.user import PasskeyRequest, PasskeyFinishRequest

router = APIRouter(prefix='/xac-thuc')

@router.get('/ca-nhan', response_model=APIResponse[UserResponse])
async def read_users_me(current_user: UserInDB = Depends(get_current_user), db=Depends(get_db)):
    user_doc = await db['users'].find_one({'_id': str(current_user.id)})
    if not user_doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    user_doc['_id'] = str(user_doc['_id'])
    user_data = UserInDB(**user_doc).model_dump()
    user_data['has_passkey'] = len(user_doc.get('passkeys', [])) > 0
    return APIResponse(data=user_data, message='Lấy thông tin cá nhân thành công')

@router.post('/dang-ky', response_model=APIResponse[Any], status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, request: Request, db=Depends(get_db)):
    client_ip = request.client.host if request.client else 'unknown'
    return APIResponse(data=await AuthenticationService.register_user(user_in, client_ip, db=db), message='Đăng ký tài khoản thành công', status=status.HTTP_201_CREATED)

@router.post('/dang-nhap', response_model=APIResponse[Any])
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    client_ip = request.client.host if request.client else 'unknown'
    return APIResponse(data=await AuthenticationService.login_user(form_data.username, form_data.password, client_ip, db=db), message='Đăng nhập thành công')

@router.post('/dang-xuat-tat-ca', response_model=APIResponse[Any])
async def revoke_all_sessions(current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(data=await AuthenticationService.revoke_all_sessions(current_user), message='Đã đăng xuất khỏi tất cả thiết bị')

@router.post('/quen-mat-khau', response_model=APIResponse[Any])
async def forgot_password(payload: ForgotPasswordRequest, request: Request, db=Depends(get_db)):
    client_ip = request.client.host if request.client else 'unknown'
    return APIResponse(data=await AuthenticationService.forgot_password(payload.email, client_ip, db=db), message='Yêu cầu khôi phục mật khẩu đã được gửi')

@router.post('/dat-lai-mat-khau', response_model=APIResponse[Any])
async def reset_password(payload: ResetPasswordRequest, request: Request, db=Depends(get_db)):
    client_ip = request.client.host if request.client else 'unknown'
    return APIResponse(data=await AuthenticationService.reset_password(payload.token, payload.new_password, client_ip, db=db), message='Đặt lại mật khẩu thành công')

@router.post('/ma-xac-thuc', response_model=APIResponse[Any])
async def verify_code(payload: VerifyCodeRequest, request: Request, db=Depends(get_db)):
    client_ip = request.client.host if request.client else 'unknown'
    return APIResponse(data=await AuthenticationService.verify_reset_code(payload.token, client_ip, db=db), message='Mã xác thực hợp lệ')

@router.get('/google/dang-nhap', response_model=APIResponse[Any])
async def google_login(db=Depends(get_db)):
    auth_url = await AuthenticationService.get_google_auth_url(db=db)
    return APIResponse(data={'url': auth_url}, message='Lấy liên kết đăng nhập Google thành công')

@router.get('/google/phan-hoi', response_model=APIResponse[Any])
async def google_callback(code: str, request: Request, db=Depends(get_db)):
    client_ip = request.client.host if request.client else 'unknown'
    return APIResponse(data=await AuthenticationService.handle_google_callback(code, client_ip, db=db), message='Đăng nhập Google thành công')

# --- Passkey routes embedded here ---

@router.post('/passkey/dang-ky/bat-dau', response_model=APIResponse[Any])
async def passkey_register_begin(payload: PasskeyRequest, db=Depends(get_db)):
    return APIResponse(data=await PasskeyService.register_begin(payload.email, db=db), message='Khởi tạo đăng ký Passkey thành công')

@router.post('/passkey/dang-ky/hoan-tat', response_model=APIResponse[Any])
async def passkey_register_finish(payload: PasskeyFinishRequest, db=Depends(get_db)):
    return APIResponse(data=await PasskeyService.register_finish(payload.email, payload.credential, db=db), message='Hoàn tất đăng ký Passkey thành công')

@router.post('/passkey/dang-nhap/bat-dau', response_model=APIResponse[Any])
async def passkey_login_begin(payload: PasskeyRequest, db=Depends(get_db)):
    return APIResponse(data=await PasskeyService.login_begin(payload.email, db=db), message='Khởi tạo đăng nhập Passkey thành công')

@router.post('/passkey/dang-nhap/hoan-tat', response_model=APIResponse[Any])
async def passkey_login_finish(payload: PasskeyFinishRequest, db=Depends(get_db)):
    return APIResponse(data=await PasskeyService.login_finish(payload.email, payload.credential, db=db), message='Đăng nhập bằng Passkey thành công')
