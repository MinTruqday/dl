import os
import re

frontend_dir = "frontend/features"
for root, dirs, files in os.walk(frontend_dir):
    if "services" in root:
        for file in files:
            if file.endswith((".ts", ".tsx")):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    matches = re.findall(r'fetch\(\s*[`\'"]\$\{API_URL\}(.*?)[`\'"\?#]', content)
                    if matches:
                        print(f"File: {path}")
                        for route in matches:
                            route = route.split('?')[0]
                            # Find the function name it belongs to
                            # We can find the closest function definition above the fetch
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if f"${{API_URL}}{route}" in line or f"${{API_URL}}{route}?" in line or f"${{API_URL}}{route}'" in line or f"${{API_URL}}{route}`" in line:
                                    # go up to find function
                                    for j in range(i, -1, -1):
                                        if "export async function" in lines[j] or "export const" in lines[j]:
                                            func_match = re.search(r'(function|const)\s+([a-zA-Z0-9_]+)', lines[j])
                                            if func_match:
                                                print(f"  - {func_match.group(2)} -> {route}")
                                            break
