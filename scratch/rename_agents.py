import os
import re

directories = [
    "backend/agentic-ai/src/agents/",
    "backend/agentic-ai/src/workflow/",
    "backend/agentic-ai/src/tools/",
]

replacements = {
    "KnowledgeAgent": "Knowledge",
    "knowledge_agent": "knowledge",
    "ReasoningAgent": "Reasoning",
    "reasoning_agent": "reasoning",
    "CodeInterpreterAgent": "CodeInterpreter",
    "code_interpreter_agent": "code_interpreter",
    "DraftGeneratorAgent": "DraftGenerator",
    "draft_generator_agent": "draft_generator",
    "AggregatorAgent": "Aggregator",
    "aggregator_agent": "aggregator",
    "RouterAgent": "SemanticRouter",
    "router_agent": "semantic_router",
    "SearchEngineAgent": "SearchEngine",
    "search_engine_agent": "search_engine",
    "action_agent": "action",
    "ToolDispatcherAgent": "ToolDispatcher"
}

import glob

files_to_check = []
for d in directories:
    for root, _, files in os.walk(d):
        for file in files:
            if file.endswith(".py"):
                files_to_check.append(os.path.join(root, file))

for filepath in files_to_check:
    with open(filepath, "r") as f:
        content = f.read()
    
    new_content = content
    # Do replacements in a specific order if necessary, but dict order is fine here since keys are mostly distinct
    for k, v in replacements.items():
        # Avoid partial replacements (like 'knowledge_agent' inside 'knowledge_agent_app')
        # Wait, if we replace knowledge_agent with knowledge, knowledge_agent_app becomes knowledge_app
        if k == "knowledge_agent":
            new_content = re.sub(r'\bknowledge_agent_app\b', 'knowledge_app', new_content)
            new_content = re.sub(r'\bknowledge_agent\b', 'knowledge', new_content)
        elif k == "KnowledgeAgent":
            new_content = re.sub(r'\bKnowledgeAgent\b', 'Knowledge', new_content)
        else:
            new_content = re.sub(r'\b' + k + r'\b', v, new_content)
            
    if new_content != content:
        with open(filepath, "w") as f:
            f.write(new_content)
        print(f"Updated {filepath}")

