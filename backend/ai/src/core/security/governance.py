import re
from typing import List, Tuple

def enforce_resource_limits(results: List[str]) -> Tuple[bool, str]:
    max_length = 50000
    total_length = sum(len(str(r)) for r in results)
    
    if total_length > max_length:
        return False, f"Output length {total_length} exceeds hard limit {max_length}"
        
    return True, ""

def sanitize_output(results: List[str]) -> List[str]:
    from src.core.security.guardrails import guardrails_engine

    sanitized = []
    for r in results:
        res = guardrails_engine.inspect_output(str(r))
        sanitized.append(res.get("sanitized_text", str(r)))
    return sanitized
