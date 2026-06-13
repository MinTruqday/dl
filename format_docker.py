import os
import glob
import re

DOCKER_KEYWORDS = [
    "FROM", "MAINTAINER", "RUN", "CMD", "LABEL", "EXPOSE", "ENV", "ADD",
    "COPY", "ENTRYPOINT", "VOLUME", "USER", "WORKDIR", "ARG", "ONBUILD",
    "STOPSIGNAL", "HEALTHCHECK", "SHELL"
]

def format_dockerfile(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    formatted_lines = []
    prev_blank = False
    
    for line in lines:
        stripped = line.strip()
        
        # Remove multiple blank lines
        if not stripped:
            if not prev_blank:
                formatted_lines.append("\n")
                prev_blank = True
            continue
            
        prev_blank = False
        
        # Upper case keywords
        words = stripped.split()
        if words and words[0].upper() in DOCKER_KEYWORDS:
            # Reconstruct line with upper case keyword and proper spacing
            first_word = words[0].upper()
            rest = " ".join(words[1:])
            # Don't strip if it was indented (though Dockerfile usually isn't)
            # Just keep original indentation if any
            indent_match = re.match(r'^\s+', line)
            indent = indent_match.group(0) if indent_match else ""
            formatted_lines.append(f"{indent}{first_word} {rest}\n")
        else:
            formatted_lines.append(line.rstrip() + "\n")
            
    # Clean up top/bottom blank lines
    while formatted_lines and formatted_lines[0].strip() == "":
        formatted_lines.pop(0)
    while formatted_lines and formatted_lines[-1].strip() == "":
        formatted_lines.pop()
        
    formatted_lines.append("\n") # Add final newline
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(formatted_lines)
        
    print(f"Formatted: {filepath}")

def main():
    dockerfiles = glob.glob("backend/*/Dockerfile")
    for df in dockerfiles:
        format_dockerfile(df)
        
if __name__ == "__main__":
    main()
