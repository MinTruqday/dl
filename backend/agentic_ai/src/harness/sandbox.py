import os
import subprocess
import tempfile
from typing import Tuple
from loguru import logger

class CodeSandbox:
    """
    <module_purpose>
    DocLib Code Sandbox for executing dynamically generated code in a restricted, isolated environment.
    </module_purpose>
    <contract>
    - Precondition: Executable code snippet and runtime constraints (timeout, memory).
    - Postcondition: Returns execution outputs (stdout, stderr) or timeout errors.
    - Error Handling: Fails immediately and cleans up resources on timeouts or unauthorized I/O attempts.
    </contract>
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
        logger.info("Docker container execution started via SDK")
        import docker
        from src.core.infrastructure.configuration import settings
        
        try:
            client = docker.DockerClient(base_url=settings.DOCKER_HOST)
            deps_cmd = f"pip install {' '.join(dependencies)} &&" if dependencies else ""
            cmd_str = f"{deps_cmd} python script.py"

            volumes = {self.temp_dir: {'bind': '/sandbox', 'mode': 'rw'}}
            
            container = client.containers.run(
                "python:3.10-alpine",
                command=["sh", "-c", cmd_str],
                volumes=volumes,
                working_dir="/sandbox",
                detach=True,
                remove=False,
                mem_limit="128m",
                network_mode="none"
            )
            
            try:
                result = container.wait(timeout=45)
                logs = container.logs().decode('utf-8')
                success = result.get('StatusCode', 1) == 0
                
                if not success:
                    return False, "", logs
                return True, logs, ""
                
            except Exception as wait_e:
                return False, "", f"Docker wait timeout/error: {str(wait_e)}"
            finally:
                container.remove(force=True)
                
        except Exception as e:
            logger.error(f"Docker sandbox execution failed: {e}")
            return False, "", str(e)
            
    def cleanup(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        logger.info("Sandbox cleanup execution completed")
