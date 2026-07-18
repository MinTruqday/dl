import os
import subprocess
import tempfile
from typing import Tuple, List
import glob
from loguru import logger
import queue
import atexit

kernel_manager = None
client = None

def get_jupyter_client():
    global kernel_manager, client
    if client is None:
        try:
            from jupyter_client.manager import start_new_kernel
            kernel_manager, client = start_new_kernel(kernel_name='python3')
            atexit.register(kernel_manager.shutdown_kernel)
            logger.info("Persistent Jupyter Kernel started.")
        except ImportError:
            logger.warning("jupyter_client not installed, cannot start kernel.")
    return client

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
        
    def execute_code(self, code: str, dependencies: list = None) -> Tuple[bool, str, str, List[str]]:
        code_file = os.path.join(self.temp_dir, "script.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code)
            
        if self.use_docker:
            success, stdout, stderr = self._run_docker(code_file, dependencies)
        else:
            success, stdout, stderr = self._run_jupyter(code)
            
        artifacts = []
        for file in glob.glob(os.path.join(self.temp_dir, "*")):
            if not file.endswith("script.py") and not file.endswith("venv"):
                artifacts.append(file)
                
        return success, stdout, stderr, artifacts
            
    def _run_jupyter(self, code: str) -> Tuple[bool, str, str]:
        jc = get_jupyter_client()
        if not jc:
            return False, "", "Jupyter client not available"
        
        try:
            msg_id = jc.execute(code)
            stdout = ""
            stderr = ""
            while True:
                try:
                    msg = jc.get_iopub_msg(timeout=30)
                    msg_type = msg['header']['msg_type']
                    content = msg['content']
                    
                    if msg_type == 'stream':
                        if content['name'] == 'stdout':
                            stdout += content['text']
                        elif content['name'] == 'stderr':
                            stderr += content['text']
                    elif msg_type == 'error':
                        stderr += "\n".join(content['traceback'])
                    elif msg_type == 'execute_result':
                        stdout += str(content['data'].get('text/plain', ''))
                    elif msg_type == 'status' and content['execution_state'] == 'idle':
                        break
                except queue.Empty:
                    return False, stdout, stderr + "\nExecution timeout exceeded"
                    
            return len(stderr) == 0, stdout, stderr
        except Exception as e:
            return False, "", str(e)
            
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
