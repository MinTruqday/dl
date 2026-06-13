import os
import re

BACKEND_DIR = "backend"

# Folders to add suffixes to
SUFFIX_MAP = {
    "api": "_router",
    "services": "_service",
    "schemas": "_schema"
}

route_map = {
    # Finance
    "vi-tien": "wallet",
    "nap-tien": "deposit",
    "rut-tien": "withdrawal",
    "ma-uu-dai": "coupon",
    "kiem-tien": "monetization",
    "so-du": "balance",
    "ma-qua-tang": "coupon-code",
    "doi-ma": "redeem",
    "lich-su": "history",
    "doanh-thu": "revenue",
    "giao-dich-mua": "purchase",
    
    # Auth
    "dinh-danh": "auth",
    "mat-khau": "password",
    "dang-nhap": "login",
    "dang-ky": "register",
    
    # Agentic AI
    "suy-luan": "inference",
    "tro-chuyen": "chat",
    "nap-du-lieu": "ingest",
    "phan-hoi": "feedback",
    "huan-luyen": "finetune",
    "tieu-de": "title",
    
    # Content
    "tai-lieu": "document",
    "danh-gia": "review",
    "phien-ban": "version",
    "doc-tai-lieu": "reading",
    "danh-dau": "bookmark",
    "thu-vien": "library",
    "tai-len": "upload",
    "kham-pha": "discovery",
    "xuat-ban": "export",
    "cong-tac": "collaboration",
    "xuat-ban-an": "publication",
    "luu-tru": "storage",
    "bo-suu-tap": "collection",
    "lam-noi-bat": "highlight",
    
    # Compiler / Editor
    "don-dep": "cleanup",
    "bien-dich-xem-truoc": "compile-preview",
    "dinh-dang": "format",
    
    # Websocket / Contact
    "tin-nhan": "message",
    "nhan-tin": "contact",
    "giai-dap": "solve",
    "nhom": "group",
    "chia-se-tai-lieu": "share-doc",
    "tai-lieu-chia-se": "shared-docs",
    "doc-tin-nhan": "read-message",
    "bo-chan": "unblock",
    "chan": "block",
    "trang-thai-chan": "block-status",
    "ghim-hoi-thoai": "pin-conversation",
    "dich": "translate",
    "nhap-tin-nhan": "typing",
    "tu-huy": "self-destruct",
    "tat-am": "mute",
    
    # Provision
    "so-lieu": "metrics",
    "cau-hinh": "settings",
    "thung-rac": "trash",
    "nguoi-dung": "user",
    "nhat-ky": "audit",
    "hoat-dong": "operation",
    "han-muc": "quota",
}


def build_rename_map():
    rename_map = {}
    import_map = {} # Maps old import string to new import string
    
    for service_name in os.listdir(BACKEND_DIR):
        service_path = os.path.join(BACKEND_DIR, service_name)
        src_path = os.path.join(service_path, "src")
        
        if not os.path.isdir(src_path):
            continue
            
        for folder, suffix in SUFFIX_MAP.items():
            folder_path = os.path.join(src_path, folder)
            if not os.path.isdir(folder_path):
                continue
                
            for filename in os.listdir(folder_path):
                if filename.endswith(".py") and filename != "__init__.py":
                    base_name = filename[:-3]
                    
                    # If already has the suffix, skip renaming but keep it in mind
                    if base_name.endswith(suffix):
                        continue
                        
                    new_base_name = base_name + suffix
                    new_filename = new_base_name + ".py"
                    
                    old_path = os.path.join(folder_path, filename)
                    new_path = os.path.join(folder_path, new_filename)
                    
                    rename_map[old_path] = new_path
                    
                    # Calculate import strings
                    # from src.api.wallet import ... -> from src.api.wallet_router import ...
                    # import src.api.wallet -> import src.api.wallet_router
                    
                    old_import_module = f"src.{folder}.{base_name}"
                    new_import_module = f"src.{folder}.{new_base_name}"
                    
                    import_map[old_import_module] = new_import_module
                    
                    # Also handle relative imports inside the same microservice
                    # e.g. from .wallet import ...
                    import_map[f"from .{base_name} import"] = f"from .{new_base_name} import"
                    
    return rename_map, import_map


def apply_refactor(rename_map, import_map):
    # 1. Update file contents
    for root, dirs, files in os.walk(BACKEND_DIR):
        for file in files:
            if not file.endswith(".py"):
                continue
                
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            new_content = content
            
            # Apply import replacements
            for old_import, new_import in import_map.items():
                # Replace exact module matches in from/import statements
                new_content = re.sub(rf'\bfrom {old_import}\b', f'from {new_import}', new_content)
                new_content = re.sub(rf'\bimport {old_import}\b', f'import {new_import}', new_content)
                
            # Apply route translations
            for vn, en in route_map.items():
                # We want to match things like "/vi-tien" or "/vi-tien/" or "/vi-tien/so-du"
                # using regex to ensure we only replace full path segments.
                pattern = r'(/|prefix=")' + re.escape(vn) + r'(?=[/"\'?\n\)\(\\]|$)'
                new_content = re.sub(pattern, r'\g<1>' + en, new_content)
                
            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated contents: {file_path}")
                
    # 2. Rename files
    for old_path, new_path in rename_map.items():
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            print(f"Renamed: {old_path} -> {new_path}")

    # 3. Create repositories directories
    for service_name in os.listdir(BACKEND_DIR):
        service_path = os.path.join(BACKEND_DIR, service_name)
        src_path = os.path.join(service_path, "src")
        
        if os.path.isdir(src_path):
            repo_path = os.path.join(src_path, "repositories")
            if not os.path.exists(repo_path):
                os.makedirs(repo_path)
                # Create empty __init__.py
                with open(os.path.join(repo_path, "__init__.py"), "w") as f:
                    pass
                print(f"Created repository directory: {repo_path}")


if __name__ == "__main__":
    rename_map, import_map = build_rename_map()
    apply_refactor(rename_map, import_map)
    print("Refactoring completed.")
