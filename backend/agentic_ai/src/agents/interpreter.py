import re
from loguru import logger
from src.harness.sandbox import CodeSandbox


class InterpreterAgent:
    """
    <module_purpose>
    Represent the isolated code execution capability for data analysis and code evaluation.
    </module_purpose>
    <contract>
    - Precondition: Receives task description containing code blocks or expression strings.
    - Postcondition: Executes code safely via CodeSandbox and returns stdout output.
    - Error Handling: Returns localized error message string on failure.
    </contract>
    """

    def __init__(self):
        self.sandbox = CodeSandbox()

    async def execute(self, task_desc: str) -> str:
        code_blocks = re.findall(r"```python\s*(.*?)\s*```", task_desc, re.DOTALL)
        if not code_blocks:
            code_blocks = re.findall(r"```\s*(.*?)\s*```", task_desc, re.DOTALL)
        if code_blocks:
            code = "\n".join(code_blocks)
        else:
            code = task_desc
        success, stdout, stderr, _ = self.sandbox.execute_code(code)
        if success:
            return stdout if stdout.strip() else "Code executed successfully with no output"
        return f"Execution failed: {stderr}"


interpreter = InterpreterAgent()
