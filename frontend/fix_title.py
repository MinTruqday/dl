import os

directory = "features/compilation/components"

for filename in os.listdir(directory):
    if not filename.endswith(".ts") or filename == "index.ts":
        continue

    filepath = os.path.join(directory, filename)
    with open(filepath, "r") as f:
        content = f.read()

    if 'title: "Doc Lib ' in content:
        content = content.replace('title: "Doc Lib ', 'title: "DocLib ')
        with open(filepath, "w") as f:
            f.write(content)
        print(f"Fixed title in {filepath}")
