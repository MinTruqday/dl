import asyncio
from typing import Any, Dict, Optional

from src.tools.drm import (
    generate_dynamic_watermark,
    issue_temporary_aes_key,
    verify_device_fingerprint,
    check_network_anomaly,
    get_user_trust_profile,
    analyze_document_risk,
)
from src.schemas.drm import WatermarkConfig, AntiExfiltrationFlags

class DRMEnforcementEngine:
    async def fast_deterministic_enforce(
        self,
        user_id: str,
        document_id: str,
        client_ip: str,
        user_tier: str = "BASIC",
        document_type: str = "standard",
        device_fingerprint: Optional[str] = None,
        email: str = ""
    ) -> Dict[str, Any]:
        """
        Fast 100% Deterministic DRM Enforcement (< 2ms, ZERO Token Cost).
        """
        network_task = check_network_anomaly.ainvoke({"user_id": user_id, "client_ip": client_ip})
        trust_task = get_user_trust_profile.ainvoke({"user_id": user_id, "user_tier": user_tier})
        risk_task = analyze_document_risk.ainvoke({"document_id": document_id, "document_type": document_type})
        fp_task = verify_device_fingerprint.ainvoke({"user_id": user_id, "device_fingerprint": device_fingerprint, "client_ip": client_ip})

        network_res, trust_res, risk_res, fp_res = await asyncio.gather(
            network_task, trust_task, risk_task, fp_task
        )

        trust_score = trust_res.get("trust_score", 50)
        risk_level = risk_res.get("risk_level", "LOW")
        anomaly = network_res.get("system_flag_anomaly", False)
        fp_matched = fp_res.get("matched", True)

        if anomaly:
            return {
                "decision": "BLOCKED",
                "reasoning": "Network anomaly detected (IP hopping / rate-limit breach)",
                "watermark": WatermarkConfig().model_dump(),
                "anti_exfiltration": AntiExfiltrationFlags().model_dump(),
                "enable_aes_encryption": False,
                "hardware_binding_strict": False,
                "requires_ai_escalation": True
            }

        decision = "LEVEL_0"
        enable_aes = False
        strict_hw = False
        block_print = False
        block_copy = False
        block_screenshot = False
        enable_watermark = False

        if risk_level == "HIGH" or trust_score < 60 or not fp_matched:
            decision = "LEVEL_3"
            enable_aes = True
            strict_hw = True
            block_print = True
            block_copy = True
            block_screenshot = True
            enable_watermark = True
        elif trust_score < 80:
            decision = "LEVEL_2"
            enable_watermark = True
            block_print = True
            block_copy = True
        else:
            decision = "LEVEL_1"
            enable_watermark = True

        watermark_payload = await generate_dynamic_watermark.ainvoke({
            "user_id": user_id,
            "client_ip": client_ip,
            "email": email
        }) if enable_watermark else {"enabled": False}

        aes_session = None
        if enable_aes:
            aes_session = await issue_temporary_aes_key.ainvoke({
                "document_id": document_id,
                "user_id": user_id,
                "ttl_seconds": 300
            })

        return {
            "decision": decision,
            "reasoning": f"Fast deterministic policy evaluated (trust_score={trust_score}, risk={risk_level})",
            "watermark": watermark_payload,
            "anti_exfiltration": {
                "block_print": block_print,
                "block_copy": block_copy,
                "block_screenshot": block_screenshot
            },
            "aes_session": aes_session,
            "enable_aes_encryption": enable_aes,
            "hardware_binding_strict": strict_hw,
            "requires_ai_escalation": False
        }

drm_enforcement_engine = DRMEnforcementEngine()
