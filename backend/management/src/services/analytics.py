import csv
import io
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.infrastructure.mongo import mongo
from src.core.logic_logger import log_logic_execution


class AnalyticsService:

    @staticmethod
    def _get_client() -> AsyncIOMotorClient:
        if database.mongodb is not None:
            return database.mongodb
        return mongo.client

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            cleaned = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None

    @staticmethod
    @log_logic_execution
    async def get_author_overview(
        user_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = AnalyticsService._get_client()
        content_db = client[settings.CONTENT_DB_NAME]
        finance_db = client[settings.FINANCE_DB_NAME]
        humanity_db = client[settings.HUMANITY_DB_NAME]

        documents = await content_db.documents.find(
            {"creator_id": user_id, "status": "published"}
        ).to_list(length=None)
        document_ids = [str(doc["_id"]) for doc in documents]

        purchase_filter: Dict[str, Any] = {
            "document_id": {"$in": document_ids},
            "status": "ACTIVE",
        }
        start_dt = AnalyticsService._parse_date(from_date)
        end_dt = AnalyticsService._parse_date(to_date)
        if start_dt or end_dt:
            time_filter: Dict[str, Any] = {}
            if start_dt:
                time_filter["$gte"] = start_dt
            if end_dt:
                time_filter["$lte"] = end_dt
            purchase_filter["purchased_at"] = time_filter

        purchases = await finance_db.purchases.find(purchase_filter).to_list(length=None)
        total_revenue = sum(int(p.get("price", 0)) for p in purchases)
        total_purchases = len(purchases)
        total_views = sum(int(doc.get("views", doc.get("view_count", 0))) for doc in documents)
        conversion_rate = (
            round((total_purchases / total_views) * 100, 2) if total_views > 0 else 0.0
        )
        unique_buyers = len({str(p.get("user_id")) for p in purchases if p.get("user_id")})

        wallet = await finance_db.wallets.find_one({"_id": user_id})
        profile = await humanity_db.users.find_one({"_id": user_id})

        return {
            "total_revenue": total_revenue,
            "total_views": total_views,
            "total_purchases": total_purchases,
            "conversion_rate": conversion_rate,
            "unique_buyers": unique_buyers,
            "total_documents": len(documents),
            "available_balance": int(wallet.get("balance", 0)) if wallet else 0,
            "reward_points": int(profile.get("reward_points", 0)) if profile else 0,
        }

    @staticmethod
    @log_logic_execution
    async def get_author_timeseries(
        user_id: str,
        days: int = 30,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        client = AnalyticsService._get_client()
        content_db = client[settings.CONTENT_DB_NAME]
        finance_db = client[settings.FINANCE_DB_NAME]

        documents = await content_db.documents.find(
            {"creator_id": user_id, "status": "published"}
        ).to_list(length=None)
        document_ids = [str(doc["_id"]) for doc in documents]

        start_dt = AnalyticsService._parse_date(from_date)
        end_dt = AnalyticsService._parse_date(to_date)
        now = datetime.now(timezone.utc)

        if not start_dt:
            start_dt = now - timedelta(days=days)
        if not end_dt:
            end_dt = now

        purchases = await finance_db.purchases.find(
            {
                "document_id": {"$in": document_ids},
                "status": "ACTIVE",
                "purchased_at": {"$gte": start_dt, "$lte": end_dt},
            }
        ).to_list(length=None)

        buckets: Dict[str, Dict[str, Any]] = {}
        curr = start_dt
        while curr <= end_dt:
            date_key = curr.strftime("%Y-%m-%d")
            buckets[date_key] = {
                "date": date_key,
                "revenue": 0,
                "purchases": 0,
            }
            curr += timedelta(days=1)

        for p in purchases:
            p_date = p.get("purchased_at")
            if isinstance(p_date, datetime):
                key = p_date.strftime("%Y-%m-%d")
                if key in buckets:
                    buckets[key]["revenue"] += int(p.get("price", 0))
                    buckets[key]["purchases"] += 1

        return list(buckets.values())

    @staticmethod
    @log_logic_execution
    async def get_author_documents_analytics(
        user_id: str,
        search: Optional[str] = None,
        sort_by: str = "revenue",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = AnalyticsService._get_client()
        content_db = client[settings.CONTENT_DB_NAME]
        finance_db = client[settings.FINANCE_DB_NAME]

        query: Dict[str, Any] = {"creator_id": user_id, "status": "published"}
        if search and search.strip():
            query["title"] = {"$regex": search.strip(), "$options": "i"}

        documents = await content_db.documents.find(query).to_list(length=None)
        document_ids = [str(doc["_id"]) for doc in documents]

        purchase_filter: Dict[str, Any] = {
            "document_id": {"$in": document_ids},
            "status": "ACTIVE",
        }
        start_dt = AnalyticsService._parse_date(from_date)
        end_dt = AnalyticsService._parse_date(to_date)
        if start_dt or end_dt:
            time_filter: Dict[str, Any] = {}
            if start_dt:
                time_filter["$gte"] = start_dt
            if end_dt:
                time_filter["$lte"] = end_dt
            purchase_filter["purchased_at"] = time_filter

        pipeline = [
            {"$match": purchase_filter},
            {
                "$group": {
                    "_id": "$document_id",
                    "revenue": {"$sum": "$price"},
                    "purchases": {"$sum": 1},
                    "last_purchased_at": {"$max": "$purchased_at"},
                }
            },
        ]
        revenue_rows = await finance_db.purchases.aggregate(pipeline).to_list(length=None)
        revenue_map = {row["_id"]: row for row in revenue_rows}

        total_author_revenue = sum(row.get("revenue", 0) for row in revenue_rows)

        items = []
        for doc in documents:
            doc_id = str(doc["_id"])
            rev_info = revenue_map.get(doc_id, {})
            revenue = int(rev_info.get("revenue", 0))
            purchases = int(rev_info.get("purchases", 0))
            views = int(doc.get("views", doc.get("view_count", 0)))
            cr = round((purchases / views) * 100, 2) if views > 0 else 0.0
            share = (
                round((revenue / total_author_revenue) * 100, 2)
                if total_author_revenue > 0
                else 0.0
            )

            last_purchase = rev_info.get("last_purchased_at")
            if isinstance(last_purchase, datetime):
                last_purchase_str = last_purchase.isoformat()
            else:
                last_purchase_str = None

            items.append(
                {
                    "id": doc_id,
                    "slug": doc.get("slug", doc_id),
                    "title": doc.get("title", "Tài liệu chưa đặt tên"),
                    "views": views,
                    "price": int(doc.get("price_dl", doc.get("price_dls", 0)) or 0),
                    "purchases": purchases,
                    "revenue": revenue,
                    "conversion_rate": cr,
                    "revenue_percentage": share,
                    "is_drm": bool(doc.get("is_drm_protected", True)),
                    "last_purchased_at": last_purchase_str,
                    "created_at": (
                        doc.get("created_at").isoformat()
                        if isinstance(doc.get("created_at"), datetime)
                        else None
                    ),
                }
            )

        reverse = sort_order.lower() != "asc"
        if sort_by == "views":
            items.sort(key=lambda x: x["views"], reverse=reverse)
        elif sort_by == "purchases":
            items.sort(key=lambda x: x["purchases"], reverse=reverse)
        elif sort_by == "conversion_rate":
            items.sort(key=lambda x: x["conversion_rate"], reverse=reverse)
        elif sort_by == "title":
            items.sort(key=lambda x: x["title"].lower(), reverse=reverse)
        else:
            items.sort(key=lambda x: x["revenue"], reverse=reverse)

        total = len(items)
        total_pages = max(1, (total + page_size - 1) // page_size)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_items = items[start_idx:end_idx]

        return {
            "items": paged_items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    @staticmethod
    @log_logic_execution
    async def get_system_analytics(
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = AnalyticsService._get_client()
        content_db = client[settings.CONTENT_DB_NAME]
        finance_db = client[settings.FINANCE_DB_NAME]
        humanity_db = client[settings.HUMANITY_DB_NAME]

        purchase_filter: Dict[str, Any] = {"status": "ACTIVE"}
        start_dt = AnalyticsService._parse_date(from_date)
        end_dt = AnalyticsService._parse_date(to_date)
        if start_dt or end_dt:
            time_filter: Dict[str, Any] = {}
            if start_dt:
                time_filter["$gte"] = start_dt
            if end_dt:
                time_filter["$lte"] = end_dt
            purchase_filter["purchased_at"] = time_filter

        purchases = await finance_db.purchases.find(purchase_filter).to_list(length=None)
        total_platform_revenue = sum(int(p.get("price", 0)) for p in purchases)
        total_platform_purchases = len(purchases)

        total_users = await humanity_db.users.count_documents({})
        total_authors = await humanity_db.users.count_documents({"role": {"$in": ["author", "admin"]}})
        total_documents = await content_db.documents.count_documents({"status": "published"})

        all_docs = await content_db.documents.find({"status": "published"}).to_list(length=None)
        total_platform_views = sum(int(doc.get("views", doc.get("view_count", 0))) for doc in all_docs)

        author_revenue_pipeline = [
            {"$match": purchase_filter},
            {"$group": {"_id": "$seller_id", "revenue": {"$sum": "$price"}, "purchases": {"$sum": 1}}},
            {"$sort": {"revenue": -1}},
            {"$limit": 10},
        ]
        top_authors_raw = await finance_db.purchases.aggregate(author_revenue_pipeline).to_list(length=None)
        top_authors = []
        for a in top_authors_raw:
            seller_id = a.get("_id")
            user_doc = (
                await humanity_db.users.find_one({"_id": seller_id}) if seller_id else None
            )
            top_authors.append(
                {
                    "author_id": seller_id,
                    "author_name": (
                        user_doc.get("full_name") or user_doc.get("email") or "Tác giả"
                        if user_doc
                        else "Chưa xác định"
                    ),
                    "revenue": int(a.get("revenue", 0)),
                    "purchases": int(a.get("purchases", 0)),
                }
            )

        doc_revenue_pipeline = [
            {"$match": purchase_filter},
            {"$group": {"_id": "$document_id", "revenue": {"$sum": "$price"}, "purchases": {"$sum": 1}}},
            {"$sort": {"revenue": -1}},
            {"$limit": 10},
        ]
        top_docs_raw = await finance_db.purchases.aggregate(doc_revenue_pipeline).to_list(length=None)
        top_documents = []
        for d in top_docs_raw:
            doc_id = d.get("_id")
            doc_info = await content_db.documents.find_one({"_id": doc_id}) if doc_id else None
            top_documents.append(
                {
                    "document_id": doc_id,
                    "title": doc_info.get("title") if doc_info else "Tài liệu hệ thống",
                    "revenue": int(d.get("revenue", 0)),
                    "purchases": int(d.get("purchases", 0)),
                }
            )

        return {
            "total_revenue": total_platform_revenue,
            "total_purchases": total_platform_purchases,
            "total_views": total_platform_views,
            "total_documents": total_documents,
            "total_users": total_users,
            "total_authors": total_authors,
            "top_authors": top_authors,
            "top_documents": top_documents,
        }

    @staticmethod
    @log_logic_execution
    async def export_analytics(
        user_id: str,
        is_admin: bool = False,
        format_type: str = "json",
        scope: str = "author",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        if scope == "system" and is_admin:
            data = await AnalyticsService.get_system_analytics(from_date, to_date)
            filename = f"phan_tich_he_thong_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        else:
            docs_data = await AnalyticsService.get_author_documents_analytics(
                user_id=user_id,
                page=1,
                page_size=1000,
                from_date=from_date,
                to_date=to_date,
            )
            overview_data = await AnalyticsService.get_author_overview(
                user_id=user_id,
                from_date=from_date,
                to_date=to_date,
            )
            data = {
                "overview": overview_data,
                "documents": docs_data["items"],
            }
            filename = f"phan_tich_tac_gia_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        if format_type.lower() == "csv":
            output = io.StringIO()
            if scope == "system" and is_admin:
                writer = csv.writer(output)
                writer.writerow(["chi_so", "gia_tri"])
                writer.writerow(["tong_doanh_thu", data.get("total_revenue", 0)])
                writer.writerow(["tong_luot_mua", data.get("total_purchases", 0)])
                writer.writerow(["tong_luot_xem", data.get("total_views", 0)])
                writer.writerow(["tong_tai_lieu", data.get("total_documents", 0)])
                writer.writerow(["tong_nguoi_dung", data.get("total_users", 0)])
                writer.writerow(["tong_tac_gia", data.get("total_authors", 0)])
            else:
                writer = csv.writer(output)
                writer.writerow(
                    [
                        "ma_tai_lieu",
                        "tieu_de",
                        "gia_ban",
                        "luot_xem",
                        "luot_mua",
                        "doanh_thu",
                        "ty_le_chuyen_doi",
                        "ty_le_dong_gop",
                    ]
                )
                for item in data.get("documents", []):
                    writer.writerow(
                        [
                            item["id"],
                            item["title"],
                            item["price"],
                            item["views"],
                            item["purchases"],
                            item["revenue"],
                            item["conversion_rate"],
                            item["revenue_percentage"],
                        ]
                    )
            return {
                "filename": f"{filename}.csv",
                "format": "csv",
                "content": output.getvalue(),
            }

        return {
            "filename": f"{filename}.json",
            "format": "json",
            "content": data,
        }
