"""
Auto-generated tests for drm based on OpenAPI schema.
"""

import pytest
import httpx
from typing import AsyncGenerator

pytestmark = pytest.mark.asyncio(loop_scope='session')

async def test_auto_acquire_license_drm_kiem_tra_post(drm_client):
    """Test for POST /drm/kiem-tra"""
    response = await drm_client.post('/drm/kiem-tra', json={'file_id': 'string', 'client_public_key': 'string'})

    assert response.status_code < 500

async def test_auto_export_document_pdf_ket_xuat__document_id__drm_get(drm_client):
    """Test for GET /ket-xuat/{document_id}/drm"""
    response = await drm_client.get('/ket-xuat/test_id/drm')

    assert response.status_code < 500

async def test_auto_verify_document_watermark_ket_xuat_giai_ma_truy_vet_post(drm_client):
    """Test for POST /ket-xuat/giai-ma-truy-vet"""
    response = await drm_client.post('/ket-xuat/giai-ma-truy-vet', json={'text': 'string'})

    assert response.status_code < 500

async def test_auto_update_drm_settings_ban_quyen__document_id__put(drm_client):
    """Test for PUT /ban-quyen/{document_id}"""
    response = await drm_client.put('/ban-quyen/test_id', json={'disable_copy': True, 'hide_from_search': True})

    assert response.status_code < 500

async def test_auto_resolve_copyright_dispute_ban_quyen__dispute_id__giai_quyet_post(drm_client):
    """Test for POST /ban-quyen/{dispute_id}/giai-quyet"""
    response = await drm_client.post('/ban-quyen/test_id/giai-quyet', json={})

    assert response.status_code < 500

async def test_auto_health_check_health_get(drm_client):
    """Test for GET /health"""
    response = await drm_client.get('/health')

    assert response.status_code < 500
