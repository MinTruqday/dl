import os

translations = {
    "/bien-dich": "/compile",
    "/bien-doi-van-ban": "/text-transform",
    "/binh-luan": "/comment",
    "/giai-quyet": "/resolve",
    "/cong-viec": "/jobs",
    "/bat-dau": "/start",
    "/danh-gia": "/evaluate", # or evaluate depending on context, I'll use /evaluate for content/evaluate
    "/huy-bo": "/cancel",
    "/trien-khai": "/deploy",
    "/chi-so": "/metrics",
    "/trang-thai": "/status",
    "/dich-thuat": "/translate",
    "/dinh-dang": "/format",
    "/goi-y": "/suggestion",
    "/hanh-dong": "/actions",
    "/kiem-tra-dao-van": "/check-plagiarism",
    "/kiem-tra-ngu-phap": "/check-grammar",
    "/kiem-tra-suc-khoe": "/health",
    "/luong-du-lieu": "/stream",
    "/nap-du-lieu": "/ingest",
    "/nhap": "/input",
    "/phan-hoi": "/feedback",
    "/tai-lieu": "/document",
    "/nhat-ky-he-thong": "/system-logs",
    "/noi-bo": "/internal",
    "/cong-viec-dang-chay": "/running-jobs",
    "/kich-hoat": "/trigger",
    "/phan-tich-cam-xuc": "/sentiment-analysis",
    "/phan-tich-tai-lieu": "/document-analysis",
    "/tai-xuong-zip": "/download-zip",
    "/tam-dung": "/pause",
    "/tao-ma-nguon": "/generate-code",
    "/tao-noi-dung": "/generate-content",
    "/tap-du-lieu": "/dataset",
    "/mau": "/sample",
    "/tham-dinh-noi-dung": "/content-moderation",
    "/thong-ke": "/statistics",
    "/tom-tat": "/summarize",
    "/tong-hop-da-tai-lieu": "/multi-doc-synthesis",
    "/trich-dan-thong-minh": "/smart-citation",
    "/trich-xuat-van-ban": "/extract-text",
    "/tro-chuyen": "/chat",
    "/tu-dong-nghia": "/synonyms",
    "/xuat-zip": "/export-zip",
    "/xuat": "/export",
    "/dong-bo-thao-tac": "/sync-action",
    "/goi-y-ai": "/ai-suggest",
    "/gui-duyet": "/submit-review",
    "/kiem-tra-logic": "/check-logic",
    "/phan-tich-the": "/analyze-tags",
    "/so-sanh-phien-ban": "/compare-version",
    "/thay-the-toan-cuc": "/replace-all",
    "/tu-dong-luu": "/auto-save",
    "/da-doc": "/read",
    "/da-doc-tat-ca": "/read-all",
    "/nguoi-dung": "/user",
    "/tao-moi": "/create",
    "/thong-bao": "/notification",
    "/ca-nhan": "/personal",
    "/thung-rac": "/trash",
    "/khoi-phuc": "/restore",
    "/phan-tich": "/analyze",
    "/roi-rot": "/dropoff",
    "/thu-thap": "/collect",
    "/tai-lieu-chia-se": "/shared-document",
    "/nhieu-nguoi-dung": "/multiple-users",
    "/chuoi-tai-lieu": "/document-series",
    "/thong-ke-dong-gop": "/contribution-stats",
    "/danh-sach": "/list"
}

# Sort by length descending to replace longest paths first (e.g., /da-doc-tat-ca before /da-doc)
sorted_translations = sorted(translations.items(), key=lambda x: len(x[0]), reverse=True)

def replace_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for vn, en in sorted_translations:
        # replace occurrences safely
        new_content = new_content.replace(vn, en)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, _, files in os.walk('backend'):
    if '.venv' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            replace_in_file(os.path.join(root, file))
