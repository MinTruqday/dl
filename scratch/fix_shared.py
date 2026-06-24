import os

backend_dir = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend"

for root, dirs, files in os.walk(backend_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if "from shared." in content or "import shared." in content:
                new_content = content.replace("from shared.", "from src.core.")
                new_content = new_content.replace("import shared.", "import src.core.")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Fixed {path}")
