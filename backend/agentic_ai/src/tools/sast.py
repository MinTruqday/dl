import json
import os
import subprocess
import tempfile

from langchain_core.tools import tool
from loguru import logger

class PythonAstScanner:
    @staticmethod
    def scan(code: str) -> str:
        import ast
        findings = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ["eval", "exec"]:
                            findings.append(
                                {
                                    "rule": "dynamic_code_execution",
                                    "symbol": node.func.id,
                                    "line": node.lineno,
                                }
                            )
                    elif isinstance(node.func, ast.Attribute):
                        if node.func.attr in ["system", "popen", "call"]:
                            findings.append(
                                {
                                    "rule": "command_execution",
                                    "symbol": node.func.attr,
                                    "line": node.lineno,
                                }
                            )
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and any(keyword in target.id.lower() for keyword in ["password", "secret", "token", "api_key"]):
                            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                                findings.append(
                                    {
                                        "rule": "hardcoded_secret",
                                        "symbol": target.id,
                                        "line": node.lineno,
                                    }
                                )
        except SyntaxError:
            return json.dumps({"status": "invalid_syntax", "findings": []})
        except Exception:
            logger.exception("AST security scan failed")
            return json.dumps({"status": "scan_failed", "findings": []})

        return json.dumps({"status": "success", "findings": findings})


class SASTScanner:
    """
    <module_purpose>Runs Static Application Security Testing against code artifacts using Bandit, Semgrep, and AST-based OWASP Top 10 pattern matching.</module_purpose>
    <contract>Acts as the deterministic backbone for the SecOpsAgent. Returns full, actionable scan output including severity levels and line references.</contract>
    """

    @staticmethod
    async def run_owasp_patterns(code: str) -> str:
        ast_result = PythonAstScanner.scan(code)
        
        from src.core.registry import PromptType, registry
        from src.utils.huggingface import HFInferenceChat
        from huggingface_hub import AsyncInferenceClient
        from src.core.infrastructure.configuration import settings
        from langchain_core.messages import HumanMessage, SystemMessage

        try:
            client = AsyncInferenceClient(model=settings.LLM_MODEL, token=settings.HF_TOKEN)
            llm = HFInferenceChat(client=client, model=settings.LLM_MODEL)
            
            system_prompt = registry.get(PromptType.SAST_OWASP_SCAN).replace("{{code}}", code)
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=code)
            ]
            response = await llm.ainvoke(messages, max_tokens=1024, temperature=0.1)
            llm_result = response.content.strip()
        except Exception:
            logger.exception("LLM OWASP analysis failed")
            llm_result = json.dumps({"status": "model_analysis_failed"})

        return json.dumps(
            {
                "ast": json.loads(ast_result),
                "model_analysis": llm_result,
            },
            ensure_ascii=False,
        )

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
                output = (result.stderr or "").strip()
            return json.dumps(
                {
                    "status": "success",
                    "return_code": result.returncode,
                    "output": output,
                }
            )
        except FileNotFoundError:
            return json.dumps({"status": "dependency_missing"})
        except subprocess.TimeoutExpired:
            return json.dumps({"status": "timeout"})
        except Exception:
            logger.exception("Bandit execution failed")
            return json.dumps({"status": "execution_failed"})
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
            return json.dumps(
                {
                    "status": "success",
                    "return_code": result.returncode,
                    "output": output,
                }
            )
        except FileNotFoundError:
            return json.dumps({"status": "dependency_missing"})
        except subprocess.TimeoutExpired:
            return json.dumps({"status": "timeout"})
        except Exception:
            logger.exception("Bandit execution failed")
            return json.dumps({"status": "execution_failed"})

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
                output = (result.stderr or "").strip()
            return json.dumps(
                {
                    "status": "success",
                    "return_code": result.returncode,
                    "output": output,
                }
            )
        except FileNotFoundError:
            return json.dumps({"status": "dependency_missing"})
        except subprocess.TimeoutExpired:
            return json.dumps({"status": "timeout"})
        except Exception:
            logger.exception("Semgrep execution failed")
            return json.dumps({"status": "execution_failed"})
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
            return json.dumps(
                {
                    "status": "success",
                    "return_code": result.returncode,
                    "output": output,
                }
            )
        except FileNotFoundError:
            return json.dumps({"status": "dependency_missing"})
        except subprocess.TimeoutExpired:
            return json.dumps({"status": "timeout"})
        except Exception:
            logger.exception("Semgrep execution failed")
            return json.dumps({"status": "execution_failed"})

    @classmethod
    async def full_scan(cls, code: str) -> str:
        bandit_result = cls.run_bandit_on_code(code)
        semgrep_result = cls.run_semgrep_on_code(code)
        owasp_result = await cls.run_owasp_patterns(code)
        return json.dumps(
            {
                "bandit": json.loads(bandit_result),
                "semgrep": json.loads(semgrep_result),
                "owasp": json.loads(owasp_result),
            },
            ensure_ascii=False,
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
