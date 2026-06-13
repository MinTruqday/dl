import os
import shutil
import json
from pathlib import Path

# Base paths
FRONTEND_DIR = Path('/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/frontend')

if not FRONTEND_DIR.exists():
    print("Frontend directory not found!")
    exit(1)

# 1. Directory Structure Definition
DIRS = [
    "shared/components/ui",
    "shared/components/common",
    "shared/contexts",
    "shared/lib",
    "features/auth/components",
    "features/auth/services",
    "features/auth/contexts",
    "features/finance/components",
    "features/finance/services",
    "features/communication/components",
    "features/communication/services",
    "features/editor/components",
    "features/editor/services",
    "features/ai/components",
    "features/ai/services",
    "features/content/components",
    "features/content/services",
    "features/provision/components",
    "features/provision/services",
]

for d in DIRS:
    (FRONTEND_DIR / d).mkdir(parents=True, exist_ok=True)

# 2. File Movement Map (Source -> Destination)
MOVE_MAP = {
    # Shared
    "components/ui": "shared/components/ui", # directory
    "lib/utils.ts": "shared/lib/utils.ts",
    "contexts/Theme.tsx": "shared/contexts/Theme.tsx",
    "contexts/Toast.tsx": "shared/contexts/Toast.tsx",
    "contexts/Notification.tsx": "shared/contexts/Notification.tsx",
    "components/Toast.tsx": "shared/components/common/Toast.tsx",
    "components/Navigation.tsx": "shared/components/common/Navigation.tsx",
    "components/Menu.tsx": "shared/components/common/Menu.tsx",

    # Auth
    "components/Passkey.tsx": "features/auth/components/Passkey.tsx",
    "contexts/Auth.tsx": "features/auth/contexts/Auth.tsx",
    "services/authentication.service.ts": "features/auth/services/authentication.service.ts",
    "services/passkey.service.ts": "features/auth/services/passkey.service.ts",

    # Finance
    "services/wallet.service.ts": "features/finance/services/wallet.service.ts",
    "services/deposit.service.ts": "features/finance/services/deposit.service.ts",
    "services/withdrawal.service.ts": "features/finance/services/withdrawal.service.ts",
    "services/coupon.service.ts": "features/finance/services/coupon.service.ts",
    "services/monetization.service.ts": "features/finance/services/monetization.service.ts",

    # Communication
    "components/Comment.tsx": "features/communication/components/Comment.tsx",
    "services/comment.service.ts": "features/communication/services/comment.service.ts",
    "services/notification.service.ts": "features/communication/services/notification.service.ts",

    # Editor
    "components/editor": "features/editor/components", # directory
    "services/editor.service.ts": "features/editor/services/editor.service.ts",
    "services/latex.service.ts": "features/editor/services/latex.service.ts",
    "services/compilation.service.ts": "features/editor/services/compilation.service.ts",

    # AI
    "services/ai.service.ts": "features/ai/services/ai.service.ts",
    "services/rag.service.ts": "features/ai/services/rag.service.ts",
    "services/inference.service.ts": "features/ai/services/inference.service.ts",
    "services/finetune.service.ts": "features/ai/services/finetune.service.ts",
    "services/chat.service.ts": "features/ai/services/chat.service.ts",

    # Content
    "components/Review.tsx": "features/content/components/Review.tsx",
    "components/Workspace.tsx": "features/content/components/Workspace.tsx",
    "services/document.service.ts": "features/content/services/document.service.ts",
    "services/review.service.ts": "features/content/services/review.service.ts",
    "services/reading.service.ts": "features/content/services/reading.service.ts",
    "services/library.service.ts": "features/content/services/library.service.ts",
    "services/bookmark.service.ts": "features/content/services/bookmark.service.ts",
    "services/highlight.service.ts": "features/content/services/highlight.service.ts",
    "services/draft.service.ts": "features/content/services/draft.service.ts",
    "services/version.service.ts": "features/content/services/version.service.ts",
    "services/publication.service.ts": "features/content/services/publication.service.ts",
    "services/discovery.service.ts": "features/content/services/discovery.service.ts",
    "services/storage.service.ts": "features/content/services/storage.service.ts",
    "services/upload.service.ts": "features/content/services/upload.service.ts",
    "services/collaboration.service.ts": "features/content/services/collaboration.service.ts",

    # Provision
    "components/Report.tsx": "features/provision/components/Report.tsx",
    "services/user.service.ts": "features/provision/services/user.service.ts",
    "services/profile.service.ts": "features/provision/services/profile.service.ts",
    "services/audit.service.ts": "features/provision/services/audit.service.ts",
    "services/quota.service.ts": "features/provision/services/quota.service.ts",
    "services/setting.service.ts": "features/provision/services/setting.service.ts",
    "services/telemetry.service.ts": "features/provision/services/telemetry.service.ts",
    "services/report.service.ts": "features/provision/services/report.service.ts",
    "services/collector.service.ts": "features/provision/services/collector.service.ts",
    "services/banner.service.ts": "features/provision/services/banner.service.ts",
    "services/operation.service.ts": "features/provision/services/operation.service.ts",
    "services/feedback.service.ts": "features/provision/services/feedback.service.ts",
    "services/export.service.ts": "features/provision/services/export.service.ts",
}

