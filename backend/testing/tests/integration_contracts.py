import os

import httpx
import jwt


SERVICES = {
    "authentication": os.getenv("AUTH_TEST_URL", "http://authentication:8000"),
    "content": os.getenv("CONTENT_TEST_URL", "http://content:8000"),
    "knowledge": os.getenv("KNOWLEDGE_TEST_URL", "http://ai:8000"),
    "ai": os.getenv("AI_TEST_URL", "http://ai:8000"),
    "testing": os.getenv("TESTING_TEST_URL", "http://testing:8000"),
}


for name, base_url in SERVICES.items():
    with httpx.Client(base_url=base_url, timeout=20) as client:
        health = client.get("/suc-khoe")
        assert health.status_code == 200, f"{name} health contract failed {health.text}"
        schema = client.get("/openapi.json")
        assert schema.status_code == 200, f"{name} schema contract failed {schema.text}"
        assert schema.json().get("paths"), f"{name} exposes no API paths"

with httpx.Client(base_url=SERVICES["testing"], timeout=20) as client:
    unauthenticated = client.get("/kiem-thu/du-an")
    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["error"]["code"] == "AUTH_REQUIRED"
    malformed = client.post(
        "/kiem-thu/du-an",
        headers={
            "Authorization": "Bearer "
            + jwt.encode(
                {"uid": "contract-user", "sub": "contract-user@example.com", "system_role": "USER"},
                os.environ["SECRET_KEY"],
                algorithm="HS256",
            )
        },
        json={"key": "invalid key", "name": ""},
    )
    assert malformed.status_code == 422
    assert malformed.json()["error"]["code"] == "VALIDATION_ERROR"
    paths = client.get("/openapi.json").json()["paths"]
    required = {
        "/kiem-thu/du-an",
        "/kiem-thu/du-an/{project_id}/yeu-cau",
        "/kiem-thu/du-an/{project_id}/ban-nhap-ca-kiem-thu",
        "/kiem-thu/du-an/{project_id}/truy-vet",
        "/kiem-thu/bo-thay-doi/{change_set_id}/phan-tich-anh-huong",
        "/kiem-thu/lan-chay-kiem-thu/{run_id}/bao-cao",
        "/kiem-thu/du-an/{project_id}/yeu-cau/{requirement_id}",
        "/kiem-thu/du-an/{project_id}/yeu-cau/{requirement_id}/tach",
        "/kiem-thu/du-an/{project_id}/yeu-cau/gop",
        "/kiem-thu/du-an/{project_id}/yeu-cau/kiem-tra-trung-lap",
        "/kiem-thu/du-an/{project_id}/ca-kiem-thu/{draft_id}",
        "/kiem-thu/du-an/{project_id}/thuc-thi-kiem-thu/{execution_id}",
        "/kiem-thu/du-an/{project_id}/ket-qua-kiem-thu",
        "/kiem-thu/du-an/{project_id}/anh-chup-do-phu",
        "/kiem-thu/yeu-cau/{requirement_id}/khac-biet",
        "/kiem-thu/ca-kiem-thu/{test_case_id}/truy-vet",
        "/kiem-thu/yeu-cau/{requirement_id}/ngung-hieu-luc",
        "/kiem-thu/ca-kiem-thu/{test_case_id}/nhan-ban",
        "/kiem-thu/ca-kiem-thu/{test_case_id}/ngung-hieu-luc",
        "/kiem-thu/nhap-yeu-cau/{job_id}",
        "/kiem-thu/nhap-yeu-cau/{job_id}/ung-vien/gop",
        "/kiem-thu/nhap-yeu-cau/{job_id}/ung-vien/{candidate_id}/tach",
        "/kiem-thu/nhap-yeu-cau/{job_id}/ung-vien/{candidate_id}/tu-choi",
        "/kiem-thu/tai-lieu-yeu-cau/{document_id}/thu-lai-phan-tich",
        "/kiem-thu/bo-thay-doi/{change_set_id}/ra-soat",
        "/kiem-thu/du-an/{project_id}/du-lieu-kiem-thu",
        "/kiem-thu/du-lieu-kiem-thu/{data_set_id}/phien-ban",
        "/kiem-thu/loi/{defect_id}/ung-vien-truy-vet",
        "/kiem-thu/du-an/{project_id}/ai/loi/{defect_id}/goi-y-truy-vet",
        "/kiem-thu/du-an/{project_id}/loi/{defect_id}/truy-vet",
        "/kiem-thu/de-xuat-bao-tri/{proposal_id}/sinh-lai",
        "/kiem-thu/du-an/{project_id}/hang-loat/nhan",
        "/kiem-thu/du-an/{project_id}/hang-loat/ca-kiem-thu/them-vao-bo-kiem-thu",
        "/kiem-thu/du-an/{project_id}/hang-loat/ca-kiem-thu/danh-dau-can-ra-soat",
        "/kiem-thu/du-an/{project_id}/hang-loat/luu-tru",
        "/kiem-thu/du-an/{project_id}/hang-loat/de-xuat-anh-huong",
        "/kiem-thu/du-an/{project_id}/hang-loat/phe-duyet-de-xuat",
        "/kiem-thu/van-hanh",
        "/kiem-thu/van-hanh/tac-vu/{job_id}/thu-lai",
        "/kiem-thu/du-an/{project_id}/lien-ket-truy-vet",
        "/kiem-thu/du-an/{project_id}/lien-ket-truy-vet/{link_id}/xac-nhan",
        "/kiem-thu/du-an/{project_id}/bo-thay-doi/{change_set_id}/phan-tich-anh-huong",
        "/kiem-thu/phan-tich-anh-huong/{analysis_id}/chay-lai",
        "/kiem-thu/du-an/{project_id}/de-xuat-ai/{proposal_id}/ra-soat",
        "/kiem-thu/du-an/{project_id}/de-xuat-ai/{proposal_id}/phe-duyet",
        "/kiem-thu/du-an/{project_id}/hoi-quy/sinh",
        "/kiem-thu/du-an/{project_id}/hoi-quy/{recommendation_id}/phe-duyet",
        "/kiem-thu/du-an/{project_id}/lan-chay-kiem-thu",
        "/kiem-thu/du-an/{project_id}/lan-chay-kiem-thu/{run_id}",
        "/kiem-thu/du-an/{project_id}/lan-chay-kiem-thu/{run_id}/phan-cong",
        "/kiem-thu/du-an/{project_id}/lan-chay-kiem-thu/{run_id}/tiep-tuc",
        "/kiem-thu/du-an/{project_id}/loi/{defect_id}",
        "/kiem-thu/yeu-cau/{requirement_id}/khoi-phuc",
        "/kiem-thu/du-an/{project_id}/bao-cao/thuc-thi",
        "/kiem-thu/du-an/{project_id}/bao-cao/loi",
        "/kiem-thu/du-an/{project_id}/hoat-dong",
        "/kiem-thu/du-an/{project_id}/ai/hoi-dap",
        "/kiem-thu/yeu-cau/{requirement_id}/phu-thuoc",
        "/kiem-thu/yeu-cau/{requirement_id}/phu-thuoc/{dependency_requirement_id}",
        "/kiem-thu/ke-hoach-kiem-thu/{plan_id}/nhan-ban",
        "/kiem-thu/kich-ban-kiem-thu/{scenario_id}",
        "/kiem-thu/de-xuat-bao-tri/{proposal_id}",
        "/kiem-thu/de-xuat-hoi-quy/{recommendation_id}",
        "/kiem-thu/tai-lieu-yeu-cau/{document_id}/lap-chi-muc-lai",
        "/kiem-thu/du-an/{project_id}/du-lieu-kiem-thu",
        "/kiem-thu/du-lieu-kiem-thu/{data_set_id}/phien-ban",
        "/kiem-thu/du-an/{project_id}/du-lieu-kiem-thu/{data_set_id}/gan-ca-kiem-thu",
        "/kiem-thu/du-an/{project_id}/du-lieu-kiem-thu/{data_set_id}/xem-truoc",
        "/kiem-thu/du-an/{project_id}/du-lieu-kiem-thu/{data_set_id}/luu-tru",
        "/kiem-thu/du-an/{project_id}/mau-ca-kiem-thu",
        "/kiem-thu/mau-ca-kiem-thu/{template_id}",
        "/kiem-thu/mau-ca-kiem-thu/{template_id}/luu-tru",
        "/kiem-thu/du-an/{project_id}/dac-ta-giao-dien",
        "/kiem-thu/du-an/{project_id}/dac-ta-giao-dien/nhap",
        "/kiem-thu/dac-ta-giao-dien/{artifact_id}/ra-soat",
        "/kiem-thu/dac-ta-giao-dien/{artifact_id}/xac-nhan",
        "/kiem-thu/du-an/{project_id}/dac-ta-giao-dien/khac-biet",
        "/kiem-thu/du-an/{project_id}/dac-ta-giao-dien/phan-tich-anh-huong",
        "/kiem-thu/dac-ta-giao-dien/{artifact_id}/luu-tru",
    }
    assert required <= set(paths)

print("service contracts passed")
