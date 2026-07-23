from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from src.agents.planning import llm
from src.tools.drm import check_network_anomaly, get_user_trust_profile, analyze_document_risk
import asyncio
from src.core.infrastructure.configuration import settings
import json
import redis

from src.core.registry import registry, PromptType
from src.schemas.drm import DRMPolicyOutput

SYSTEM_PROMPT = registry.get(PromptType.DRM_POLICY)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Evaluate the DRM policy for this request.")
])

def _build_chain():
    if hasattr(llm, "with_structured_output"):
        try:
            return prompt | llm.with_structured_output(DRMPolicyOutput)
        except Exception:
            pass
    return prompt | llm

async def evaluate_drm_policy(user_id: str, document_id: str, client_ip: str, user_tier: str, document_type: str) -> Dict[str, Any]:

    try:
        redis_client = redis.from_url(settings.REDIS_URI, decode_responses=True)
        cache_key = f"drm_policy:{document_id}:{user_id}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info("DRM Policy found in cache")
            return json.loads(cached_result)
    except Exception as e:
        logger.warning(f"DRM Cache read failed: {e}")
        redis_client = None

    network_task = check_network_anomaly.ainvoke({"user_id": user_id, "client_ip": client_ip})
    trust_task = get_user_trust_profile.ainvoke({"user_id": user_id, "user_tier": user_tier})
    risk_task = analyze_document_risk.ainvoke({"document_id": document_id, "document_type": document_type})
    
    network_ctx, trust_ctx, risk_ctx = await asyncio.gather(network_task, trust_task, risk_task)
    
    context_data = {
        "network_anomaly": network_ctx,
        "user_trust": trust_ctx,
        "document_risk": risk_ctx
    }
    try:
        chain = _build_chain()
        result = await chain.ainvoke({"context_data": str(context_data)})
        
        if isinstance(result, DRMPolicyOutput):
            final_dict = result.model_dump()
        elif isinstance(result, dict):
            final_dict = result
        else:
            import json, re
            content_str = result.content if hasattr(result, "content") else str(result)
            match = re.search(r'\{.*\}', content_str, re.DOTALL)
            if match:
                final_dict = json.loads(match.group(0))
            else:
                raise ValueError(f"Could not parse LLM output: {content_str[:200]}")
        if redis_client:
            try:
                redis_client.setex(cache_key, 3600, json.dumps(final_dict))
            except Exception as e:
                logger.warning(f"DRM Cache write failed: {e}")
                
        return final_dict
            
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

