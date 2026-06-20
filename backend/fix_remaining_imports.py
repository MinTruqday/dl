import os
import re

for root, _, files in os.walk("."):
    if "venv" in root or "node_modules" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()

            new_content = content

            # Fix "from src.router import X_router" -> "from src.router import X"
            # It can be a list: "from src.router import (A_router, B_router)"
            # We can just replace occurrences of "_router" with "" in the context of router module usage.
            # But be careful not to replace `router as message_router`.

            # Let's just do targeted replacements for the known bad ones in main.py:
            if f == "main.py":
                new_content = re.sub(r"(\b\w+)_router\b", r"\1", new_content)
                new_content = re.sub(r"(\b\w+)_service\b", r"\1", new_content)
                new_content = re.sub(r"(\b\w+)_schema\b", r"\1", new_content)
                new_content = re.sub(r"(\b\w+)_model\b", r"\1", new_content)

                # if that resulted in `from src.router.message import router as message`, that's fine.
                # but let's check if there's any `import editor as editor`
                new_content = new_content.replace(
                    "import editor as editor", "import editor"
                )
                new_content = new_content.replace(
                    "import editorjs as editorjs", "import editorjs"
                )
                new_content = new_content.replace(
                    "import latex as latex", "import latex"
                )

            # Also fix any remaining usages of `module.router` -> `module.router`
            new_content = re.sub(r"(\w+)_router\.router", r"\1.router", new_content)

            # Fix usages of `module.Service` -> `module.Service`
            new_content = re.sub(r"(\w+)_service\.(\w+)", r"\1.\2", new_content)

            # Fix references to agentic_ai harness
            new_content = re.sub(r"(\w+)_harness\b", r"\1", new_content)

            if new_content != content:
                with open(path, "w", encoding="utf-8") as file:
                    file.write(new_content)
                print(f"Updated {path}")

print("Fixed remaining imports.")
