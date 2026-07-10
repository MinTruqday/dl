import os
import re

env_path = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/.env"
with open(env_path, "r") as f:
    master_keys = []
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            if "=" in line:
                key = line.split("=")[0]
                master_keys.append(key)

backend_dir = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend"

for root, dirs, files in os.walk(backend_dir):
    if "configuration.py" in files:
        filepath = os.path.join(root, "configuration.py")
        with open(filepath, "r") as f:
            content = f.read()

        # Extract everything before "class Settings(BaseModel):"
        parts = re.split(r"class Settings\(BaseModel\):\n", content)
        if len(parts) != 2:
            continue
            
        header = parts[0] + "class Settings(BaseModel):\n"
        body = parts[1]
        
        # Extract the settings instance creation (usually at the bottom like "settings = Settings()")
        body_parts = re.split(r"\n\s*settings\s*=\s*Settings\(\)", body)
        class_body = body_parts[0]
        footer = "\n\nsettings = Settings()\n" if len(body_parts) > 1 else ""

        # Find all attribute lines
        attr_lines = []
        for line in class_body.split("\n"):
            if line.strip() and ":" in line and "=" in line:
                attr_lines.append(line)
                
        # Sort attribute lines based on master_keys
        def get_key_index(line):
            key = line.split(":")[0].strip()
            # If it's a dynamic URL property or not in env, put it at the end
            if key in master_keys:
                return master_keys.index(key)
            # Service URL properties usually end in _URL but not in env
            if key.endswith("_URL"): return 9999
            if key == "SERVICE_DB_NAME": return 10000
            return 9998 # Other non-env things

        sorted_attrs = sorted(attr_lines, key=get_key_index)
        
        # Build new class body
        new_class_body = "\n".join(sorted_attrs)
        
        new_content = header + new_class_body + footer
        
        if content != new_content:
            with open(filepath, "w") as f:
                f.write(new_content)
            print(f"[x] Sorted config in {filepath}")

