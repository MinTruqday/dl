from src.core.database import database


class AnnaSource:
    @staticmethod
    async def probe_list_source() -> dict:
        return {
            "source": "AnnaArchive",
            "reachable": False,
            "http_status": None,
            "documents_detected": 0,
            "reason": "Nguồn không được hỗ trợ vì không có luồng tải PDF công khai được xác thực",
        }

    @staticmethod
    async def run_list_collector(
        search_query: str = "",
        pages: int = 1,
        job_id: str | None = None,
        max_documents: int = 1,
    ):
        raise PermissionError(
            "Anna Archive không có luồng thu thập PDF công khai được DocLib hỗ trợ"
        )

    @staticmethod
    async def run_detail_collector(
        document_url: str,
        job_id: str | None = None,
        collection_scope: dict | None = None,
    ):
        raise PermissionError(
            "Anna Archive không có luồng thu thập PDF công khai được DocLib hỗ trợ"
        )

    @staticmethod
    async def run_download_processor(payload: dict):
        raise PermissionError(
            "Anna Archive không có luồng thu thập PDF công khai được DocLib hỗ trợ"
        )
