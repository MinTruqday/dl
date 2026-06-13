import os
import re
from pathlib import Path

MAP = {
    "dang-nhap": "login",
    "xac-thuc-ma": "verify",
    "dat-lai-mat-khau": "reset-password",
    "dang-ky": "register",
    "quen-mat-khau": "forgot-password",
    "bo-suu-tap": "collection",
    "tai-lieu": "document",
    "thu-thap": "collect",
    "sang-tac": "compose",
    "van-hanh": "operation",
    "thong-bao": "notification",
    "tim-kiem": "search",
    "nguoi-dung": "user",
    "nhat-ky": "audit",
    "dieu-khoan": "terms",
    "ma-uu-dai": "coupon",
    "tro-chuyen": "chat",
    "tinh-chinh": "finetune",
    "ho-so": "profile",
    "cai-dat": "settings",
    "bao-cao": "report",
    "luu-tru": "storage",
    "vi-tien": "wallet",
    "tro-giup": "help",
    "phan-tich": "analytics",
    "cong-tac": "collaboration",
    "thanh-toan": "payment",
    "tin-nhan": "message",
    "khoi-tao": "provision",
    "thu-vien": "library",
    "bieu-ngu": "banner",
    "ban-nhap": "draft",
    "binh-luan": "comment",
    "danh-gia": "review",
    "dau-trang": "bookmark",
    "do-luong": "telemetry",
    "doc": "reading",
    "ghim": "highlight",
    "kham-pha": "discovery",
    "kiem-tien": "monetization",
    "nap-tien": "deposit",
    "neu-bat": "highlight",
    "phan-hoi": "feedback",
    "phien-ban": "version",
    "rut-tien": "withdrawal",
    "soan-thao": "editor",
    "soan-thao-latex": "latex",
    "suy-luan": "inference",
    "tai-len": "upload",
    "tuy-chinh": "setting",
    "xuat-ban": "publication",
    "xuat-tai-lieu": "export",
    "xac-thuc": "auth",
    "bien-dich": "compile",
    "nhan-tin": "contact"
}

BASE_DIR = Path('/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib')
FRONTEND_DIR = BASE_DIR / 'frontend'

# 1. Rename directories
def rename_dirs():
    for group in ['(main)', '(auth)']:
        group_dir = FRONTEND_DIR / 'app' / group
        if group_dir.exists():
            for d in group_dir.iterdir():
                if d.is_dir() and d.name in MAP:
                    new_name = MAP[d.name]
                    new_path = group_dir / new_name
                    # If target exists, just move contents (unlikely but safe)
                    if not new_path.exists():
                        d.rename(new_path)
                        print(f"Renamed folder: {d.name} -> {new_name}")

# 2. String replacement in files
def update_files():
    # regex matches /<word> or }/<word>
    # we want to match boundaries so we don't partially replace
    # we will just replace /key/ with /value/ or /key" or /key' etc
    
    files_to_check = []
    files_to_check.extend(FRONTEND_DIR.rglob('*.ts'))
    files_to_check.extend(FRONTEND_DIR.rglob('*.tsx'))
    
    ingress_file = BASE_DIR / 'k8s' / 'ingress' / 'ingress.yaml'
    if ingress_file.exists():
        files_to_check.append(ingress_file)
        
    docker_compose_file = BASE_DIR / 'docker-compose.yml'
    if docker_compose_file.exists():
        files_to_check.append(docker_compose_file)
        
    for fpath in files_to_check:
        if 'node_modules' in fpath.parts or '.next' in fpath.parts:
            continue
            
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            continue
            
        new_content = content
        for vn, en in MAP.items():
            # Match vn word if it's a path segment. 
            # Example: /vi-tien/so-du -> /wallet/so-du
            # Using capturing group instead of lookbehind because lookbehind requires fixed width in Python
            pattern = r'(/|API_URL\})' + re.escape(vn) + r'(?=[/"\'`?\n\)\(\\]|$)'
            new_content = re.sub(pattern, r'\g<1>' + en, new_content)
            
            # Additional replace for ingress which has path: /vi-tien
            pattern_ingress = r'(path: /)' + re.escape(vn) + r'(?=[/\(]|$)'
            new_content = re.sub(pattern_ingress, r'\g<1>' + en, new_content)
            
        if new_content != content:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated routes in: {fpath.relative_to(BASE_DIR)}")

if __name__ == '__main__':
    rename_dirs()
    update_files()
    print("Translation completed.")
