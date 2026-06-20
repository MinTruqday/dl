import os

for root, _, files in os.walk("."):
    if "venv" in root or "node_modules" in root or ".git" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()

            new_content = content.replace("/email/", "/email/")
            new_content = new_content.replace("/ten-mien/", "/ten-mien/")

            if new_content != content:
                with open(path, "w", encoding="utf-8") as file:
                    file.write(new_content)
                print(f"Fixed {path}")

print("Fixed theo-*")
