from typing import Annotated

from langchain_core.tools import tool
from pydantic import Field

from src.harness.sandbox import CodeSandbox


@tool
def execute_python(
    code: Annotated[
        str,
        Field(
            min_length=1,
            max_length=20000,
            description="Python source to run without files network or dependencies",
        ),
    ],
) -> dict:
    """Run bounded Python in DocLib's isolated RestrictedPython sandbox

    Use for calculations and deterministic text or data transformations only
    External packages filesystem access network access and private attributes are blocked
    Returns captured output and a structured error when execution is rejected or fails
    """
    sandbox = CodeSandbox()
    try:
        success, stdout, stderr, files = sandbox.execute_code(code)
        return {
            "success": success,
            "stdout": stdout,
            "stderr": stderr,
            "files": files,
        }
    finally:
        sandbox.cleanup()
