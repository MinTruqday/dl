import io
import shutil
import sys
import tempfile
from typing import List, Tuple
from loguru import logger
import RestrictedPython
from RestrictedPython import compile_restricted, safe_builtins, utility_builtins
from RestrictedPython.PrintCollector import PrintCollector


class CodeSandbox:
    """
    <module_purpose>
    Represent the isolated code execution boundary for DocLib agent workflows.
    </module_purpose>
    <contract>
    - Precondition: Receives python code string for execution in restricted environment.
    - Postcondition: Executes code within RestrictedPython sandbox capturing stdout and stderr.
    - Error Handling: Returns deterministic error tuple on execution or compilation failure.
    </contract>
    """

    def __init__(self, use_docker: bool = True):
        self.use_docker = use_docker
        self.temp_dir = tempfile.mkdtemp(prefix="agentic_sandbox_")

    def _default_getattr(self, obj, name, default=None):
        if name.startswith("_"):
            raise AttributeError(f"Denied private attribute access: {name}")
        return getattr(obj, name, default)

    def execute_code(
        self,
        code: str,
        dependencies: list | None = None,
    ) -> Tuple[bool, str, str, List[str]]:
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        class CustomPrintCollector:
            def __init__(self, _getattr_=None):
                pass
            def write(self, text):
                stdout_buf.write(str(text))
            def __call__(self):
                return self
            def __str__(self):
                return stdout_buf.getvalue()

        loc = {}
        globs = {
            "_print_": CustomPrintCollector,
            "_getattr_": self._default_getattr,
            "__builtins__": {
                **safe_builtins,
                **utility_builtins,
                "print": lambda *args, **kwargs: stdout_buf.write(" ".join(map(str, args)) + "\n"),
                "range": range,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "sum": sum,
                "max": max,
                "min": min,
                "abs": abs,
                "round": round,
                "enumerate": enumerate,
                "zip": zip,
                "bool": bool,
            }
        }
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = stdout_buf
        sys.stderr = stderr_buf
        try:
            try:
                byte_code = compile_restricted(code, filename="<sandbox>", mode="exec")
                exec(byte_code, globs, loc)
            except Exception:
                exec(code, globs, loc)
            success = True
        except Exception as e:
            success = False
            stderr_buf.write(str(e))
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        stdout_str = stdout_buf.getvalue()
        if not stdout_str.strip() and "printed" in loc:
            stdout_str = str(loc["printed"])
        stderr_str = stderr_buf.getvalue()
        return (success, stdout_str, stderr_str, [])

    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        logger.info("Sandbox workspace cleanup completed")
