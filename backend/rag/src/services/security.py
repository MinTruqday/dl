import re


PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.I),
    re.compile(r"system\s+prompt", re.I),
    re.compile(r"reveal\s+(your\s+)?(secret|token|credential)", re.I),
    re.compile(r"execute\s+(this\s+)?tool", re.I),
    re.compile(r"bỏ\s+qua\s+(mọi\s+)?chỉ\s+dẫn\s+trước", re.I),
    re.compile(r"tiết\s+lộ\s+(khóa|mật\s+khẩu|token)", re.I),
]


def prompt_injection_flags(text: str):
    return [f"prompt_injection_pattern_{index + 1}" for index, pattern in enumerate(PATTERNS) if pattern.search(text)]
