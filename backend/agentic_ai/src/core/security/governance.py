import re
from typing import List, Tuple

def enforce_resource_limits(results: List[str]) -> Tuple[bool, str]:
    max_length = 50000
    total_length = sum(len(str(r)) for r in results)
    
    if total_length > max_length:
        return False, f"Output length {total_length} exceeds hard limit {max_length}"
        
    return True, ""

def sanitize_output(results: List[str]) -> List[str]:
    sanitized = []
    for r in results:
        text = str(r)
        text = re.sub(r"\b(0[3|5|7|8|9])+([0-9]{8})\b", "[REDACTED PHONE]", text)
        text = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED EMAIL]", text)
        text = re.sub(r"\b(?:\d[ -]*?){13,16}\b", "[REDACTED CC]", text)
        
        text = re.sub(r"(?i)(password|secret|key|token)[\s:=]+[\"']?[A-Za-z0-9_\-\+]{16,}[\"']?", r"\1: [REDACTED SECRET]", text)
        
        sanitized.append(text)
        
    return sanitized
