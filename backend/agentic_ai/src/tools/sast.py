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


class SASTScanner:
    """
    <module_purpose>
    <purpose>Runs Static Application Security Testing against code artifacts using Bandit, Semgrep, and OWASP Top 10 pattern matching.</purpose>
    <metis_behavior>Acts as the deterministic backbone for the SecOpsAgent. Returns full, actionable scan output including severity levels and line references.</metis_behavior>
    </module_purpose>
    """

    @staticmethod
    def run_owasp_patterns(code: str) -> str:
        import re
        findings = []
        for category, patterns in OWASP_PATTERNS.items():
            for pattern in patterns:
                matches = [(m.start(), m.group()) for m in re.finditer(pattern, code, re.IGNORECASE)]
                for pos, match in matches:
                    line_num = code[:pos].count("\n") + 1
                    findings.append(f"[OWASP {category}] Line {line_num}: {match.strip()[:80]}")
        if not findings:
            return "OWASP Top 10 check: No obvious patterns detected"
        return "\n".join(findings)

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
            f"=== Bandit ===\n{bandit_result}\n\n"
            f"=== Semgrep ===\n{semgrep_result}\n\n"
            f"=== OWASP Top 10 ===\n{owasp_result}"
        )


@tool
def tool_scan_code_bandit(target_path: str) -> str:
    """
    <tool_definition>
    <purpose>Executes the Bandit security scanner to find common security issues in Python code.</purpose>
    <input_params>target_path: The filesystem path to scan.</input_params>
    <return_value>Full scan output including severity, confidence, and line numbers.</return_value>
    </tool_definition>
    """
    return SASTScanner.run_bandit(target_path)


@tool
def tool_scan_code_semgrep(target_path: str) -> str:
    """
    <tool_definition>
    <purpose>Executes the Semgrep security scanner to find advanced semantic security issues in code.</purpose>
    <input_params>target_path: The filesystem path to scan.</input_params>
    <return_value>Full scan output with rule IDs and locations.</return_value>
    </tool_definition>
    """
    return SASTScanner.run_semgrep(target_path)
