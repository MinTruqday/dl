import os
import subprocess
import tempfile
from typing import Dict, List

from langchain_core.tools import tool
from loguru import logger


OWASP_PATTERNS: Dict[str, List[str]] = {
    "SQL Injection": [
        r"execute\s*\(\s*[\"'].*%s",
        r"cursor\.execute\s*\(.*\+",
        r"f[\"'].*SELECT.*{",
    ],
    "Command Injection": [
        r"os\.system\s*\(",
        r"subprocess\.call\s*\(.*shell=True",
        r"eval\s*\(.*input",
    ],
    "Path Traversal": [
        r"\.\./",
        r"open\s*\(.*request\.",
    ],
    "Hardcoded Secrets": [
        r"password\s*=\s*[\"'][^\"']{4,}",
        r"api_key\s*=\s*[\"'][^\"']{8,}",
        r"secret\s*=\s*[\"'][^\"']{4,}",
        r"token\s*=\s*[\"'][A-Za-z0-9+/]{20,}",
    ],
    "XSS": [
        r"render_template_string\s*\(.*request\.",
        r"innerHTML\s*=.*user",
    ],
    "Insecure Deserialization": [
        r"pickle\.loads\s*\(",
        r"yaml\.load\s*\([^)]*Loader",
    ],
}

class OWASPASTVisitor(ast.NodeVisitor):
    def __init__(self):
        self.findings = []

    def visit_Call(self, node):
        # Command Injection
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            if func_name == "system" and isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                self.findings.append(f"Command Injection (os.system) at line {node.lineno}")
            elif func_name == "call" and isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        self.findings.append(f"Command Injection (subprocess.call with shell=True) at line {node.lineno}")
            # Insecure Deserialization
            elif func_name == "loads" and isinstance(node.func.value, ast.Name) and node.func.value.id == "pickle":
                self.findings.append(f"Insecure Deserialization (pickle.loads) at line {node.lineno}")
            elif func_name == "load" and isinstance(node.func.value, ast.Name) and node.func.value.id == "yaml":
                self.findings.append(f"Insecure Deserialization (yaml.load) at line {node.lineno}")
            # SQL Injection
            elif func_name == "execute":
                for arg in node.args:
                    if isinstance(arg, ast.JoinedStr) or isinstance(arg, ast.BinOp):
                        self.findings.append(f"Possible SQL Injection (execute with dynamic string) at line {node.lineno}")
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name == "eval":
                self.findings.append(f"Command Injection (eval) at line {node.lineno}")

        self.generic_visit(node)

    def visit_Assign(self, node):
        # Hardcoded Secrets
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id.lower()
                if any(sec in var_name for sec in ["password", "secret", "api_key", "token"]):
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str) and len(node.value.value) >= 4:
                        self.findings.append(f"Hardcoded Secret ({var_name}) at line {node.lineno}")
        self.generic_visit(node)

class SASTScanner:
    """
    <module_purpose>Runs Static Application Security Testing against code artifacts using Bandit, Semgrep, and AST-based OWASP Top 10 pattern matching.</module_purpose>
    <contract>Acts as the deterministic backbone for the SecOpsAgent. Returns full, actionable scan output including severity levels and line references.</contract>
    """

    @staticmethod
    def run_owasp_patterns(code: str) -> str:
        try:
            tree = ast.parse(code)
            visitor = OWASPASTVisitor()
            visitor.visit(tree)
            if not visitor.findings:
                return "OWASP Top 10 check: No obvious patterns detected"
            
            return "\n".join([f"[OWASP AST] {finding}" for finding in visitor.findings])
        except SyntaxError:
            return "OWASP Top 10 check: Code contains syntax errors, cannot parse AST."
        except Exception as e:
            logger.exception("AST parsing failed")
            return f"OWASP Top 10 check: Error during AST analysis: {e}"

    @staticmethod
    def run_bandit_on_code(code: str) -> str:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name
        try:
            logger.info("Bandit execution started")
            cmd = ["bandit", "-r", tmp_path, "-f", "txt", "-ll"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            output = (result.stdout or "").strip()
            if not output:
                output = (result.stderr or "Bandit returned no output").strip()
            return output if output else "Bandit execution completed with no findings"
        except FileNotFoundError:
            return "Bandit dependency is missing in the current environment"
        except subprocess.TimeoutExpired:
            return "Bandit execution timed out"
        except Exception:
            logger.exception("Bandit execution failed")
            return "Bandit execution failed"
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    @staticmethod
    def run_bandit(target_path: str) -> str:
        try:
            logger.info("Bandit execution started")
            cmd = ["bandit", "-r", target_path, "-f", "txt", "-ll"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            output = (result.stdout or "").strip()
            return output if output else "Bandit execution completed with no findings"
        except FileNotFoundError:
            return "Bandit dependency is missing in the current environment"
        except subprocess.TimeoutExpired:
            return "Bandit execution timed out"
        except Exception:
            logger.exception("Bandit execution failed")
            return "Bandit execution failed"

    @staticmethod
    def run_semgrep_on_code(code: str) -> str:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name
        try:
            logger.info("Semgrep execution started")
            cmd = ["semgrep", "scan", "--config", "auto", "--quiet", tmp_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            output = (result.stdout or "").strip()
            if not output:
                output = (result.stderr or "Semgrep returned no output").strip()
            return output if output else "Semgrep execution completed with no findings"
        except FileNotFoundError:
            return "Semgrep dependency is missing in the current environment"
        except subprocess.TimeoutExpired:
            return "Semgrep execution timed out"
        except Exception:
            logger.exception("Semgrep execution failed")
            return "Semgrep execution failed"
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    @staticmethod
    def run_semgrep(target_path: str) -> str:
        try:
            logger.info("Semgrep execution started")
            cmd = ["semgrep", "scan", "--config", "auto", "--quiet", target_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            output = (result.stdout or "").strip()
            return output if output else "Semgrep execution completed with no findings"
        except FileNotFoundError:
            return "Semgrep dependency is missing in the current environment"
        except subprocess.TimeoutExpired:
            return "Semgrep execution timed out"
        except Exception:
            logger.exception("Semgrep execution failed")
            return "Semgrep execution failed"

    @classmethod
    def full_scan(cls, code: str) -> str:
        bandit_result = cls.run_bandit_on_code(code)
        semgrep_result = cls.run_semgrep_on_code(code)
        owasp_result = cls.run_owasp_patterns(code)
        return (
            f"Bandit: \n{bandit_result}\n\n"
            f"Semgrep: \n{semgrep_result}\n\n"
            f"OWASP Top 10: \n{owasp_result}"
        )


@tool
def tool_scan_code_bandit(target_path: str) -> str:
    """
    <module_purpose>Runs the Bandit SAST tool on the provided target path to find common security issues in Python code.</module_purpose>
    <contract>Accepts a target path string. Returns the standard output of the Bandit scan.</contract>
    """
    return SASTScanner.run_bandit(target_path)


@tool
def tool_scan_code_semgrep(target_path: str) -> str:
    """
    <module_purpose>Executes the Semgrep security scanner to find advanced semantic security issues in code.</module_purpose>
    <contract>Accepts a target path string. Returns the full scan output with rule IDs and locations.</contract>
    """
    return SASTScanner.run_semgrep(target_path)
