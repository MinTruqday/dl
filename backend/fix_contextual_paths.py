import os
import re

replacements = {
    "/mau-thu": "/mau-thu",
    "/ma-qua-tang": "/ma-qua-tang",
    "/tien-trinh/": "/tien-trinh/",
    "/tien-trinh-dang-chay": "/tien-trinh-dang-chay",
}


def apply_replacements(content):
    for old, new in replacements.items():
        content = content.replace(old, new)

    # Also fix the tasks if it was changed to cong-viec in collaboration
    # wait, if I did "/tien-trinh/" -> "/tien-trinh/", then "/tai-lieu/{document_id}/cong-viec" -> "/tai-lieu/{document_id}/nhiem-vu"
    # Is that correct for collaboration tasks? Probably "nhiem-vu" is better for collaboration tasks.
    # Let's fix collaboration tasks manually if needed.
    content = content.replace(
        "/tai-lieu/{document_id}/nhiem-vu", "/tai-lieu/{document_id}/nhiem-vu"
    )
    # For tasks/{task_id} which was /nhiem-vu/{task_id} => /nhiem-vu/{task_id}
    # Let's see if there are task_id vs job_id
    content = content.replace("/nhiem-vu/{task_id}", "/nhiem-vu/{task_id}")
    return content


for root, _, files in os.walk("."):
    if "venv" in root or "node_modules" in root or ".git" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()

            new_content = apply_replacements(content)

            if new_content != content:
                with open(path, "w", encoding="utf-8") as file:
                    file.write(new_content)
                print(f"Fixed {path}")

print("Contextual translation fix complete.")
