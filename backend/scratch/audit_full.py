import os
import re

def audit_files(directory):
    files_with_errors = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    has_error = False
                    
                    if "router = APIRouter" in content:
                        decorators = re.findall(r"@router\.(get|post|put|delete|patch)\((.*?)\)", content, re.DOTALL)
                        for method, args in decorators:
                            if "response_model=APIResponse" not in args and "response_model=Any" not in args:
                                has_error = True
                                break
                    
                    if "os.getenv" in content:
                        if "core/config.py" not in path:
                            has_error = True
                    
                    
                    if has_error and path not in files_with_errors:
                        files_with_errors.append(path)
                            
    return files_with_errors

api_dir = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/api"
service_dir = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/services"

errors = audit_files(api_dir) + audit_files(service_dir)
for e in errors:
    print(e)
