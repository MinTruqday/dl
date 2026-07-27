from loguru import logger


class InterpreterAgent:
    """
    <module_purpose>
    Represent the optional isolated code execution capability.
    </module_purpose>
    <contract>
    - Precondition: A separately isolated execution service must be available.
    - Postcondition: Refuses execution while that isolation boundary is unavailable.
    - Error Handling: Returns a localized deterministic response without running code.
    </contract>
    """

    async def execute(self, task_desc: str) -> str:
        logger.warning(
            "Interpreter execution refused because no isolated service is configured"
        )
        return "Tính năng thực thi mã đang tạm khóa để bảo đảm an toàn hệ thống"


interpreter = InterpreterAgent()