IMPORT_REPLACE_MAP = {}

for src, dst in MOVE_MAP.items():
    src_path = FRONTEND_DIR / src
    dst_path = FRONTEND_DIR / dst
    if src_path.exists():
        if src_path.is_dir():
            if not dst_path.exists():
                shutil.move(str(src_path), str(dst_path))
            else:
                for item in src_path.iterdir():
                    shutil.move(str(item), str(dst_path))
                src_path.rmdir()
        else:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dst_path))
    
    # Generate import mapping (without extension)
    src_base = src.replace('.tsx', '').replace('.ts', '')
    dst_base = dst.replace('.tsx', '').replace('.ts', '')
    
    # E.g. @/components/ui -> @/shared/components/ui
    IMPORT_REPLACE_MAP[f"@/{src_base}"] = f"@/{dst_base}"

# Additional catch-alls for specific directory moves to ensure sub-file imports are replaced
IMPORT_REPLACE_MAP["@/components/ui/"] = "@/shared/components/ui/"
IMPORT_REPLACE_MAP["@/components/editor/"] = "@/features/editor/components/"

# 3. String Replacement in all .ts, .tsx files
def update_imports(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return
    
    new_content = content
    # Replace longer strings first to avoid partial matches
    sorted_keys = sorted(IMPORT_REPLACE_MAP.keys(), key=len, reverse=True)
    for old_import in sorted_keys:
        new_import = IMPORT_REPLACE_MAP[old_import]
        new_content = new_content.replace(f"'{old_import}", f"'{new_import}").replace(f'"{old_import}', f'"{new_import}')
        
        # In case they used absolute or relative imports not starting with @
        # e.g., "../../components/ui/" -> this is harder. We assume they mostly use @/ 
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

for ext in ('*.ts', '*.tsx'):
    for file_path in FRONTEND_DIR.rglob(ext):
        if 'node_modules' not in file_path.parts and '.next' not in file_path.parts:
            update_imports(file_path)

# 4. Update tsconfig.json
tsconfig_path = FRONTEND_DIR / 'tsconfig.json'
if tsconfig_path.exists():
    try:
        # Load tsconfig (note: might have comments, json library might fail. A simple regex/string replace might be safer)
        with open(tsconfig_path, 'r') as f:
            ts_content = f.read()
            
        if '"paths": {' in ts_content and '"@/shared/*"' not in ts_content:
            ts_content = ts_content.replace(
                '"paths": {',
                '"paths": {\n      "@/shared/*": ["./shared/*"],\n      "@/features/*": ["./features/*"],'
            )
            with open(tsconfig_path, 'w') as f:
                f.write(ts_content)
    except Exception as e:
        print(f"Failed to update tsconfig.json: {e}")

# 5. Cleanup empty directories
dirs_to_check = ['components', 'services', 'contexts']
for d in dirs_to_check:
    d_path = FRONTEND_DIR / d
    if d_path.exists() and not any(d_path.iterdir()):
        d_path.rmdir()

print("Refactoring completed successfully!")
