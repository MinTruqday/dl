import re
from fastapi import HTTPException
from loguru import logger

class AgenticFirewall:
    """
    <module_purpose>
    DocLib Agentic Firewall to detect and block prompt injection attacks.
    </module_purpose>
    <contract>
    - Precondition: Receives a raw input string from the user or retrieved documents.
    - Postcondition: Returns True if safe, otherwise raises an HTTPException (Hard Block).
    - Error Handling: Uses Tiếng Việt in HTTPException details for End-users, and English in logger.
    </contract>
    """
    
    # Common prompt injection patterns (heuristic approach for performance)
    SUSPICIOUS_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+(a\s+)?", re.IGNORECASE),
        re.compile(r"system\s+override", re.IGNORECASE),
        re.compile(r"print\s+your\s+initial\s+prompt", re.IGNORECASE),
        re.compile(r"forget\s+everything", re.IGNORECASE),
        re.compile(r"output\s+the\s+password", re.IGNORECASE),
    ]

    @classmethod
    def scan_input(cls, text: str) -> bool:
        if not text:
            return True
            
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if pattern.search(text):
                logger.error(f"Firewall blocked a potential prompt injection attack. Pattern matched: {pattern.pattern}")
                raise HTTPException(
                    status_code=403,
                    detail="Hệ thống phát hiện nội dung độc hại hoặc yêu cầu thao túng (Prompt Injection) trong dữ liệu đầu vào. Hành động đã bị chặn"
                )
                
        return True

firewall = AgenticFirewall()
