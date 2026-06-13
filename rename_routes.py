import os
import re

translations = {
    "/bien-dich": "/compile",
    "/bien-doi-van-ban": "/text-transform",
    "/binh-luan": "/comment",
    "/giai-quyet": "/resolve",
    "/cong-viec": "/jobs",
    "/bat-dau": "/start",
    "/danh-gia": "/evaluate",
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
}

def replace_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    
    def replacer(match):
        prefix = match.group(1)
        path = match.group(2)
        suffix = match.group(3)
        
        parts = path.split('/')
        new_parts = []
        for p in parts:
            if p == "":
                new_parts.append("")
                continue
            
            if p.startswith('{') and p.endswith('}'):
                new_parts.append(p)
                continue
                
            p_with_slash = "/" + p
            if p_with_slash in translations:
                new_parts.append(translations[p_with_slash][1:])
            else:
                if path == "/da-doc-tat-ca" and p == "da-doc-tat-ca":
                    new_parts.append("read-all")
                elif path == "/da-doc" and p == "da-doc":
                    new_parts.append("read")
                else:
                    new_parts.append(p)
                
        # Handle special full paths if missed
        new_path = "/".join(new_parts)
        if path == "/da-doc-tat-ca":
            new_path = "/read-all"
        elif path == "/kiem-tra-suc-khoe":
            new_path = "/health"
            
        return prefix + new_path + suffix

    pattern = re.compile(r'(@(?:app|router)\.(?:get|post|put|patch|delete|websocket)\([\'"])(.*?)([\'"](?:,\s*[^)]*)?\))')
    new_content = pattern.sub(replacer, new_content)

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
