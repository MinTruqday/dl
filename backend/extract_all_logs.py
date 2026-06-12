import os
import ast

target_dirs = [
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/worker',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/signal',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/provision',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/contact',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/content',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/compiler',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/authentication',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/finance',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/websocket',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/core',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/collector',
    '/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/agentic-ai'
]

results = set()

def extract_source_segment(source, node):
    lines = source.splitlines(True)
    if not hasattr(node, 'lineno') or not hasattr(node, 'end_lineno'):
        return None
    if node.lineno == node.end_lineno:
        return lines[node.lineno - 1][node.col_offset:node.end_col_offset]
    
    extracted = []
    extracted.append(lines[node.lineno - 1][node.col_offset:])
    for i in range(node.lineno, node.end_lineno - 1):
        extracted.append(lines[i])
    extracted.append(lines[node.end_lineno - 1][:node.end_col_offset])
    return "".join(extracted)

class StringVisitor(ast.NodeVisitor):
    def __init__(self, source, filepath):
        self.source = source
        self.filepath = filepath

    def add_match(self, node):
        segment = extract_source_segment(self.source, node)
        if segment:
            results.add(segment.strip().replace('\n', ' '))

    def visit_Call(self, node):
        if getattr(getattr(node.func, 'value', None), 'id', '') == 'logger' or getattr(node.func, 'id', '') in ['HTTPException', 'Exception', 'ValueError', 'print']:
            for arg in node.args:
                if isinstance(arg, (ast.Constant, ast.JoinedStr)):
                    self.add_match(arg)
            for kw in node.keywords:
                if kw.arg in ['detail', 'content', 'message']:
                    if isinstance(kw.value, (ast.Constant, ast.JoinedStr)):
                        self.add_match(kw.value)
        self.generic_visit(node)
        
    def visit_Return(self, node):
        if isinstance(node.value, ast.Dict):
            for k, v in zip(node.value.keys, node.value.values):
                if isinstance(k, ast.Constant) and k.value in ['message', 'detail', 'status']:
                    if isinstance(v, (ast.Constant, ast.JoinedStr)):
                        self.add_match(v)
        self.generic_visit(node)

for d in target_dirs:
    for root, dirs, files in os.walk(d):
        if 'venv' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    source = f.read()
                try:
                    StringVisitor(source, filepath).visit(ast.parse(source))
                except Exception as e:
                    pass

with open('/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/all_logs.txt', 'w') as f:
    for s in sorted(list(results)):
        f.write(s + '\n')
