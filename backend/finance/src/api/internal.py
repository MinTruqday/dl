from fastapi import APIRouter, Depends, HTTPException

from src.core.dependency import verify_internal_token
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database


router = APIRouter(
    prefix="/tai-chinh/noi-bo",
    dependencies=[Depends(verify_internal_token)],
)


@router.post("/mua-hang", include_in_schema=False)
async def exchange_purchase(req: dict):
    action = str(req.get("action", ""))
    user_id = str(req.get("user_id", ""))
    document_id = str(req.get("document_id", ""))
    purchases = database.mongodb[settings.FINANCE_DB_NAME].purchases
    active_query = {
        "user_id": user_id,
        "$or": [{"document_id": document_id}, {"item_id": document_id}],
        "status": {"$in": ["ACTIVE", "purchased"]},
    }
    if action == "has_purchase":
        row = await purchases.find_one(active_query, {"_id": 1})
        return {"data": {"purchased": bool(row)}}
    if action == "get_purchase":
        row = await purchases.find_one(active_query)
        if not row:
            raise HTTPException(status_code=404, detail="Không tìm thấy giao dịch mua")
        row["_id"] = str(row["_id"])
        return {"data": row}
    if action == "purchase_count":
        count = await purchases.count_documents(
            {
                "$or": [{"document_id": document_id}, {"item_id": document_id}],
                "status": {"$in": ["ACTIVE", "purchased"]},
            }
        )
        return {"data": {"count": count}}
    raise HTTPException(status_code=422, detail="Tác vụ giao dịch nội bộ không hợp lệ")
