from typing import List, Dict, Any, Optional
import json
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.output_parsers import JsonOutputParser
from loguru import logger
from src.core.config import settings

_hf_endpoint = HuggingFaceEndpoint(
    repo_id=settings.LLAMA_MODEL,
    huggingfacehub_api_token=settings.HF_TOKEN,
    temperature=0.1
)
llm = ChatHuggingFace(llm=_hf_endpoint)

from src.models.plan import PlanStep, ExecutionPlan

class AgenticBrain:
    def __init__(self):
        self.llm = llm
        self.parser = JsonOutputParser(pydantic_object=ExecutionPlan)
        
    async def _invoke_llm(self, messages):
        import httpx
        try:
            return await self.llm.ainvoke(messages)
        except (httpx.TimeoutException, httpx.HTTPStatusError, Exception) as primary_err:
            logger.warning(f"Brain: Primary LLM failed ({primary_err}).")
            raise primary_err
        
    async def create_plan(self, req) -> List[Dict[str, str]]:
        logger.info(f"Brain: Creating structured plan for query: {req.query}")
        
        system_prompt = """SYSTEM IDENTITY: DocLib Core System - Neural Routing Brain.
OBJECTIVE: Analyze the user's request, perform logical reasoning, and decompose it into a structured execution plan.
OUTPUT_LANGUAGE: The JSON values must exactly match the language of the user's input query.

AVAILABLE AGENTS:
- ActionAgent: Executes system operations, modifies personal data, manages wallet balance, deletes/restores documents.
- KnowledgeAgent: Searches, reads, and analyzes internal documents from the DocLib library.
- CodeInterpreter: Writes and executes Python code for data processing, calculations, and plotting.
- SearchEngine: Performs web searches to retrieve external information.
- DraftGenerator: Generates drafts, writes emails, formats text into Markdown or LaTeX.
- ReasoningAgent: Performs deep logical analysis and evaluates quality.

RULES:
1. You MUST output a strictly valid JSON object.
2. The JSON object must contain a "reasoning" string detailing your Chain of Thought.
3. The JSON object must contain a "steps" array with the execution sequence.

<example>
<user_input>Search for AI trends in 2024 on the internet and create a markdown draft document.</user_input>
<output>
{{
    "reasoning": "The request has two parts: searching the internet for information, then drafting a document. SearchEngine retrieves data first, then DraftGenerator formats the output.",
    "steps": [
        {{"agent": "SearchEngine", "task": "Search for AI trends in 2024"}},
        {{"agent": "DraftGenerator", "task": "Draft a markdown document summarizing the found AI trends"}}
    ]
}}
</output>
</example>

<example>
<user_input>Draw a pie chart of documents uploaded this month.</user_input>
<output>
{{
    "reasoning": "The user wants a chart based on system data. ActionAgent fetches the statistics, then CodeInterpreter draws the chart.",
    "steps": [
        {{"agent": "ActionAgent", "task": "Fetch document upload statistics for the current month"}},
        {{"agent": "CodeInterpreter", "task": "Generate a pie chart using the provided upload statistics"}}
    ]
}}
</output>
</example>

{format_instructions}"""
        
        history_str = ""
        if hasattr(req, "conversation_history") and req.conversation_history:
            history_str = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in req.conversation_history[-5:]])
            
        prompt = f"Recent conversation history:\n{history_str}\n\nLatest request: {req.query}\nCurrent context: {req.context if hasattr(req, 'context') else 'None'}"
        
        try:
            format_instructions = self.parser.get_format_instructions()
            messages = [
                SystemMessage(content=system_prompt.format(format_instructions=format_instructions)),
                HumanMessage(content=prompt)
            ]
            
            response = await self._invoke_llm(messages)
            
            parsed_result = self.parser.invoke(response)
            
            steps = [{"agent": step["agent"], "task": step["task"]} for step in parsed_result.get("steps", [])]
            
            if not steps:
                steps = [{"agent": "ActionAgent", "task": "Xử lý trực tiếp yêu cầu"}]
                
            return steps
            
        except Exception as e:
            logger.error(f"Brain: Plan creation failed: {e}")
            return [{"agent": "ActionAgent", "task": req.query}]

brain = AgenticBrain()

