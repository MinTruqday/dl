import io
import base64
import contextlib
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from RestrictedPython import compile_restricted
from RestrictedPython import safe_builtins, limited_builtins, utility_builtins
from RestrictedPython.PrintCollector import PrintCollector
from loguru import logger
from langchain_core.messages import SystemMessage, HumanMessage

def setup_safe_env():
    env = safe_builtins.copy()
    env.update(limited_builtins)
    env.update(utility_builtins)
    
    env['_print_'] = PrintCollector
    env['_getattr_'] = getattr
    env['_getitem_'] = lambda ob, index: ob[index]
    env['_write_'] = lambda obj: obj
    env['_getiter_'] = iter
    
    _plot_data = []
    
    def safe_show(*args, **kwargs):
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        _plot_data.append(img_base64)
        plt.clf()
        
    safe_plt = type('SafePlt', (), {
        'plot': plt.plot,
        'bar': plt.bar,
        'scatter': plt.scatter,
        'pie': plt.pie,
        'title': plt.title,
        'xlabel': plt.xlabel,
        'ylabel': plt.ylabel,
        'legend': plt.legend,
        'show': safe_show,
        'figure': plt.figure,
        'grid': plt.grid,
        'subplots': plt.subplots,
        'axis': plt.axis
    })
    
    env['math'] = math
    env['np'] = np
    env['pd'] = pd
    env['plt'] = safe_plt
    
    return env, _plot_data

class CodeInterpreterAgent:
    def __init__(self):
        pass

    async def execute(self, task_desc: str) -> str:
        logger.info(f"CodeInterpreter: Processing task (Safe Mode): {task_desc}")
        
        try:
            from src.core.brain import llm
            
            system_prompt = (
                "Bạn là một trợ lý phân tích dữ liệu và lập trình Python. Hãy viết mã Python để hoàn thành yêu cầu sau.\n"
                "Trả về DUY NHẤT mã Python nằm trong thẻ ```python ... ```, KHÔNG GIẢI THÍCH THÊM.\n"
                "Môi trường của bạn đã có sẵn các thư viện sau: `math`, `np` (numpy), `pd` (pandas), `plt` (matplotlib.pyplot an toàn).\n"
                "Bạn CHỈ ĐƯỢC PHÉP DÙNG các biến toàn cục này và built-in của Python. TUYỆT ĐỐI không dùng lệnh `import` bất kỳ thư viện nào."
            )
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=task_desc)
            ]
            response = await llm.ainvoke(messages)
            content = response.content.strip()
            
            if "```python" in content:
                code = content.split("```python")[1].split("```")[0].strip()
            elif "```" in content:
                code = content.split("```")[1].strip()
            else:
                code = content.strip()

            if "import " in code:
                return "Lỗi bảo mật: Không cho phép sử dụng lệnh `import` trong môi trường an toàn. Hãy dùng các thư viện đã được cung cấp sẵn (np, pd, plt, math)."

            code = "print = _print_()\n" + code
            
            try:
                byte_code = compile_restricted(code, '<inline>', 'exec')
            except Exception as ce:
                return f"Lỗi biên dịch mã an toàn: {ce}"

            env, _plot_data = setup_safe_env()
            
            try:
                exec(byte_code, env, None)
            except Exception as ee:
                return f"Lỗi thực thi mã: {ee}"
                
            printed_output = ""
            if "print" in env and hasattr(env["print"], "txt"):
                printed_output = env["print"].txt
                
            final_res = ""
            if printed_output:
                final_res += f"Kết quả in ra:\n{printed_output}\n"
            if _plot_data:
                final_res += f"Đã sinh ra {len(_plot_data)} biểu đồ:\n\n"
                for i, b64 in enumerate(_plot_data):
                    final_res += f"![Biểu đồ kết quả](data:image/png;base64,{b64})\n"
            
            if not final_res:
                final_res = "Mã đã được thực thi thành công (Không có output)."
                
            return final_res
        except Exception as e:
            logger.error(f"CodeInterpreter: Execution failed: {e}")
            return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

code_interpreter_agent = CodeInterpreterAgent()

