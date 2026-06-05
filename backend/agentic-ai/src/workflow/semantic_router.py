from loguru import logger
from langchain_core.prompts import PromptTemplate
from src.core.config import settings
from huggingface_hub import AsyncInferenceClient
from src.utils.hf import HFInferenceChat

class RouterAgent:
    def __init__(self):
        llama_model = settings.LLAMA_MODEL
        if not llama_model:
            raise ValueError("LLAMA_MODEL is not set")
            
        self.llama_client = AsyncInferenceClient(
            model=settings.LLAMA_MODEL,
            token=settings.HF_TOKEN,
        )
        self.router_llm = HFInferenceChat(client=self.llama_client, model=settings.LLAMA_MODEL)

    async def execute(self, query: str) -> dict:
        prompt = PromptTemplate(
            template="""SYSTEM IDENTITY: DocLib Core System - Primary Router.
OBJECTIVE: Analyze the user's intent and determine the primary processing route.
OUTPUT_LANGUAGE: The JSON values must exactly match the language of the user's input query.

ROUTES AVAILABLE:
- "action": System operations, data mutations, wallet transactions, document management.
- "knowledge": Information retrieval, academic questions, document querying, mathematical logic, code generation.
- "chat": Casual conversation, greetings, pleasantries.

RULES:
1. Provide a step-by-step reasoning in the "reasoning" field.
2. Return the chosen route in the "route" field.
3. If the route is "chat", provide a direct response in the "answer" field. Otherwise, leave it empty.
4. Output ONLY valid JSON.

<example>
<user_input>Create a new folder called Study Materials</user_input>
<output>
{{
    "reasoning": "The user is requesting a system operation to create a new directory.",
    "route": "action",
    "answer": ""
}}
</output>
</example>

<example>
<user_input>Summarize chapter 1 of Clean Code for me</user_input>
<output>
{{
    "reasoning": "The user is asking for a document summary, which requires knowledge retrieval and analysis.",
    "route": "knowledge",
    "answer": ""
}}
</output>
</example>

USER INPUT: {question}""",
            input_variables=["question"]
        )
        try:
            from src.workflow.brain import llm
            from pydantic import BaseModel, Field
            
            class RouteDecision(BaseModel):
                reasoning: str = Field(description="Step-by-step reasoning")
                route: str = Field(description="The chosen route: 'action', 'knowledge', or 'chat'")
                answer: str = Field(description="Direct response if route is 'chat', else empty string")
            
            try:
                structured_llm = llm.with_structured_output(RouteDecision)
                res = await structured_llm.ainvoke(prompt.format(question=query))
                route = res.route.lower()
                answer = res.answer
            except Exception:
                import json
                import re
                raw_res = await llm.ainvoke(prompt.format(question=query))
                match = re.search(r'\{.*\}', raw_res.content, re.DOTALL)
                if match:
                    decision = json.loads(match.group(0))
                else:
                    decision = {}
                route = decision.get("route", "knowledge").lower()
                answer = decision.get("answer", "")
            
            if route not in ["chat", "action", "knowledge"]:
                route = "knowledge"
                
            logger.info(f"RouterAgent: Classified request as route='{route}'")
            return {"route": route, "answer": answer}
            
        except Exception as e:
            logger.error(f"RouterAgent: Routing failed: {e}")
            return {"route": "knowledge", "answer": ""}

router_agent = RouterAgent()
