from typing import Any, Dict, Optional
from loguru import logger

from langchain_core.prompts import ChatPromptTemplate
from src.agents.planning import llm
from src.core.registry import PromptType, registry
from src.core.security.drm_enforcement import drm_enforcement_engine
from src.schemas.drm import DRMPolicyOutput

SYSTEM_PROMPT = registry.get(PromptType.DRM_POLICY)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Evaluate high-risk DRM escalation for context: {context_data}")
])

def _build_chain():
    return prompt | llm.with_structured_output(DRMPolicyOutput)

async def evaluate_drm_policy(
    user_id: str,
    document_id: str,
    client_ip: str,
    user_tier: str = "BASIC",
    document_type: str = "standard",
    device_fingerprint: Optional[str] = None,
    email: str = ""
) -> Dict[str, Any]:
    fast_result = await drm_enforcement_engine.fast_deterministic_enforce(
        user_id=user_id,
        document_id=document_id,
        client_ip=client_ip,
        user_tier=user_tier,
        document_type=document_type,
        device_fingerprint=device_fingerprint,
        email=email
    )

    if not fast_result.get("requires_ai_escalation", False):
        return fast_result

    try:
        import json

        logger.warning("DRM escalation started")
        chain = _build_chain()
        ai_res = await chain.ainvoke({"context_data": json.dumps(fast_result)})
        if isinstance(ai_res, DRMPolicyOutput):
            final_dict = ai_res.model_dump()
        else:
            final_dict = fast_result
    except Exception:
        logger.exception("DRM escalation failed")
        final_dict = fast_result

    return final_dict
