import io
import sys
import contextlib
from loguru import logger

class CodeInterpreterAgent:
    def __init__(self):
        pass

    async def execute(self, code: str) -> str:
        logger.info("CodeInterpreter: Đang thực thi mã Python")
        
        forbidden = ["os.system", "subprocess", "rm -rf", "shutil.rmtree", "exit()", "sys.exit"]
        for f in forbidden:
            if f in code:
                return f"Lỗi bảo mật: Mã nguồn chứa lệnh không được phép '{f}'."

        output_buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
                local_env = {}
                global_env = {"__builtins__": __builtins__}
                exec(code, global_env, local_env)
                
            output = output_buffer.getvalue()
            return f"Kết quả thực thi mã:\n{output}" if output else "Mã đã được thực thi thành công (Không có output)."
        except Exception as e:
            logger.error(f"CodeInterpreter: Lỗi khi chạy code: {e}")
            error_output = output_buffer.getvalue()
            return f"Lỗi trong quá trình chạy mã Python: {e}\nChi tiết:\n{error_output}"

code_interpreter_agent = CodeInterpreterAgent()
