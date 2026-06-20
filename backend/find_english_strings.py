import ast
import os
import re

def is_english(text):
    # Check if there are English words. If it contains vietnamese characters, it's likely translated.
    if re.search(r'[àáãạảăắằẳẵặâấầẩẫậèéẹẻẽêềếểễệđìíĩỉịòóõọỏôốồổỗộơớờởỡợùúũụủưứừửữựỳýỹỷỵ]', text, re.IGNORECASE):
        return False
    # If it has more than 2 english words, consider it english
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
    return len(words) >= 2

class EnglishStringFinder(ast.NodeVisitor):
    def __init__(self, filepath):
        self.filepath = filepath
        self.findings = []
        
    def check_string(self, node, text):
        if is_english(text):
            self.findings.append((node.lineno, text))

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            # Context checking could be complex, let's just collect all strings and filter by context later, 
            # or just look at where it's used.
            pass
        self.generic_visit(node)
        
    def visit_Call(self, node):
        # check logger
        is_log_or_err = False
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id == 'logger':
                is_log_or_err = True
        elif isinstance(node.func, ast.Name):
            if 'Exception' in node.func.id or 'Error' in node.func.id:
                is_log_or_err = True
        
        # Check APIResponse message
        if isinstance(node.func, ast.Name) and node.func.id == 'APIResponse':
            for kw in node.keywords:
                if kw.arg in ['message', 'detail']:
                    self._extract_text(kw.value, node.lineno)
                    
        if is_log_or_err:
            if node.args:
                self._extract_text(node.args[0], node.lineno)
            for kw in node.keywords:
                if kw.arg in ['detail', 'message']:
                    self._extract_text(kw.value, node.lineno)
                    
        self.generic_visit(node)
        
    def _extract_text(self, node, lineno):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if is_english(node.value):
                self.findings.append((lineno, node.value))
        elif isinstance(node, ast.JoinedStr):
            # Extract raw string parts
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    parts.append(v.value)
                elif isinstance(v, ast.FormattedValue):
                    parts.append("{...}")
            text = "".join(parts)
            if is_english(text):
                self.findings.append((lineno, text))

for root, _, files in os.walk('.'):
    for f in files:
        if f.endswith('.py') and 'venv' not in root and 'node_modules' not in root:
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                tree = ast.parse(content)
                finder = EnglishStringFinder(path)
                finder.visit(tree)
                if finder.findings:
                    print(f"--- {path} ---")
                    for lineno, text in finder.findings:
                        print(f"Line {lineno}: {text}")
            except Exception as e:
                pass
