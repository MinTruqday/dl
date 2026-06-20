import os
import re

translations = {
    # operation.py
    "/api-key": "/khoa-api",
    "/backup": "/sao-luu",
    "/collectors/active-jobs": "/thu-thap/tien-trinh-dang-chay",
    "/collectors/logs": "/thu-thap/nhat-ky",
    "/collectors/stats": "/thu-thap/thong-ke",
    "/collectors/stop": "/thu-thap/dung",
    "/collectors/trigger": "/thu-thap/kich-hoat",
    "/health": "/tinh-trang",
    "/maintenance": "/bao-tri",
    "/marketing/campaign": "/tiep-thi/chien-dich",
    "/metrics": "/chi-so",
    "/reports": "/bao-cao",
    "/settings": "/cai-dat",
    "/storage/stats": "/luu-tru/thong-ke",
    "/users/{user_id}/kyc/{status}": "/nguoi-dung/{user_id}/xac-minh/{status}",
    "/users/{user_id}/shadowban": "/nguoi-dung/{user_id}/cam-ngam",
    # user.py
    "/multiple-users": "/danh-sach",
    "/{user_id}/lock": "/{user_id}/khoa",
    "/{user_id}/notes": "/{user_id}/ghi-chu",
    "/{user_id}/role": "/{user_id}/vai-tro",
    "/{user_id}/shadowban": "/{user_id}/cam-ngam",
    "/{user_id}/status": "/{user_id}/trang-thai",
    "/{user_id}/warn": "/{user_id}/canh-bao",
    # telemetry.py
    "/activity": "/hoat-dong",
    "/audit": "/kiem-toan",
    "/stats": "/thong-ke",
    # banner.py
    "/all": "/tat-ca",
    # profile.py
    "/export-data": "/xuat-du-lieu",
    # quota.py
    "/consume": "/tieu-thu",
    # withdrawal.py
    "/queue": "/hang-doi",
    "/{withdrawal_id}/verify": "/{withdrawal_id}/xac-minh",
    # message.py
    "/conversations/{other_user_id}": "/cuoc-tro-chuyen/{other_user_id}",
}


def fix_content(content):
    # For every route, we look for "@router...("route""
    # Because routes might span multiple lines, we will search for the exact quote.
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

print("Final cleanup complete.")
