import os
import re

comprehensive_translation = {
    # Inference / AI
    "/generate-content": "/tao-noi-dung",
    "/generate-code": "/tao-ma",
    "/analyze-document": "/phan-tich-tai-lieu",
    "/moderate-content": "/kiem-duyet-noi-dung",
    "/smart-citations": "/trich-dan-thong-minh",
    "/text-transform": "/bien-doi-van-ban",
    "/extract-text": "/trich-xuat-van-ban",
    "/synthesize-documents": "/tong-hop-tai-lieu",
    "/synonyms": "/tu-dong-nghia",
    "/check": "/kiem-tra",
    "/check-grammar": "/kiem-tra-ngu-phap",
    "/check-plagiarism": "/kiem-tra-dao-van",
    "/ai-suggestions": "/goi-y-ai",
    # Finetuning & Datasets
    "/finetuning": "/tinh-chinh",
    "/datasets": "/tap-du-lieu",
    "/datasets/{dataset_id}": "/tap-du-lieu/{dataset_id}",
    "/datasets/{dataset_id}/samples": "/tap-du-lieu/{dataset_id}/mau-thu",
    "/datasets/{dataset_id}/samples/{sample_id}": "/tap-du-lieu/{dataset_id}/mau-thu/{sample_id}",
    "/jobs/{job_id}": "/tien-trinh/{job_id}",
    "/jobs/{job_id}/start": "/tien-trinh/{job_id}/bat-dau",
    "/jobs/{job_id}/cancel": "/tien-trinh/{job_id}/huy-bo",
    "/jobs/{job_id}/evaluate": "/tien-trinh/{job_id}/danh-gia",
    "/jobs/{job_id}/deploy": "/tien-trinh/{job_id}/trien-khai",
    "/metrics": "/chi-so",
    # Discovery & Reading
    "/smart-search": "/tim-kiem-thong-minh",
    "/trending": "/thinh-hanh",
    "/trending-hashtags": "/tu-khoa-thinh-hanh",
    "/genres": "/the-loai",
    "/history": "/lich-su",
    "/history/{document_id}": "/lich-su/{document_id}",
    "/progress": "/tien-do",
    "/archive/tree": "/luu-tru/cay-thu-muc",
    "/archive/content": "/luu-tru/noi-dung",
    # Documents & Collaboration
    "/documents": "/tai-lieu",
    "/documents/{document_id}": "/tai-lieu/{document_id}",
    "/documents/{document_id}/activity": "/tai-lieu/{document_id}/hoat-dong",
    "/documents/{document_id}/ping": "/tai-lieu/{document_id}/ping",
    "/documents/{document_id}/online": "/tai-lieu/{document_id}/truc-tuyen",
    "/documents/{document_id}/roles": "/tai-lieu/{document_id}/vai-tro",
    "/documents/{document_id}/messages": "/tai-lieu/{document_id}/tin-nhan",
    "/documents/{document_id}/access": "/tai-lieu/{document_id}/quyen-truy-cap",
    "/documents/{document_id}/versions": "/tai-lieu/{document_id}/phien-ban",
    "/documents/{document_id}/lock": "/tai-lieu/{document_id}/khoa",
    "/documents/{document_id}/unlock": "/tai-lieu/{document_id}/mo-khoa",
    "/documents/{document_id}/lock-status": "/tai-lieu/{document_id}/trang-thai-khoa",
    "/documents/{document_id}/invite-codes": "/tai-lieu/{document_id}/ma-moi",
    "/documents/{document_id}/tasks": "/tai-lieu/{document_id}/cong-viec",
    "/documents/{document_id}/search": "/tai-lieu/{document_id}/tim-kiem",
    "/documents/{document_id}/export": "/tai-lieu/{document_id}/ket-xuat",
    "/documents/{document_id}/pdf": "/tai-lieu/{document_id}/pdf",
    # Collab specific
    "/invitations": "/loi-moi",
    "/invitations/{invite_id}": "/loi-moi/{invite_id}",
    "/{collaboration_id}": "/{collaboration_id}",
    "/{collaboration_id}/roles": "/{collaboration_id}/vai-tro",
    "/join/{invite_code}": "/tham-gia/{invite_code}",
    "/tasks/{task_id}": "/nhiem-vu/{task_id}",
    "/tasks/{task_id}/comments": "/nhiem-vu/{task_id}/binh-luan",
    # Profile & Users
    "/profiles": "/ho-so",
    "/applications/author": "/dang-ky-tac-gia",
    "/upgrade-to-author": "/nang-cap-tac-gia",
    "/settings": "/cai-dat",
    "/brand-page": "/trang-tac-gia",
    "/block/{target_id}": "/chan/{target_id}",
    "/export-data": "/xuat-du-lieu",
    "/auth/passkey": "/xac-thuc/khoa-bao-mat",
    "/email/{email}": "/email/{email}",
    "/slug/{slug}": "/ten-mien/{slug}",
    "/{role}/config": "/{role}/cau-hinh",
    "/{user_id}": "/{user_id}",
    # Misc
    "/config": "/cau-hinh",
    "/images": "/hinh-anh",
    "/feedback": "/phan-hoi",
    "/triggers": "/kich-hoat",
    "/inputs/documents": "/dau-vao/tai-lieu",
    "/inputs/feedback": "/dau-vao/phan-hoi",
    "/ingest": "/nap-du-lieu",
    "/ingestion": "/qua-trinh-nap",
    "/pause": "/tam-dung",
    "/read-all": "/doc-tat-ca",
    "/save/{document_id}": "/luu/{document_id}",
    "/segments": "/phan-doan",
    "/vectors/{document_id}": "/vector/{document_id}",
    "/lists/{list_id}": "/danh-sach/{list_id}",
    "/pins": "/ghim",
    "/{version_id}/restore": "/{version_id}/khoi-phuc",
    "/{highlight_id}": "/{highlight_id}",
    "/{highlight_id}/notes": "/{highlight_id}/ghi-chu",
    "/{notif_id}": "/{notif_id}",
    "/{message_id}": "/{message_id}",
    "/{session_id}": "/{session_id}",
    "/{session_id}/messages": "/{session_id}/tin-nhan",
    "/{session_id}/title": "/{session_id}/tieu-de",
}


def grand_replace(content):
    # Sort keys by length descending to match longest path first
    for eng, vie in sorted(
        comprehensive_translation.items(), key=lambda x: len(x[0]), reverse=True
    ):
        pattern_double = (
            r'(@router\.(?:get|post|put|patch|delete|websocket)\()"{}"'.format(
                re.escape(eng)
            )
        )
        content = re.sub(pattern_double, f'\\1"{vie}"', content)
        pattern_single = (
            r"(@router\.(?:get|post|put|patch|delete|websocket)\()'{}'".format(
                re.escape(eng)
            )
        )
        content = re.sub(pattern_single, f"\\1'{vie}'", content)

        # Also replace prefix
        content = re.sub(f'prefix="{eng}"', f'prefix="{vie}"', content)
        content = re.sub(f"prefix='{eng}'", f"prefix='{vie}'", content)
    return content


for root, _, files in os.walk("."):
    if "venv" in root or "node_modules" in root or ".git" in root or "core" in root:
        continue
    for f in files:
        if f.endswith(".py") and "router" in root:
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()

            new_content = grand_replace(content)

            if new_content != content:
                with open(path, "w", encoding="utf-8") as file:
                    file.write(new_content)
                print(f"Updated {path}")

print("Grand Translation complete.")
