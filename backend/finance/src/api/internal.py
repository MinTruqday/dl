from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from src.core.dependency import verify_internal_token
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database


router = APIRouter(
    prefix="/tai-chinh/noi-bo",
    dependencies=[Depends(verify_internal_token)],
)


def _parse_date(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _purchase_filter(req: dict, document_ids: list[str] | None = None) -> dict:
    query = {"status": {"$in": ["ACTIVE", "purchased"]}}
    if document_ids is not None:
        query["$or"] = [
            {"document_id": {"$in": document_ids}},
            {"item_id": {"$in": document_ids}},
        ]
    from_date = _parse_date(req.get("from_date"))
    to_date = _parse_date(req.get("to_date"))
    if from_date or to_date:
        purchased_at = {}
        if from_date:
            purchased_at["$gte"] = from_date
        if to_date:
            purchased_at["$lte"] = to_date
        query["purchased_at"] = purchased_at
    return query


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
    if action == "author_analytics":
        document_ids = [str(value) for value in req.get("document_ids", [])]
        query = _purchase_filter(req, document_ids)
        rows = await purchases.aggregate(
            [
                {"$match": query},
                {
                    "$group": {
                        "_id": {"$ifNull": ["$document_id", "$item_id"]},
                        "revenue": {"$sum": "$price"},
                        "purchases": {"$sum": 1},
                        "buyers": {"$addToSet": "$user_id"},
                        "last_purchased_at": {"$max": "$purchased_at"},
                    }
                },
            ]
        ).to_list(length=None)
        daily = await purchases.aggregate(
            [
                {"$match": query},
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$purchased_at",
                                "timezone": "UTC",
                            }
                        },
                        "revenue": {"$sum": "$price"},
                        "purchases": {"$sum": 1},
                    }
                },
                {"$sort": {"_id": 1}},
            ]
        ).to_list(length=None)
        author_totals = await purchases.aggregate(
            [
                {"$match": query},
                {
                    "$group": {
                        "_id": None,
                        "revenue": {"$sum": "$price"},
                        "purchases": {"$sum": 1},
                        "buyers": {"$addToSet": "$user_id"},
                    }
                },
            ]
        ).to_list(length=1)
        wallet = await database.mongodb[settings.FINANCE_DB_NAME].wallets.find_one(
            {"_id": user_id}, {"balance": 1}
        )
        totals = author_totals[0] if author_totals else {}
        return {
            "data": {
                "documents": [
                    {
                        "document_id": str(row.get("_id", "")),
                        "revenue": int(row.get("revenue", 0)),
                        "purchases": int(row.get("purchases", 0)),
                        "unique_buyers": len([value for value in row.get("buyers", []) if value]),
                        "last_purchased_at": row.get("last_purchased_at"),
                    }
                    for row in rows
                ],
                "daily": [
                    {
                        "date": row.get("_id"),
                        "revenue": int(row.get("revenue", 0)),
                        "purchases": int(row.get("purchases", 0)),
                    }
                    for row in daily
                ],
                "total_revenue": int(totals.get("revenue", 0)),
                "total_purchases": int(totals.get("purchases", 0)),
                "unique_buyers": len([value for value in totals.get("buyers", []) if value]),
                "available_balance": int(wallet.get("balance", 0)) if wallet else 0,
            }
        }
    if action == "system_analytics":
        query = _purchase_filter(req)
        totals = await purchases.aggregate(
            [
                {"$match": query},
                {
                    "$group": {
                        "_id": None,
                        "revenue": {"$sum": "$price"},
                        "purchases": {"$sum": 1},
                    }
                },
            ]
        ).to_list(length=1)
        top_authors = await purchases.aggregate(
            [
                {"$match": query},
                {
                    "$group": {
                        "_id": "$seller_id",
                        "revenue": {"$sum": "$price"},
                        "purchases": {"$sum": 1},
                    }
                },
                {"$sort": {"revenue": -1}},
                {"$limit": 10},
            ]
        ).to_list(length=10)
        top_documents = await purchases.aggregate(
            [
                {"$match": query},
                {
                    "$group": {
                        "_id": {"$ifNull": ["$document_id", "$item_id"]},
                        "revenue": {"$sum": "$price"},
                        "purchases": {"$sum": 1},
                    }
                },
                {"$sort": {"revenue": -1}},
                {"$limit": 10},
            ]
        ).to_list(length=10)
        total = totals[0] if totals else {}
        return {
            "data": {
                "total_revenue": int(total.get("revenue", 0)),
                "total_purchases": int(total.get("purchases", 0)),
                "top_authors": [
                    {
                        "author_id": str(row.get("_id") or ""),
                        "revenue": int(row.get("revenue", 0)),
                        "purchases": int(row.get("purchases", 0)),
                    }
                    for row in top_authors
                ],
                "top_documents": [
                    {
                        "document_id": str(row.get("_id") or ""),
                        "revenue": int(row.get("revenue", 0)),
                        "purchases": int(row.get("purchases", 0)),
                    }
                    for row in top_documents
                ],
            }
        }
    raise HTTPException(status_code=422, detail="Tác vụ giao dịch nội bộ không hợp lệ")
