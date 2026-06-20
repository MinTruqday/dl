import os
import re

final_translation = {
    "/actions": "/hanh-dong",
    "/folders/{folder_id}": "/thu-muc/{folder_id}",
    "/preview/{slug}": "/xem-truoc/{slug}",
    "/quota": "/han-muc",
    "/quotas": "/han-muc",
    "/stream": "/phat-truc-tiep",
    "/{document_id}/analytics": "/{document_id}/thong-ke",
    "/{document_id}/unlock": "/{document_id}/mo-khoa",
    "/{other_user_id}/search": "/{other_user_id}/tim-kiem",
    "/export/{format}": "/ket-xuat/{format}",
    "/history/{document_id}": "/lich-su/{document_id}",
    "/d/{slug}": "/tai-lieu/{slug}",
}


def grand_replace(content):
    for eng, vie in sorted(
        final_translation.items(), key=lambda x: len(x[0]), reverse=True
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

print("Final Translation complete.")
