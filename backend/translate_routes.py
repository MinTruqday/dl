import os
import re

prefix_translations = {
    "/notifications": "/thong-bao",
    "/ingest": "/nap-du-lieu",
    "/chat": "/tro-chuyen",
    "/inference": "/suy-luan",
    "/finetune": "/tinh-chinh",
    "/collectors": "/thu-thap",
    "/users": "/nguoi-dung",
    "/audit": "/kiem-toan",
    "/profile": "/ho-so",
    "/quota": "/han-muc",
    "/telemetry": "/giam-sat",
    "/operations": "/van-hanh",
    "/banners": "/quang-cao",
    "/pin": "/ghim",
    "/versions": "/phien-ban",
    "/library": "/thu-vien",
    "/upload": "/tai-len",
    "/discovery": "/kham-pha",
    "/reading": "/doc-hieu",
    "/export": "/ket-xuat",
    "/reviews": "/danh-gia",
    "/bookmarks": "/danh-dau",
    "/collaboration": "/cong-tac",
    "/documents": "/tai-lieu",
    "/publications": "/xuat-ban",
    "/storage": "/luu-tru",
    "/highlights": "/danh-dau-dong",
    "/drafts": "/ban-nhap",
    "/editor": "/trinh-soan-thao",
    "/messages": "/tin-nhan",
    "/withdrawals": "/rut-tien",
    "/deposits": "/nap-tien",
    "/coupons": "/ma-giam-gia",
    "/monetization": "/kiem-tien",
    "/wallets": "/vi-tien",
    "/auth": "/xac-thuc",
    "/passkeys": "/khoa-xac-thuc",
    "/editorjs": "/soan-thao-editorjs",
    "/latex": "/soan-thao-latex",
    "/privacy": "/quyen-rieng-tu",
}

