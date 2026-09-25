from src.core.infrastructure.configuration import settings
from src.repositories.storage import storage_repository
from src.services.storage_policy import storage_policy


async def get_storage_quota(owner_id: str) -> dict:
    pipeline = [
        {"$match": {"owner_id": owner_id, "is_folder": False, "is_shortcut": False}},
        {
            "$project": {
                "assets": {
                    "$concatArrays": [
                        {
                            "$cond": [
                                {"$eq": [{"$type": "$url"}, "string"]},
                                [{"url": "$url", "size": "$size"}],
                                [],
                            ]
                        },
                        {
                            "$map": {
                                "input": {"$ifNull": ["$versions", []]},
                                "as": "version",
                                "in": {"url": "$$version.url", "size": "$$version.size"},
                            }
                        },
                    ]
                }
            }
        },
        {"$unwind": "$assets"},
        {"$group": {"_id": "$assets.url", "size": {"$max": "$assets.size"}}},
        {"$group": {"_id": None, "total_used": {"$sum": "$size"}}},
    ]
    result = await storage_repository.aggregate(pipeline)
    used = (result[0].get("total_used") or 0) if result else 0
    return {"used": used, "limit": settings.DEFAULT_STORAGE_LIMIT_BYTES}


async def get_quota_analytics(owner_id: str) -> dict:
    quota = await get_storage_quota(owner_id)
    total_limit = quota["limit"]
    total_used = quota["used"]
    free_bytes = max(0, total_limit - total_used)
    usage_pct = round((total_used / total_limit * 100) if total_limit > 0 else 0.0, 2)
    configured_categories = storage_policy()["file_categories"]
    categories = {
        name: {"extensions": extensions, "count": 0, "size": 0}
        for name, extensions in configured_categories.items()
    }
    categories["others"] = {"extensions": [], "count": 0, "size": 0}
    files = await storage_repository.find_many(
        {"owner_id": owner_id, "is_folder": False, "is_trashed": False}
    )
    for file in files:
        name = (file.get("name") or "").lower()
        size = (file.get("size") or 0) + sum(
            version.get("size") or 0 for version in file.get("versions", [])
        )
        matched = False
        for category_name, category in categories.items():
            if category_name != "others" and any(
                name.endswith(extension) for extension in category["extensions"]
            ):
                category["count"] += 1
                category["size"] += size
                matched = True
                break
        if not matched:
            categories["others"]["count"] += 1
            categories["others"]["size"] += size
    breakdown = {
        name: {
            "count": category["count"],
            "size": category["size"],
            "percentage": round(
                (category["size"] / total_used * 100) if total_used > 0 else 0.0,
                2,
            ),
        }
        for name, category in categories.items()
    }
    total_folders = await storage_repository.count(
        {"owner_id": owner_id, "is_folder": True, "is_trashed": False}
    )
    trashed_files = await storage_repository.find_many(
        {"owner_id": owner_id, "is_trashed": True, "is_folder": False}
    )
    return {
        "total_quota_bytes": total_limit,
        "used_quota_bytes": total_used,
        "free_quota_bytes": free_bytes,
        "usage_percentage": usage_pct,
        "total_files_count": len(files),
        "total_folders_count": total_folders,
        "trashed_files_count": len(trashed_files),
        "trashed_bytes": sum((item.get("size") or 0) for item in trashed_files),
        "breakdown": breakdown,
    }
