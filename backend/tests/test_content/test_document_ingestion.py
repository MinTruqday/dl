import pytest
from httpx import AsyncClient
import os

pytestmark = pytest.mark.asyncio(loop_scope='session')

async def test_document_upload_and_ingestion(cloud_client: AsyncClient, content_client: AsyncClient):
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../doc/827-thoi-quen-nguyen-tu-thuviensach.vn.pdf"))
    assert os.path.exists(pdf_path), "Sample PDF file not found!"

    # 1. Upload to Cloud Service
    with open(pdf_path, "rb") as f:
        files = {"file": ("827-thoi-quen-nguyen-tu-thuviensach.vn.pdf", f, "application/pdf")}
        upload_res = await cloud_client.post("/tai-len/tai-lieu", files=files)
        
    assert upload_res.status_code in [200, 201], f"Upload failed: {upload_res.text}"
    upload_data = upload_res.json()
    file_url = upload_data.get("data", {}).get("url", "")
    assert file_url, "File URL not returned by Cloud service"

    import uuid
    random_slug = f"thoi-quen-nguyen-tu-{uuid.uuid4().hex[:8]}"
    # 2. Create Document in Content Service
    doc_payload = {
        "title": "Thói Quen Nguyên Tử",
        "slug": random_slug,
        "description": "Test upload",
        "source_url": file_url,
        "format": "pdf",
        "tags": ["test"],
        "categories": ["test"],
        "is_public": False
    }
    
    create_res = await content_client.post("/tai-lieu", json=doc_payload)
    assert create_res.status_code in [200, 201], f"Document creation failed: {create_res.text}"
    
    doc_data = create_res.json()
    assert "data" in doc_data
    assert doc_data["data"]["title"] == "Thói Quen Nguyên Tử"
