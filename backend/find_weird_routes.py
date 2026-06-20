import os
import re

weird_routes = []
theo_routes = []

diacritics_pattern = re.compile(
    r"[áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđĐ]"
)

for root, _, files in os.walk("."):
    if "venv" in root or "node_modules" in root or ".git" in root:
        continue
    for f in files:
        if f.endswith(".py") and (
            "router" in root or "services" in root or "tools" in root
        ):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()

            # Find all router paths
            paths = re.findall(
                r'(?:@router\.(?:get|post|put|patch|delete|websocket)\(|prefix=)["\']([^"\']+)["\']',
                content,
            )
            # Find all internal API urls in f-strings: f"{...}/path"
            internal_paths = re.findall(r'f"\{[^\}]+\}(/[^"]+)"', content)

            all_paths = paths + internal_paths

            for p in all_paths:
                if diacritics_pattern.search(p):
                    weird_routes.append((path, p))
                if "theo-" in p:
                    theo_routes.append((path, p))

print("Routes with diacritics:")
for path, p in weird_routes:
    print(f"  {path}: {p}")

print("\nRoutes with 'theo-':")
for path, p in theo_routes:
    print(f"  {path}: {p}")
