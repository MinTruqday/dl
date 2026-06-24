import os
import tokenize
import io

BACKEND_DIR = "backend"

def remove_comments(source_code):
    io_obj = io.StringIO(source_code)
    out = ""
    last_lineno = -1
    last_col = 0
    
    try:
        for tok in tokenize.generate_tokens(io_obj.readline):
            token_type = tok[0]
            token_string = tok[1]
            start_line, start_col = tok[2]
            end_line, end_col = tok[3]
            
            if start_line > last_lineno:
                last_col = 0
            if start_col > last_col:
                out += (" " * (start_col - last_col))
                
            if token_type == tokenize.COMMENT:
                pass
            else:
                out += token_string
                
            last_lineno = end_line
            last_col = end_col
            
        return out
    except Exception as e:
        print(f"Error parsing source code: {e}")
        return source_code

for root, dirs, files in os.walk(BACKEND_DIR):
    for f in files:
        if not f.endswith(".py"):
            continue
            
        filepath = os.path.join(root, f)
        
        with open(filepath, "r") as fp:
            content = fp.read()
            
        new_content = remove_comments(content)
        
        # Clean up empty lines that might have been left behind by removed comments
        lines = new_content.splitlines()
        cleaned_lines = []
        for line in lines:
            if line.strip() == "" and len(cleaned_lines) > 0 and cleaned_lines[-1].strip() == "":
                continue # Skip consecutive empty lines
            cleaned_lines.append(line)
            
        final_content = "\n".join(cleaned_lines) + "\n"
        
        if final_content != content:
            with open(filepath, "w") as fp:
                fp.write(final_content)

print("Comments removed from backend.")
