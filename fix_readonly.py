import os
import glob
import re

directory = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/frontend/components/editor"
files = glob.glob(os.path.join(directory, "*.ts"))

for file_path in files:
    with open(file_path, "r") as f:
        content = f.read()
    
    if "api.readOnly.toggle" in content:
        print(f"Fixing {os.path.basename(file_path)}...")
        
        # 1. Replace all usages of this.api.readOnly.toggle with this.readOnly
        content = content.replace("this.api.readOnly.toggle", "this.readOnly")
        
        # 2. Add private readOnly: boolean; if not exists
        if "private readOnly: boolean;" not in content:
            content = re.sub(r'(private data:[^;]+;)', r'\1\n  private readOnly: boolean;', content, count=1)
            
        # 3. Update constructor parameter
        if "readOnly" not in re.search(r'constructor\([^)]+\)', content).group():
            content = re.sub(r'constructor\(\{\s*api,\s*data\s*\}\s*:\s*\{\s*api:\s*API,\s*data:\s*any\s*\}\)', 
                             r'constructor({ api, data, readOnly }: { api: API, data?: any, readOnly?: boolean })', 
                             content, count=1)
                             
        # 4. Add this.readOnly = !!readOnly; in constructor
        if "this.readOnly =" not in content:
            content = re.sub(r'(this\.api\s*=\s*api;)', r'\1\n    this.readOnly = !!readOnly;', content, count=1)
            
        # 5. Make data safe (optional chaining) for some common properties
        # We already made data?: any in constructor type. 
        # But we won't aggressively replace data. property access unless we know it's safe.
        # Actually, let's just do the readOnly fix first.
            
        with open(file_path, "w") as f:
            f.write(content)

print("Done!")
