from src.repositories.tier import TierRepository
from src.schemas.tier import UpdateTierRequest, UsageTierResponse

class TierService:
    @staticmethod
    async def get_user_tier(user_id: str) -> UsageTierResponse:
        sub = await TierRepository.get_user_tier(user_id)
        if not sub:
            return UsageTierResponse(user_id=user_id, ai_tier="BASIC", is_premium=False)
        return UsageTierResponse(
            user_id=user_id,
            ai_tier=sub.get("ai_tier", "BASIC"),
            is_premium=sub.get("is_premium", False)
        )

    @staticmethod
    async def update_user_tier(user_id: str, req: UpdateTierRequest) -> UsageTierResponse:
        await TierRepository.create_or_update_tier(user_id, req.ai_tier.value, req.is_premium)
        return UsageTierResponse(
            user_id=user_id,
            ai_tier=req.ai_tier,
            is_premium=req.is_premium
        )
