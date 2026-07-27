import shutil
import tempfile
from typing import List, Tuple

from loguru import logger


class CodeSandbox:
    """
    <module_purpose>
    Represent the isolated code execution boundary for DocLib agent workflows.
    </module_purpose>
    <contract>
    - Precondition: A separately isolated execution service must be configured.
    - Postcondition: Refuses local execution when no isolated service is available.
    - Error Handling: Returns a deterministic unavailable result without running code.
    </contract>
    """

    def __init__(self, use_docker: bool = True):
        self.use_docker = use_docker
        self.temp_dir = tempfile.mkdtemp(prefix="agentic_sandbox_")

    def execute_code(
        self,
        code: str,
        dependencies: list | None = None,
    ) -> Tuple[bool, str, str, List[str]]:
        logger.warning(
            "Code execution refused because no isolated sandbox service is configured"
        )
        return (
            False,
            "",
            "Isolated code execution is unavailable",
            [],
        )

    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        logger.info("Sandbox workspace cleanup completed")
