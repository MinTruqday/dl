import os
import re

translations = {
    # document.py
    "/folders": "/thu-muc",
    "/folders/{folder_id}": "/thu-muc/{folder_id}",
    "/personal": "/ca-nhan",
    "/trash": "/thung-rac",
    "/{document_id}/restore": "/{document_id}/khoi-phuc",
    "/{document_id}/protect": "/{document_id}/bao-ve",
    "/{document_id}/activity-log": "/{document_id}/nhat-ky-hoat-dong",
    "/{document_id}/star": "/{document_id}/danh-dau",
    "/{document_id}/transfer": "/{document_id}/chuyen-nhuong",
    "/{document_id}/drm": "/{document_id}/ban-quyen",
    "/{document_id}/tags": "/{document_id}/the",
    "/{document_id}/schedule": "/{document_id}/len-lich",
    # draft.py
    "/{document_id}/moderate": "/{document_id}/kiem-duyet",
    # auth.py
    "/register": "/dang-ky",
    "/login": "/dang-nhap",
}


def fix_content(content):
    for eng, vie in sorted(translations.items(), key=lambda x: len(x[0]), reverse=True):
        content = content.replace(f'"{eng}"', f'"{vie}"')
        content = content.replace(f"'{eng}'", f"'{vie}'")
    return content


for root, _, files in os.walk("."):
    if "venv" in root or "node_modules" in root or ".git" in root or "core" in root:
        continue
    for f in files:
        if f.endswith(".py") and (
            "router" in root or "services" in root or "tools" in root
        ):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()

            new_content = fix_content(content)

            if new_content != content:
                with open(path, "w", encoding="utf-8") as file:
                    file.write(new_content)
                print(f"Updated {path}")

print("Phase 4 cleanup complete.")
