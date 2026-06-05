import os
import re

def replace_in_file(filepath, replacements):
    with open(filepath, "r") as f:
        content = f.read()
    
    # Needs to import prompt_registry if not present
    if "prompt_registry" not in content and "PromptType" not in content:
        # Add import
        import_stmt = "from src.core.prompt_registry import prompt_registry, PromptType\n"
        # Find where to put it, usually after other imports
        last_import = [m for m in re.finditer(r'^import .*$|^from .* import .*$', content, re.MULTILINE)]
        if last_import:
            pos = last_import[-1].end()
            content = content[:pos] + "\n" + import_stmt + content[pos:]
        else:
            content = import_stmt + "\n" + content

    for old, new in replacements:
        content = re.sub(old, new, content, flags=re.MULTILINE|re.DOTALL)
        
    with open(filepath, "w") as f:
        f.write(content)

base = "/Users/caominhtrung/Library/Mobile Documents/com~apple~CloudDocs/Documents/DocLib/backend/agentic-ai/src/"

# 1. semantic_router.py
r1 = [
    (r'template="""SYSTEM IDENTITY: DocLib Core System - Primary Router\.[\s\S]*?USER INPUT: \{question\}"""', 
     'template=prompt_registry.get(PromptType.PRIMARY_ROUTER)')
]
replace_in_file(base + "workflow/semantic_router.py", r1)

# 2. aggregator.py
r2 = [
    (r'final_prompt = f"""SYSTEM IDENTITY: DocLib Core System - Final Aggregator Engine\.[\s\S]*?RESPONSE:"""',
     'final_prompt = prompt_registry.get(PromptType.AGGREGATOR).format(query=query, gathered_data=gathered_data)')
]
replace_in_file(base + "workflow/aggregator.py", r2)

# 3. chat.py
r3 = [
    (r'text_prompt = f"SYSTEM IDENTITY: DocLib Core System - Conversational Assistant\.\\nOBJECTIVE: Provide a concise and friendly response\.\\nOUTPUT_LANGUAGE: Must exactly match the language of the user\'s input query\.\\n\\nUSER QUERY: \{req\.query\}"',
     'text_prompt = prompt_registry.get(PromptType.CHAT_ASSISTANT).format(query=req.query)')
]
replace_in_file(base + "api/chat.py", r3)

# 4. retrieval.py
r4 = [
    (r'template="""SYSTEM IDENTITY: DocLib Core System - Multi-Query Generator\.[\s\S]*?OUTPUT:"""',
     'template=prompt_registry.get(PromptType.MULTI_QUERY)')
]
replace_in_file(base + "rag/retrieval.py", r4)

# 5. inference.py
r5 = [
    (r'prompt = f"""SYSTEM IDENTITY: DocLib Core System - Plagiarism Detection Engine\.[\s\S]*?"""',
     'prompt = prompt_registry.get(PromptType.PLAGIARISM_DETECTION).format(text=req.text[:1000], context=context)'),
    (r'prompt = f"SYSTEM IDENTITY: DocLib Core System - Content Review Engine\.\\nOBJECTIVE: Evaluate the following text based on these criteria: \{criteria_str\}\. Provide a detailed report with Strengths, Weaknesses, and Improvement Suggestions\.\\nOUTPUT_LANGUAGE: Must match the language of the input text\.\\n\\nTEXT: \{req\.text\[:3000\]\}"',
     'prompt = prompt_registry.get(PromptType.CONTENT_REVIEW).format(criteria_str=criteria_str, text=req.text[:3000])')
]
replace_in_file(base + "api/inference.py", r5)

# 6. dispatcher.py
r6 = [
    (r'system_prompt = f"""SYSTEM IDENTITY: DocLib Core System - API Tool Dispatcher\.[\s\S]*?OUTPUT_LANGUAGE: Must exactly match the language of the user\'s input query\."""',
     'system_prompt = prompt_registry.get(PromptType.TOOL_DISPATCHER)')
]
replace_in_file(base + "workflow/dispatcher.py", r6)

# 7. code_interpreter.py
r7 = [
    (r'"SYSTEM IDENTITY: DocLib Core System - Python Execution Engine\.\\n"',
     'prompt_registry.get(PromptType.CODE_INTERPRETER_SYSTEM) + "\\n"')
]
replace_in_file(base + "agents/code_interpreter.py", r7)

# 8. reasoning.py
r8 = [
    (r'prompt = f"""SYSTEM IDENTITY: DocLib Core System - Analytical Engine\.[\s\S]*?conclusion\."""',
     'prompt = prompt_registry.get(PromptType.ANALYTICAL_ENGINE).format(task=task)'),
    (r'eval_prompt = f"""SYSTEM IDENTITY: DocLib Core System - Quality Evaluation Engine\.[\s\S]*?structure\."""',
     'eval_prompt = prompt_registry.get(PromptType.QUALITY_EVALUATION).format(query=query, answer=answer, context_str=context_str[:3000])')
]
replace_in_file(base + "agents/reasoning.py", r8)

# 9. draft_generator.py
r9 = [
    (r'system_prompt = f"""SYSTEM IDENTITY: DocLib Core System - Document Generation Engine\.[\s\S]*?structure\."""',
     'system_prompt = prompt_registry.get(PromptType.DOCUMENT_GENERATION).format(format_type=format_type)')
]
replace_in_file(base + "agents/draft_generator.py", r9)

print("Replacement complete.")
