import os
import ast

BACKEND_DIR = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend"

def analyze_file(filepath):
    issues = []
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            content = f.read()
            tree = ast.parse(content)
        except SyntaxError:
            return ["Syntax error"]
        
    lines = content.split('\n')
    
    # 1. Check for BaseModel in router or services
    if '/router/' in filepath or '/services/' in filepath:
        has_basemodel = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == 'BaseModel':
                        has_basemodel = True
        if has_basemodel:
            issues.append("Contains Pydantic schema (BaseModel) but is not in schemas/")

    # 2. Check for APIRouter in services or schemas
    if '/services/' in filepath or '/schemas/' in filepath:
        has_router = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'APIRouter':
                has_router = True
        if has_router:
            issues.append("Contains APIRouter definition but is not in router/")

    # 3. Check for business logic (db queries) in routers
    # Only a loose check: if they import RepositoryFactory or db_client and use it directly instead of via a service
    if '/router/' in filepath:
        has_db_access = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == 'core.database' and any(n.name == 'db_client' for n in node.names):
                has_db_access = True
            if isinstance(node, ast.ImportFrom) and node.module == 'core.repositories.base_repository':
                has_db_access = True
        if has_db_access:
            issues.append("Router file accesses DB directly (db_client / RepositoryFactory). Business logic should be in services/")
            
    # 4. Check file size
    if len(lines) > 500:
        issues.append(f"File is very large ({len(lines)} lines), consider splitting.")
    if len(lines) < 15 and filepath.endswith('.py') and not filepath.endswith('__init__.py') and 'main.py' not in filepath:
        issues.append(f"File is very small ({len(lines)} lines), consider merging.")

    return issues

def main():
    report = []
    for root, dirs, files in os.walk(BACKEND_DIR):
        # skip env, venv, pycache
        if any(x in root for x in ['venv', '.venv', '__pycache__', '.git', 'logs']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                issues = analyze_file(filepath)
                if issues:
                    rel_path = os.path.relpath(filepath, BACKEND_DIR)
                    report.append(f"### {rel_path}")
                    for issue in issues:
                        report.append(f"- {issue}")
                    report.append("")

    with open(os.path.join(BACKEND_DIR, "structure_audit_report.md"), "w") as f:
        f.write("# Backend Structure Audit Report\n\n")
        f.write("\n".join(report))
        
    print("Audit complete. Report generated at structure_audit_report.md")

if __name__ == "__main__":
    main()
