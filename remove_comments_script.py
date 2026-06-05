import os
import tokenize
import io
import re

def remove_comments(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tokens = list(tokenize.generate_tokens(io.StringIO(content).readline))
        
        out_tokens = []
        for tok in tokens:
            if tok.exact_type == tokenize.COMMENT:
                continue
            out_tokens.append((tok.type, tok.string))
            
        out = tokenize.untokenize(out_tokens)
        
        # Clean up empty lines that were left behind by comments
        lines = out.split('\n')
        cleaned_lines = []
        for line in lines:
            if not line.strip() and len(cleaned_lines) > 0 and not cleaned_lines[-1].strip():
                # skip multiple blank lines
                continue
            cleaned_lines.append(line)
            
        out = '\n'.join(cleaned_lines)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(out)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

processed = 0
for root, dirs, files in os.walk('backend'):
    if 'venv' in root or '__pycache__' in root: continue
    for f in files:
        if f.endswith('.py'):
            remove_comments(os.path.join(root, f))
            processed += 1

print(f"Processed {processed} python files.")
