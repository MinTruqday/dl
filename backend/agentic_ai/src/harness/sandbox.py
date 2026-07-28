import io
import multiprocessing
import os
import resource
import shutil
import tempfile
import types
from pathlib import Path
from typing import List, Tuple

from loguru import logger
from RestrictedPython import compile_restricted, safe_builtins, utility_builtins


def _safe_getattr(obj, name, default=None):
    if name.startswith("_"):
        raise AttributeError(f"Denied private attribute access: {name}")
    return getattr(obj, name, default)


def _restricted_worker(code: str, working_dir: str, connection) -> None:
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    class Collector:
        def __init__(self, guarded_getattr=None):
            self.guarded_getattr = guarded_getattr

        def write(self, text):
            stdout_buffer.write(str(text))

        def __call__(self):
            return self

        def __str__(self):
            return stdout_buffer.getvalue()

        def _call_print(self, *objects, **kwargs):
            if kwargs.get("file") is not None:
                raise PermissionError("Redirected output is not allowed")
            kwargs["file"] = self
            print(*objects, **kwargs)

    try:
        os.chdir(working_dir)
        resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
        resource.setrlimit(resource.RLIMIT_FSIZE, (1_048_576, 1_048_576))
        resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
        byte_code = compile_restricted(code, filename="<sandbox>", mode="exec")
        global_scope = {
            "_print_": Collector,
            "_getattr_": _safe_getattr,
            "__builtins__": {
                **safe_builtins,
                **utility_builtins,
                "print": lambda *args, **kwargs: stdout_buffer.write(
                    " ".join(map(str, args)) + "\n"
                ),
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
            },
        }
        restricted_program = types.FunctionType(byte_code, global_scope)
        restricted_program()
        output = stdout_buffer.getvalue()
        connection.send((True, output, stderr_buffer.getvalue(), []))
    except BaseException as exc:
        stderr_buffer.write(f"{type(exc).__name__}: {exc}")
        connection.send((False, stdout_buffer.getvalue(), stderr_buffer.getvalue(), []))
    finally:
        connection.close()


class CodeSandbox:
    """
    <module_purpose>
    Represent the isolated code execution boundary for DocLib agent workflows.
    </module_purpose>
    <contract>
    - Precondition: Receives Python source without external dependencies.
    - Postcondition: Executes RestrictedPython in a resource limited child process.
    - Error Handling: Terminates timed out workers and returns a deterministic error tuple.
    </contract>
    """

    def __init__(self, timeout_seconds: float = 3.0):
        self.timeout_seconds = timeout_seconds
        self.temp_dir = tempfile.mkdtemp(prefix="agentic_sandbox_")
        os.chmod(self.temp_dir, 0o700)

    def execute_code(
        self,
        code: str,
        dependencies: list | None = None,
    ) -> Tuple[bool, str, str, List[str]]:
        if not isinstance(code, str) or not code.strip():
            return False, "", "Sandbox source is empty", []
        if dependencies:
            return False, "", "External dependencies are not allowed", []

        execution_dir = tempfile.mkdtemp(
            prefix="execution_",
            dir=self.temp_dir,
        )
        os.chmod(execution_dir, 0o700)
        context = multiprocessing.get_context("fork")
        parent_connection, child_connection = context.Pipe(duplex=False)
        process = context.Process(
            target=_restricted_worker,
            args=(code, execution_dir, child_connection),
            daemon=True,
        )
        try:
            process.start()
            child_connection.close()
            process.join(self.timeout_seconds)
            if process.is_alive():
                process.terminate()
                process.join(1)
                return False, "", "Sandbox execution timed out", []
            if parent_connection.poll():
                return parent_connection.recv()
            return (
                False,
                "",
                f"Sandbox worker exited with code {process.exitcode}",
                [],
            )
        finally:
            parent_connection.close()
            if process.is_alive():
                process.terminate()
                process.join(1)
            shutil.rmtree(execution_dir, ignore_errors=True)

    def cleanup(self):
        root = Path(self.temp_dir)
        if root.exists() and root.is_dir():
            shutil.rmtree(root, ignore_errors=True)
        logger.info("Sandbox workspace cleanup completed")