path_translations = {
    "/mark-read": "/danh-dau-da-doc",
    "/{notif_id}/read": "/{notif_id}/doc-hieu",
    "/unread-count": "/so-luong-chua-doc",
    "/{notif_id}/dismiss": "/{notif_id}/bo-qua",
    "/clear-all": "/xoa-tat-ca",
    "/mark-all-read": "/danh-dau-da-doc-tat-ca",
    "/preferences": "/tuy-chon",
    "/subscribe": "/dang-ky",
    "/batch": "/hang-loat",
    "/trigger": "/kich-hoat",
    "/dispatch": "/gui-di",
    "/me": "/ca-nhan",
    "/forgot-password": "/quen-mat-khau",
    "/reset-password": "/dat-lai-mat-khau",
    "/verify-code": "/xac-nhan-ma",
    "/login/start": "/dang-nhap/bat-dau",
    "/login/finish": "/dang-nhap/hoan-tat",
    "/google/login": "/google/dang-nhap",
    "/google/callback": "/google/phan-hoi",
    "/search": "/tim-kiem",
    "/role": "/vai-tro",
    "/status": "/trang-thai",
    "/warn": "/canh-bao",
    "/lock": "/khoa",
    "/shadowban": "/cam-ngam",
    "/kyc": "/xac-minh-danh-tinh",
    "/notes": "/ghi-chu",
    "/reports": "/bao-cao",
    "/reports/{report_id}": "/bao-cao/{report_id}",
    "/activity-log": "/nhat-ky-hoat-dong",
    "/logs": "/nhat-ky-hoat-dong",
    "/by-email/{email}": "/theo-email/{email}",
    "/by-email/{invitee_email}": "/theo-email/{invitee_email}",
    "/by-email/{username}": "/theo-email/{username}",
    "/by-slug/{slug}": "/theo-ten-mien/{slug}",
    "/by-slug/{username}": "/theo-ten-mien/{username}",
    "/trash": "/thung-rac",
    "/personal": "/ca-nhan",
    "/recent": "/gan-day",
    "/stats": "/thong-ke",
    "/{document_id}/restore": "/{document_id}/khoi-phuc",
    "/{document_id}/content": "/{document_id}/noi-dung",
    "/{document_id}/publish": "/{document_id}/xuat-ban",
    "/{document_id}/unpublish": "/{document_id}/huy-xuat-ban",
    "/{document_id}/password": "/{document_id}/mat-khau",
    "/{document_id}/transfer": "/{document_id}/chuyen-nhuong",
    "/{document_id}/tags": "/{document_id}/the",
    "/{document_id}/academic-index": "/{document_id}/chi-so-hoc-thuat",
    "/{document_id}/readability": "/{document_id}/do-de-doc",
    "/{document_id}/sync": "/{document_id}/dong-bo",
    "/{document_id}/plagiarism-check": "/{document_id}/kiem-tra-dao-van",
    "/{document_id}/check-grammar": "/{document_id}/kiem-tra-ngu-phap",
    "/{document_id}/check-logic": "/{document_id}/kiem-tra-logic",
    "/{document_id}/summarize": "/{document_id}/tom-tat",
    "/{document_id}/extract-tags": "/{document_id}/trich-xuat-the",
    "/{document_id}/compare-versions": "/{document_id}/so-sanh-phien-ban",
    "/{document_id}/ai-suggestions": "/{document_id}/goi-y-ai",
    "/{document_id}/comments": "/{document_id}/binh-luan",
    "/{document_id}/find-replace": "/{document_id}/tim-va-thay-the",
    "/{document_id}/auto-save": "/{document_id}/tu-dong-luu",
    "/folders": "/thu-muc",
    "/files": "/tap-tin",
    "/files/{item_id}": "/tap-tin/{item_id}",
    "/files/{item_id}/share": "/tap-tin/{item_id}/chia-se",
    "/shares/{share_token}": "/chia-se/{share_token}",
    "/lists": "/danh-sach",
    "/download-archive": "/tai-ve-luu-tru",
    "/purchase/document": "/mua/tai-lieu",
    "/membership": "/thanh-vien",
    "/pricing": "/bang-gia",
    "/balance": "/so-du",
    "/transactions": "/giao-dich",
    "/revenue": "/doanh-thu",
    "/queue": "/hang-doi",
    "/{withdrawal_id}/verify": "/{withdrawal_id}/xac-minh",
    "/{withdrawal_id}/process": "/{withdrawal_id}/xu-ly",
    "/redeem": "/su-dung",
    "/conversations": "/cuoc-tro-chuyen",
    "/{message_id}/pin": "/{message_id}/ghim",
    "/{message_id}/reactions": "/{message_id}/bay-to-cam-xuc",
    "/{message_id}/translate": "/{message_id}/dich-thuat",
    "/{other_user_id}/read": "/{other_user_id}/doc-hieu",
    "/{other_user_id}/block": "/{other_user_id}/chan",
    "/{other_user_id}/unblock": "/{other_user_id}/bo-chan",
    "/{other_user_id}/block-status": "/{other_user_id}/trang-thai-chan",
    "/conversations/{other_user_id}/pin": "/cuoc-tro-chuyen/{other_user_id}/ghim",
    "/{other_user_id}/drafts": "/{other_user_id}/ban-nhap",
    "/{other_user_id}/self-destruct": "/{other_user_id}/tu-huy",
    "/{other_user_id}/mute": "/{other_user_id}/tat-thong-bao",
    "/{other_user_id}/settings": "/{other_user_id}/cai-dat",
    "/{receiver_id}/documents/share": "/{receiver_id}/tai-lieu/chia-se",
    "/{other_user_id}/documents/shared": "/{other_user_id}/tai-lieu/da-chia-se",
    "/groups": "/nhom",
    "/active-jobs": "/cong-viec-dang-chay",
    "/active-processes": "/tien-trinh-dang-chay",
    "/stop": "/dung",
    "/compile": "/bien-dich",
    "/format": "/dinh-dang",
    "/export-zip": "/ket-xuat-zip",
    "/pomodoro": "/dong-ho-pomodoro",
    "/chunk": "/phan-chia",
    "/embed": "/nhung",
    "/index": "/danh-muc",
    "/{doc_id}/stream": "/{doc_id}/phat-truc-tiep",
    "/translate": "/dich-thuat",
    "/summarize": "/tom-tat",
    "/grammar": "/ngu-phap",
    "/extract": "/trich-xuat",
    "/detect": "/nhan-dien",
    "/moderate": "/kiem-duyet",
    "/jobs": "/cong-viec",
    "/{job_id}/status": "/{job_id}/trang-thai",
    "/{job_id}/cancel": "/{job_id}/huy-bo",
    "/{job_id}/metrics": "/{job_id}/chi-so",
    "/{collector_id}/logs": "/{collector_id}/nhat-ky-hoat-dong",
    "/crdt/{document_id}": "/crdt/{document_id}",  # remain
    "/suggestions/{suggestion_id}/resolve": "/goi-y/{suggestion_id}/giai-quyet",
    "/{document_id}/suggestions": "/{document_id}/goi-y",
    "/{document_id}/submit-review": "/{document_id}/gui-danh-gia",
    "/comments/{comment_id}/resolve": "/binh-luan/{comment_id}/giai-quyet",
}


