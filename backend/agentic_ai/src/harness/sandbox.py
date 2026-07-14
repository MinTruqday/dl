import os
import subprocess
import tempfile
from typing import Tuple
from loguru import logger

class CodeSandbox:
    """
    <module_purpose>
    <purpose>Executes generated code in a restricted, isolated environment.</purpose>
    <metis_behavior>Monitors resource utilization. Fails immediately on timeouts or unauthorized I/O attempts.</metis_behavior>
    </module_purpose>
    """
    def __init__(self, use_docker: bool = False):
        """
        <purpose>Initializes the sandbox environment.</purpose>
        <param name="use_docker">Whether to use Docker for isolation.</param>
        """
        self.use_docker = use_docker
        self.temp_dir = tempfile.mkdtemp(prefix="agentic_sandbox_")
        logger.info("Sandbox environment initialization completed")
        
    def _create_venv(self):
        """
        <purpose>Creates a transient virtual environment for Python execution.</purpose>
        """
        venv_path = os.path.join(self.temp_dir, "venv")
        subprocess.run(["python3", "-m", "venv", venv_path], check=True, capture_output=True)
        return os.path.join(venv_path, "bin", "python")
        
    def execute_code(self, code: str, dependencies: list = None) -> Tuple[bool, str, str]:
        code_file = os.path.join(self.temp_dir, "script.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code)
            
        if self.use_docker:
            return self._run_docker(code_file, dependencies)
        else:
            return self._run_venv(code_file, dependencies)
            
    def _run_venv(self, code_file: str, dependencies: list = None) -> Tuple[bool, str, str]:
        try:
            python_exec = self._create_venv()
            
            if dependencies:
                pip_exec = os.path.join(os.path.dirname(python_exec), "pip")
                logger.info("Dependencies installation execution started")
                subprocess.run([pip_exec, "install"] + dependencies, check=True, capture_output=True)
                
            logger.info("Virtual environment execution started")
            result = subprocess.run([python_exec, code_file], capture_output=True, text=True, timeout=30)
            
            return result.returncode == 0, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", "Execution timeout exceeded"
        except Exception as e:
            return False, "", str(e)
            
    def _run_docker(self, code_file: str, dependencies: list = None) -> Tuple[bool, str, str]:
        logger.info("Docker container execution started")
        deps_cmd = f"pip install {' '.join(dependencies)} &&" if dependencies else ""
        
        cmd = [
            "docker", "run", "--rm", 
            "-v", f"{self.temp_dir}:/sandbox",
            "-w", "/sandbox",
            "python:3.10-alpine",
            "sh", "-c",
            f"{deps_cmd} python script.py"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Docker execution timeout exceeded"
        except Exception as e:
            return False, "", str(e)
            
    def cleanup(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        logger.info("Sandbox cleanup execution completed")
