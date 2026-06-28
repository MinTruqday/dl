"""
Auto-generated tests for payment based on OpenAPI schema.
"""

import pytest
import httpx
from typing import AsyncGenerator

pytestmark = pytest.mark.asyncio(loop_scope='session')

async def test_auto_get_my_wallet_vi_dien_tu_so_du_get(payment_client):
    """Test for GET /vi-dien-tu/so-du"""
    response = await payment_client.get('/vi-dien-tu/so-du')

    assert response.status_code < 500

async def test_auto_get_my_transactions_vi_dien_tu_lich_su_get(payment_client):
    """Test for GET /vi-dien-tu/lich-su"""
    response = await payment_client.get('/vi-dien-tu/lich-su')

    assert response.status_code < 500


async def test_auto_create_deposit_nap_tien_post(payment_client):
    """Test for POST /nap-tien"""
    response = await payment_client.post('/nap-tien', json={'amount': 1.0, 'payment_method': 'string'})

    assert response.status_code < 500

async def test_auto_request_withdrawal_rut_tien_post(payment_client):
    """Test for POST /rut-tien"""
    response = await payment_client.post('/rut-tien', json={'amount': 1, 'bank_info': 'string', 'note': {}})

    assert response.status_code < 500

async def test_auto_get_withdrawal_queue_rut_tien_hang_doi_get(payment_client):
    """Test for GET /rut-tien/hang-doi"""
    response = await payment_client.get('/rut-tien/hang-doi')

    assert response.status_code < 500

async def test_auto_verify_withdrawal_rut_tien__withdrawal_id__xac_minh_post(payment_client):
    """Test for POST /rut-tien/{withdrawal_id}/xac-minh"""
    response = await payment_client.post('/rut-tien/test_id/xac-minh', json={})

    assert response.status_code < 500

async def test_auto_purchase_document_kiem_tien_mua_tai_lieu_post(payment_client):
    """Test for POST /kiem-tien/mua/tai-lieu"""
    response = await payment_client.post('/kiem-tien/mua/tai-lieu', json={'document_id': 'string', 'coupon_code': 'string'})

    assert response.status_code < 500

async def test_auto_buy_membership_kiem_tien_thanh_vien_post(payment_client):
    """Test for POST /kiem-tien/thanh-vien"""
    response = await payment_client.post('/kiem-tien/thanh-vien', json={'tier': 'string'})

    assert response.status_code < 500

async def test_auto_get_pricing_config_kiem_tien_bang_gia_get(payment_client):
    """Test for GET /kiem-tien/bang-gia"""
    response = await payment_client.get('/kiem-tien/bang-gia')

    assert response.status_code < 500

async def test_auto_get_author_revenue_kiem_tien_doanh_thu_get(payment_client):
    """Test for GET /kiem-tien/doanh-thu"""
    response = await payment_client.get('/kiem-tien/doanh-thu')

    assert response.status_code < 500

async def test_auto_set_document_pricing_kiem_tien_thiet_lap_gia_put(payment_client):
    """Test for PUT /kiem-tien/thiet-lap-gia"""
    response = await payment_client.put('/kiem-tien/thiet-lap-gia', json={'document_id': 'string', 'price_dl': 1.0, 'is_drm_protected': True})

    assert response.status_code < 500


async def test_auto_health_check_health_get(payment_client):
    """Test for GET /health"""
    response = await payment_client.get('/health')

    assert response.status_code < 500
