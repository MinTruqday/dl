import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from src.core.logic_logger import log_logic_execution
from src.services import content_client, finance_client
from src.services.humanity_client import HumanityClient


class AnalyticsService:
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
        documents = await content_client.analytics_documents(creator_id=user_id)
        document_ids = [str(doc["_id"]) for doc in documents]
        finance = await finance_client.author_analytics(
            user_id, document_ids, from_date, to_date
        )
        total_views = sum(int(doc.get("views", doc.get("view_count", 0))) for doc in documents)
        conversion_rate = (
            round((finance.get("total_purchases", 0) / total_views) * 100, 2)
            if total_views > 0
            else 0.0
        )
        profile = await HumanityClient.get(user_id)

        return {
            "total_revenue": int(finance.get("total_revenue", 0)),
            "total_views": total_views,
            "total_purchases": int(finance.get("total_purchases", 0)),
            "conversion_rate": conversion_rate,
            "unique_buyers": int(finance.get("unique_buyers", 0)),
            "total_documents": len(documents),
            "available_balance": int(finance.get("available_balance", 0)),
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
        documents = await content_client.analytics_documents(creator_id=user_id)
        document_ids = [str(doc["_id"]) for doc in documents]

        start_dt = AnalyticsService._parse_date(from_date)
        end_dt = AnalyticsService._parse_date(to_date)
        now = datetime.now(timezone.utc)

        if not start_dt:
            start_dt = now - timedelta(days=days)
        if not end_dt:
            end_dt = now

        finance = await finance_client.author_analytics(
            user_id,
            document_ids,
            start_dt.isoformat(),
            end_dt.isoformat(),
        )

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

        for row in finance.get("daily", []):
            key = str(row.get("date", ""))
            if key in buckets:
                buckets[key]["revenue"] = int(row.get("revenue", 0))
                buckets[key]["purchases"] = int(row.get("purchases", 0))

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
        documents = await content_client.analytics_documents(
            creator_id=user_id,
            search=search.strip() if search else None,
        )
        document_ids = [str(doc["_id"]) for doc in documents]
        finance = await finance_client.author_analytics(
            user_id, document_ids, from_date, to_date
        )
        revenue_rows = finance.get("documents", [])
        revenue_map = {row["document_id"]: row for row in revenue_rows}
        total_author_revenue = int(finance.get("total_revenue", 0))

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
            last_purchase_str = (
                last_purchase.isoformat()
                if isinstance(last_purchase, datetime)
                else last_purchase
            )

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
        finance = await finance_client.system_analytics(from_date, to_date)
        user_stats = await HumanityClient.stats()
        all_docs = await content_client.analytics_documents()
        total_documents = len(all_docs)
        total_platform_views = sum(int(doc.get("views", doc.get("view_count", 0))) for doc in all_docs)
        top_authors_raw = finance.get("top_authors", [])
        author_ids = [row.get("author_id") for row in top_authors_raw if row.get("author_id")]
        profiles = await HumanityClient.get_many(author_ids) if author_ids else []
        profile_map = {str(profile.get("_id")): profile for profile in profiles}
        top_authors = []
        for a in top_authors_raw:
            seller_id = a.get("author_id")
            user_doc = profile_map.get(str(seller_id))
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

        document_map = {str(doc.get("_id")): doc for doc in all_docs}
        top_docs_raw = finance.get("top_documents", [])
        top_documents = []
        for d in top_docs_raw:
            doc_id = d.get("document_id")
            doc_info = document_map.get(str(doc_id))
            top_documents.append(
                {
                    "document_id": doc_id,
                    "title": doc_info.get("title") if doc_info else "Tài liệu hệ thống",
                    "revenue": int(d.get("revenue", 0)),
                    "purchases": int(d.get("purchases", 0)),
                }
            )

        return {
            "total_revenue": int(finance.get("total_revenue", 0)),
            "total_purchases": int(finance.get("total_purchases", 0)),
            "total_views": total_platform_views,
            "total_documents": total_documents,
            "total_users": int(user_stats.get("total_users", 0)),
            "total_authors": int(user_stats.get("total_authors", 0)),
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