def translate_prefixes(content):
    for eng, vie in prefix_translations.items():
        content = re.sub(f'prefix="{eng}"', f'prefix="{vie}"', content)
        content = re.sub(f"prefix='{eng}'", f"prefix='{vie}'", content)
    return content


def translate_routes(content):
    for eng, vie in path_translations.items():
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
    return content


def translate_httpx_calls(content):
    # This matches f"{settings.XXX_URL}/eng/eng"
    # We will build a replacement table for known full paths
    full_path_replacements = {
        "/wallets/balance": "/vi-tien/so-du",
        "/wallets/transactions": "/vi-tien/giao-dich",
        "/coupons/redeem": "/ma-giam-gia/su-dung",
        "/withdrawals/revenue": "/rut-tien/doanh-thu",
        "/documents/personal": "/tai-lieu/ca-nhan",
        "/documents/trash": "/tai-lieu/thung-rac",
        "/documents/{document_id}/restore": "/tai-lieu/{document_id}/khoi-phuc",
        "/documents/{document_id}/analyze/dropoff": "/tai-lieu/{document_id}/phan-tich/bo-do",
        "/documents/": "/tai-lieu/",
        "/documents/{document_id}": "/tai-lieu/{document_id}",
        "/documents/{doc_id}": "/tai-lieu/{doc_id}",
        "/deposits": "/nap-tien",
        "/profile/me": "/ho-so/ca-nhan",
        "/inference/translate": "/suy-luan/dich-thuat",
        "/quota/verify": "/han-muc/xac-minh",
        "/quota/consume": "/han-muc/su-dung",
        "/notifications/trigger": "/thong-bao/kich-hoat",
        "/notifications/dispatch": "/thong-bao/gui-di",
        "/stats": "/thong-ke",
        "/trigger": "/kich-hoat",
        "/stop": "/dung",
        "/logs": "/nhat-ky-hoat-dong",
        "/active-jobs": "/cong-viec-dang-chay",
        "/active-processes": "/tien-trinh-dang-chay",
        "/withdrawals/queue": "/rut-tien/hang-doi",
        "/withdrawals/{withdrawal_id}/verify": "/rut-tien/{withdrawal_id}/xac-minh",
        "/users/by-email/{invitee_email}": "/nguoi-dung/theo-email/{invitee_email}",
        "/users/by-email/{email}": "/nguoi-dung/theo-email/{email}",
        "/users/by-email/{username}": "/nguoi-dung/theo-email/{username}",
        "/users/by-slug/{username}": "/nguoi-dung/theo-ten-mien/{username}",
        "/users/{target_user_id}": "/nguoi-dung/{target_user_id}",
        "/users/{current_user.id}": "/nguoi-dung/{current_user.id}",
        "/users/{new_owner_id}": "/nguoi-dung/{new_owner_id}",
        "/users/batch": "/nguoi-dung/hang-loat",
        "/users": "/nguoi-dung",
        "/translate": "/dich-thuat",
    }

    # We iterate over full paths in reverse length order to match specific ones first
    for eng, vie in sorted(
        full_path_replacements.items(), key=lambda x: len(x[0]), reverse=True
    ):
        # We look for something like {settings.MANAGEMENT_URL}/nguoi-dung
        pattern = r"(\{(?:settings|config)\.[A-Z_]+_URL\})" + re.escape(eng)
        content = re.sub(pattern, f"\\1{vie}", content)
    return content


for root, _, files in os.walk("."):
    if "venv" in root or "node_modules" in root or ".git" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()

                new_content = content
                if "router" in root:
                    new_content = translate_prefixes(new_content)
                    new_content = translate_routes(new_content)

                    # Fix /chat/chat problem by removing duplication
                    # If prefix is /tro-chuyen and endpoint is /tro-chuyen
                    # Wait, let's just do it explicitly for chat.py if it exists
                    if "agentic_ai/src/router/chat.py" in path:
                        new_content = new_content.replace(
                            '@router.post("/tro-chuyen"', '@router.post(""'
                        )
                        new_content = new_content.replace(
                            '@router.post("/chat"', '@router.post(""'
                        )

                # Fix internal httpx calls globally
                new_content = translate_httpx_calls(new_content)

                if new_content != content:
                    with open(path, "w", encoding="utf-8") as file:
                        file.write(new_content)
                    print(f"Updated {path}")
            except Exception as e:
                pass
print("Translation complete.")
