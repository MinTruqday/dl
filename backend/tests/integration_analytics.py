import asyncio
import os
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from src.services.analytics import AnalyticsService


async def run_integration_tests():
    client = AsyncIOMotorClient(os.environ["MONGODB_URI"])

    content_db = client[os.getenv("CONTENT_DB_NAME", "doclib_content")]
    finance_db = client[os.getenv("FINANCE_DB_NAME", "doclib_finance")]
    humanity_db = client[os.getenv("HUMANITY_DB_NAME", "doclib_humanity")]

    author_id = "test_analytics_author_01"
    reader_1 = "test_analytics_reader_01"
    reader_2 = "test_analytics_reader_02"
    admin_id = "test_analytics_admin_01"

    doc_id_1 = "test_doc_analytics_01"
    doc_id_2 = "test_doc_analytics_02"

    now = datetime.now(timezone.utc)

    await humanity_db.users.delete_many({"_id": {"$in": [author_id, reader_1, reader_2, admin_id]}})
    await content_db.documents.delete_many({"_id": {"$in": [doc_id_1, doc_id_2]}})
    await finance_db.purchases.delete_many({"document_id": {"$in": [doc_id_1, doc_id_2]}})
    await finance_db.wallets.delete_many({"_id": {"$in": [author_id, reader_1, reader_2, admin_id]}})

    await humanity_db.users.insert_many([
        {"_id": author_id, "email": "author@test.vn", "full_name": "Tác Giả Mẫu", "role": "author", "reward_points": 500},
        {"_id": reader_1, "email": "reader1@test.vn", "full_name": "Độc Giả 1", "role": "reader"},
        {"_id": reader_2, "email": "reader2@test.vn", "full_name": "Độc Giả 2", "role": "reader"},
        {"_id": admin_id, "email": "admin@test.vn", "full_name": "Quản Trị Viên", "role": "admin"},
    ])

    await content_db.documents.insert_many([
        {
            "_id": doc_id_1,
            "creator_id": author_id,
            "title": "Tài liệu học máy nâng cao",
            "slug": "tai-lieu-hoc-may-nang-cao",
            "status": "published",
            "price_dl": 100,
            "views": 50,
            "is_drm_protected": True,
            "created_at": now - timedelta(days=5),
        },
        {
            "_id": doc_id_2,
            "creator_id": author_id,
            "title": "Kỹ thuật lập trình hệ thống phân tán",
            "slug": "ky-thuat-lap-trinh-he-thong-phan-tan",
            "status": "published",
            "price_dl": 250,
            "views": 100,
            "is_drm_protected": True,
            "created_at": now - timedelta(days=2),
        },
    ])

    await finance_db.purchases.insert_many([
        {
            "_id": "p_01",
            "document_id": doc_id_1,
            "user_id": reader_1,
            "seller_id": author_id,
            "price": 100,
            "status": "ACTIVE",
            "purchased_at": now - timedelta(days=2),
        },
        {
            "_id": "p_02",
            "document_id": doc_id_2,
            "user_id": reader_1,
            "seller_id": author_id,
            "price": 250,
            "status": "ACTIVE",
            "purchased_at": now - timedelta(days=1),
        },
        {
            "_id": "p_03",
            "document_id": doc_id_2,
            "user_id": reader_2,
            "seller_id": author_id,
            "price": 250,
            "status": "ACTIVE",
            "purchased_at": now,
        },
    ])

    await finance_db.wallets.insert_one({"_id": author_id, "balance": 600})

    overview = await AnalyticsService.get_author_overview(author_id)
    assert overview["total_revenue"] == 600, f"Expected 600 revenue, got {overview['total_revenue']}"
    assert overview["total_purchases"] == 3, f"Expected 3 purchases, got {overview['total_purchases']}"
    assert overview["total_views"] == 150, f"Expected 150 views, got {overview['total_views']}"
    assert overview["unique_buyers"] == 2, f"Expected 2 unique buyers, got {overview['unique_buyers']}"
    assert overview["available_balance"] == 600, f"Expected 600 balance, got {overview['available_balance']}"
    assert overview["reward_points"] == 500, f"Expected 500 points, got {overview['reward_points']}"

    timeseries = await AnalyticsService.get_author_timeseries(author_id, days=7)
    assert len(timeseries) >= 7, f"Expected >= 7 points, got {len(timeseries)}"
    total_ts_revenue = sum(t["revenue"] for t in timeseries)
    assert total_ts_revenue == 600, f"Expected 600 ts revenue, got {total_ts_revenue}"

    docs_analytics = await AnalyticsService.get_author_documents_analytics(
        user_id=author_id,
        search="học máy",
        sort_by="revenue",
    )
    assert docs_analytics["total"] == 1, f"Expected 1 matched doc, got {docs_analytics['total']}"
    assert docs_analytics["items"][0]["revenue"] == 100

    docs_all = await AnalyticsService.get_author_documents_analytics(
        user_id=author_id,
        sort_by="revenue",
    )
    assert docs_all["total"] == 2
    assert docs_all["items"][0]["revenue"] == 500
    assert docs_all["items"][1]["revenue"] == 100

    sys_analytics = await AnalyticsService.get_system_analytics()
    assert sys_analytics["total_revenue"] >= 600
    assert sys_analytics["total_purchases"] >= 3
    assert len(sys_analytics["top_authors"]) >= 1
    assert len(sys_analytics["top_documents"]) >= 2

    export_csv = await AnalyticsService.export_analytics(author_id, is_admin=False, format_type="csv")
    assert export_csv["format"] == "csv"
    assert "ma_tai_lieu" in export_csv["content"]
    assert "Tài liệu học máy" in export_csv["content"]

    export_json = await AnalyticsService.export_analytics(author_id, is_admin=False, format_type="json")
    assert export_json["format"] == "json"
    assert export_json["content"]["overview"]["total_revenue"] == 600

    export_sys_csv = await AnalyticsService.export_analytics(admin_id, is_admin=True, scope="system", format_type="csv")
    assert export_sys_csv["format"] == "csv"
    assert "tong_doanh_thu" in export_sys_csv["content"]

    await humanity_db.users.delete_many({"_id": {"$in": [author_id, reader_1, reader_2, admin_id]}})
    await content_db.documents.delete_many({"_id": {"$in": [doc_id_1, doc_id_2]}})
    await finance_db.purchases.delete_many({"document_id": {"$in": [doc_id_1, doc_id_2]}})
    await finance_db.wallets.delete_many({"_id": {"$in": [author_id, reader_1, reader_2, admin_id]}})
    client.close()

    print("TAT CA CAC KIEM THU TICH HOP PHAN TICH DA HOAN TAT THANH CONG")


if __name__ == "__main__":
    asyncio.run(run_integration_tests())
