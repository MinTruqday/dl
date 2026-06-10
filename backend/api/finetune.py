from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Query, HTTPException, Request, status
from api.dependency import get_db, get_current_user
from models.user import UserInDB
from core.config import settings
import httpx
from loguru import logger
router = APIRouter(prefix='/tinh-chinh')
AGENTIC_AI_URL = settings.AGENTIC_AI_URL

async def proxy_request(method: str, path: str, current_user: UserInDB, payload: dict=None, params: dict=None, success_message: str='Thành công'):
    url = f'{AGENTIC_AI_URL}/finetune{path}'
    headers = {'Content-Type': 'application/json'}
    if payload is None:
        payload = {}
    payload['user_id'] = str(current_user.id)
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            if method.upper() == 'GET':
                req_params = params or {}
                req_params['user_id'] = str(current_user.id)
                resp = await client.get(url, params=req_params, headers=headers)
            elif method.upper() == 'POST':
                resp = await client.post(url, json=payload, headers=headers)
            elif method.upper() == 'DELETE':
                req_params = params or {}
                req_params['user_id'] = str(current_user.id)
                resp = await client.delete(url, params=req_params, headers=headers)
            else:
                raise ValueError(f'Method {method} not supported')
            if resp.status_code != 200:
                error_detail = 'Dịch vụ AI phản hồi lỗi'
                try:
                    error_detail = resp.json().get('detail', error_detail)
                except:
                    pass
                raise HTTPException(status_code=resp.status_code, detail=error_detail)
            data = resp.json()
            if isinstance(data, dict) and 'error' in data:
                if data['error'] == 'insufficient_samples':
                    return APIResponse(message='Tập dữ liệu cần tối thiểu 10 mẫu huấn luyện.', status=400)
                return APIResponse(message=data['error'], status=400)
            return APIResponse(data=data, message=success_message, status=200 if method.upper() == 'GET' else 201)
    except httpx.RequestError as e:
        logger.error(f'Finetune proxy error: {e}')
        raise HTTPException(status_code=503, detail='Không thể kết nối đến máy chủ AI.')

@router.post('/tap-du-lieu', response_model=APIResponse[Any])
async def create_dataset(req: dict, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    name = req.get('name')
    if not name:
        return APIResponse(message='Vui lòng nhập tên tập dữ liệu.', status=400)
    return await proxy_request('POST', '/dataset', current_user, payload=req, success_message='Tạo tập dữ liệu thành công.')

@router.get('/tap-du-lieu', response_model=APIResponse[Any])
async def list_datasets(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return await proxy_request('GET', '/dataset', current_user, success_message='Lấy danh sách tập dữ liệu thành công.')

@router.get('/tap-du-lieu/{dataset_id}', response_model=APIResponse[Any])
async def get_dataset(dataset_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return await proxy_request('GET', f'/dataset/{dataset_id}', current_user, success_message='Lấy tập dữ liệu thành công.')

@router.delete('/tap-du-lieu/{dataset_id}', response_model=APIResponse[Any])
async def delete_dataset(dataset_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return await proxy_request('DELETE', f'/dataset/{dataset_id}', current_user, success_message='Xóa tập dữ liệu thành công.')

@router.post('/tap-du-lieu/{dataset_id}/mau', response_model=APIResponse[Any])
async def add_samples(dataset_id: str, req: dict, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    if not req.get('samples'):
        return APIResponse(message='Danh sách mẫu không được trống.', status=400)
    return await proxy_request('POST', f'/dataset/{dataset_id}/samples', current_user, payload=req, success_message='Thêm mẫu huấn luyện thành công.')

@router.get('/tap-du-lieu/{dataset_id}/mau', response_model=APIResponse[Any])
async def get_samples(dataset_id: str, skip: int=Query(0), limit: int=Query(50), current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return await proxy_request('GET', f'/dataset/{dataset_id}/samples', current_user, params={'skip': skip, 'limit': limit}, success_message='Lấy danh sách mẫu thành công.')

@router.delete('/tap-du-lieu/{dataset_id}/mau/{sample_id}', response_model=APIResponse[Any])
async def delete_sample(dataset_id: str, sample_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return await proxy_request('DELETE', f'/dataset/{dataset_id}/samples/{sample_id}', current_user, success_message='Xóa mẫu thành công.')

@router.post('/nhap-tu-phan-hoi', response_model=APIResponse[Any])
async def import_from_feedback(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return await proxy_request('POST', '/import/feedback', current_user, success_message='Nhập dữ liệu từ phản hồi thành công.')

@router.post('/nhap-tu-tai-lieu', response_model=APIResponse[Any])
async def import_from_documents(req: dict, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    if not req.get('document_ids'):
        return APIResponse(message='Danh sách tài liệu không được trống.', status=400)
    return await proxy_request('POST', '/import/documents', current_user, payload=req, success_message='Nhập dữ liệu từ tài liệu thành công.')

@router.post('/cong-viec', response_model=APIResponse[Any])
async def create_job(req: dict, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    if not req.get('dataset_id'):
        return APIResponse(message='Vui lòng chọn tập dữ liệu.', status=400)
    if 'base_model' not in req or not req['base_model']:
        req['base_model'] = getattr(settings, 'LLAMA_MODEL', 'llama3.1')
    return await proxy_request('POST', '/job', current_user, payload=req, success_message='Tạo công việc tinh chỉnh thành công.')

@router.post('/cong-viec/{job_id}/bat-dau', response_model=APIResponse[Any])
async def start_training(job_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return await proxy_request('POST', f'/job/{job_id}/start', current_user, success_message='Bắt đầu huấn luyện thành công.')

@router.get('/cong-viec', response_model=APIResponse[Any])
async def list_jobs(current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return await proxy_request('GET', '/job', current_user, success_message='Lấy danh sách công việc thành công.')

@router.get('/cong-viec/{job_id}', response_model=APIResponse[Any])
async def get_job(job_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return await proxy_request('GET', f'/job/{job_id}', current_user, success_message='Lấy trạng thái công việc thành công.')

@router.post('/cong-viec/{job_id}/huy', response_model=APIResponse[Any])
async def cancel_job(job_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return await proxy_request('POST', f'/job/{job_id}/cancel', current_user, success_message='Đã hủy công việc tinh chỉnh.')

@router.post('/cong-viec/{job_id}/trien-khai', response_model=APIResponse[Any])
async def deploy_model(job_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return await proxy_request('POST', f'/job/{job_id}/deploy', current_user, success_message='Triển khai mô hình thành công.')

@router.post('/cong-viec/{job_id}/danh-gia', response_model=APIResponse[Any])
async def evaluate_model(job_id: str, req: dict, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    if not req.get('test_samples'):
        return APIResponse(message='Danh sách mẫu đánh giá không được trống.', status=400)
    return await proxy_request('POST', f'/job/{job_id}/evaluate', current_user, payload=req, success_message='Đánh giá mô hình thành công.')

@router.post('/cap-nhat-tien-trinh', response_model=APIResponse[Any])
async def update_progress(req: dict, db=Depends(get_db)):
    return APIResponse(data={}, message='Cập nhật tiến trình thành công.', status=200)