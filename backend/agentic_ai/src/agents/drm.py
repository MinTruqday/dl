from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from src.tools.interface import llm
from src.tools.drm import check_network_anomaly, get_user_trust_profile, analyze_document_risk
import asyncio
from src.core.registry import registry, PromptType

from src.schemas.model import DRMPolicyOutput

SYSTEM_PROMPT = registry.get(PromptType.DRM_POLICY)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Evaluate the DRM policy for this request.")
])

def _build_chain():
    """Build LLM chain with structured output if supported, else plain LLM."""
    if hasattr(llm, "with_structured_output"):
        try:
            return prompt | llm.with_structured_output(DRMPolicyOutput)
        except Exception:
            pass
    return prompt | llm

async def evaluate_drm_policy(user_id: str, document_id: str, client_ip: str, user_tier: str, document_type: str) -> Dict[str, Any]:
    """Execute the DRM Agent DAG to gather context and evaluate policy."""
    # 1. Gather context concurrently
    network_task = check_network_anomaly.ainvoke({"user_id": user_id, "client_ip": client_ip})
    trust_task = get_user_trust_profile.ainvoke({"user_id": user_id, "user_tier": user_tier})
    risk_task = analyze_document_risk.ainvoke({"document_id": document_id, "document_type": document_type})
    
    network_ctx, trust_ctx, risk_ctx = await asyncio.gather(network_task, trust_task, risk_task)
    
    context_data = {
        "network_anomaly": network_ctx,
        "user_trust": trust_ctx,
        "document_risk": risk_ctx
    }
    
    # 2. Evaluate with LLM
    try:
        chain = _build_chain()
        result = await chain.ainvoke({"context_data": str(context_data)})
        
        if isinstance(result, DRMPolicyOutput):
            return result.model_dump()
        elif isinstance(result, dict):
            return result
        else:
            # Parse raw text output from plain LLM
            import json, re
            content = result.content if hasattr(result, "content") else str(result)
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f"Could not parse LLM output: {content[:200]}")
            
    except Exception as e:
        logger.warning(f"DRM Agent LLM evaluation failed, using LEVEL_2 fallback: {e}")
        return DRMPolicyOutput(
            decision="LEVEL_2",
            reasoning=f"Fallback due to AI error: {str(e)[:100]}",
            enable_visual_watermark=True,
            enable_micro_dots=True,
            enable_aes_encryption=True,
            hardware_binding_strict=False
        ).model_dump()

