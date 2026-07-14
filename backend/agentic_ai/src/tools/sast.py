import subprocess
from typing import Dict, Any, List
from langchain_core.tools import tool
from loguru import logger

class SASTScanner:
    """
    <module_purpose>
    <purpose>Runs Static Application Security Testing against code artifacts.</purpose>
    <metis_behavior>Acts as the deterministic backbone for the SecOpsAgent. Relies on Bandit and Semgrep patterns.</metis_behavior>
    </module_purpose>
    """
    @staticmethod
    def run_bandit(target_path: str) -> str:
        """
        <method_purpose>
        <purpose>Executes the Bandit security scanner on the target directory.</purpose>
        <input_params>target_path (str): The filesystem path to scan.</input_params>
        <return_value>str: Summary of the scan outcome.</return_value>
        </method_purpose>
        """
        try:
            logger.info("Bandit execution started")
            cmd = ["bandit", "-r", target_path, "-f", "txt"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return "Bandit execution completed successfully"
            else:
                return "Bandit execution detected potential issues"
        except FileNotFoundError:
            return "Bandit dependency is missing in the current environment"
        except Exception as e:
            logger.exception("Bandit execution failed")
            return "Bandit execution failed"
            
    @staticmethod
    def run_semgrep(target_path: str) -> str:
        try:
            logger.info("Semgrep execution started")
            cmd = ["semgrep", "scan", "--config", "auto", target_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return "Semgrep execution completed successfully"
            else:
                return "Semgrep execution detected potential issues"
        except FileNotFoundError:
            return "Semgrep dependency is missing in the current environment"
        except Exception as e:
            logger.exception("Semgrep execution failed")
            return "Semgrep execution failed"

@tool
def tool_scan_code_bandit(target_path: str) -> str:
    return SASTScanner.run_bandit(target_path)

@tool
def tool_scan_code_semgrep(target_path: str) -> str:
    return SASTScanner.run_semgrep(target_path)
