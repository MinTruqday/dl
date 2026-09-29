import asyncio
import csv
import io
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException

from src.clients.service_gateway import health_request, internal_request
from src.core.dependency import CurrentUser
from src.repositories.platform import PlatformRepository
from src.schemas.platform import ActionReason, SmtpTestRequest
from src.services.email import EmailService
from src.services.platform import record_audit

class PlatformOperationsService:
    @staticmethod
    async def jobs(status: str, kind: str, limit: int, current_user: CurrentUser):
        try:
            response = await internal_request(
                "GET",
                "worker",
                "/xu-ly-nen/noi-bo/tac-vu",
                params={"status": status, "kind": kind, "limit": limit},
            )
            response.raise_for_status()
            jobs = response.json()["items"]
        except (httpx.HTTPError, KeyError, ValueError) as error:
            raise HTTPException(
                status_code=503, detail="Dịch vụ tác vụ nền chưa sẵn sàng"
            ) from error
        await record_audit(
            current_user,
            "ADMIN_OPERATIONS_JOBS_VIEWED",
            "platform",
            "operations",
        )
        return jobs

    @staticmethod
    async def retry_job(job_id: str, current_user: CurrentUser):
        return await PlatformOperationsService._job_action(
            job_id,
            "thu-lai",
            current_user,
            "ADMIN_OPERATIONS_JOB_RETRIED",
            "operations retry",
            "Tác vụ không tồn tại hoặc không đủ điều kiện chạy lại",
            "Không thể chạy lại tác vụ nền",
        )

    @staticmethod
    async def cancel_job(job_id: str, current_user: CurrentUser):
        return await PlatformOperationsService._job_action(
            job_id,
            "huy",
            current_user,
            "ADMIN_OPERATIONS_JOB_CANCELED",
            "operations cancel",
            "Tác vụ không tồn tại hoặc không thể hủy",
            "Không thể hủy tác vụ nền",
        )

    @staticmethod
    async def dead_letter_jobs(limit: int):
        try:
            response = await internal_request(
                "GET",
                "worker",
                "/xu-ly-nen/noi-bo/tac-vu",
                params={
                    "status": "failed",
                    "limit": limit,
                },
            )
            response.raise_for_status()
            return response.json()["items"]
        except (httpx.HTTPError, KeyError, ValueError) as error:
            raise HTTPException(
                status_code=503, detail="Dịch vụ tác vụ nền chưa sẵn sàng"
            ) from error

    @staticmethod
    async def discard_job(
        job_id: str, payload: ActionReason, current_user: CurrentUser
    ):
        try:
            response = await internal_request(
                "POST",
                "worker",
                f"/xu-ly-nen/noi-bo/tac-vu/{job_id}/loai-bo",
                payload={"actor_id": current_user.id, "reason": payload.reason},
            )
            response.raise_for_status()
            job = response.json()
        except httpx.HTTPStatusError as error:
            raise HTTPException(
                status_code=error.response.status_code,
                detail="Tác vụ không ở trạng thái lỗi",
            ) from error
        except (httpx.HTTPError, ValueError) as error:
            raise HTTPException(
                status_code=503, detail="Dịch vụ tác vụ nền chưa sẵn sàng"
            ) from error
        await record_audit(
            current_user,
            "ADMIN_DLQ_JOB_DISCARDED",
            job_id,
            payload.reason,
        )
        return job

    @staticmethod
    async def test_smtp(payload: SmtpTestRequest, current_user: CurrentUser):
        try:
            await EmailService.send_platform_test_email(str(payload.recipient))
        except Exception as error:
            await record_audit(
                current_user,
                "ADMIN_SMTP_TEST_FAILED",
                str(payload.recipient),
                payload.reason,
            )
            raise HTTPException(status_code=503, detail="Không thể gửi thư kiểm tra") from error
        await record_audit(
            current_user,
            "ADMIN_SMTP_TESTED",
            str(payload.recipient),
            payload.reason,
        )
        return {"recipient": payload.recipient, "delivered": True}

    @staticmethod
    async def queue_overview():
        try:
            overview_response = await internal_request(
                "GET", "worker", "/xu-ly-nen/noi-bo/tong-quan"
            )
            overview_response.raise_for_status()
            overview = overview_response.json()
            response = await health_request("worker")
            worker = response.json()
        except (httpx.HTTPError, KeyError, ValueError):
            overview = {"jobs_by_status": {}}
            worker = {
                "status": "unavailable",
                "checks": {"consumers": "unavailable"},
            }
        return {
            "jobs_by_status": overview["jobs_by_status"],
            "consumer_status": worker.get("checks", {}).get("consumers"),
            "worker_status": worker.get("status"),
        }

    @staticmethod
    async def requeue_dead_letter_job(
        job_id: str, payload: ActionReason, current_user: CurrentUser
    ):
        try:
            response = await internal_request(
                "POST", "worker", f"/xu-ly-nen/noi-bo/tac-vu/{job_id}/thu-lai"
            )
            response.raise_for_status()
            result = response.json()
        except httpx.HTTPStatusError as error:
            raise HTTPException(
                status_code=error.response.status_code,
                detail="Không thể đưa tác vụ lỗi trở lại hàng đợi",
            ) from error
        except httpx.HTTPError as error:
            raise HTTPException(
                status_code=503, detail="Dịch vụ tác vụ nền chưa sẵn sàng"
            ) from error
        await record_audit(
            current_user,
            "ADMIN_DLQ_JOB_REQUEUED",
            job_id,
            payload.reason,
        )
        return result

    @staticmethod
    async def rag_operations():
        response = await internal_request("GET", "testing", "/kiem-thu/noi-bo/quan-tri/rag")
        response.raise_for_status()
        return response.json()

    @staticmethod
    async def storage_usage():
        response = await internal_request(
            "GET", "testing", "/kiem-thu/noi-bo/quan-tri/dung-luong-luu-tru", timeout=60
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    async def platform_health(current_user: CurrentUser):
        services = ("authentication", "testing", "worker", "ai", "content")
        results = await asyncio.gather(
            *(PlatformOperationsService.service_health(name) for name in services)
        )
        results.append(await PlatformOperationsService._mongodb_health())
        await record_audit(
            current_user,
            "ADMIN_PLATFORM_HEALTH_VIEWED",
            "platform",
            "operations",
        )
        return {
            "healthy": all(item["healthy"] for item in results),
            "services": results,
            "checked_at": datetime.now(timezone.utc),
        }

    @staticmethod
    async def audit(action: str | None, limit: int):
        query = {"action": action} if action else {}
        events = await PlatformRepository.list_audit_logs(query, limit)
        return [{**event, "_id": str(event["_id"])} for event in events]

    @staticmethod
    async def test_storage(current_user: CurrentUser):
        result = await PlatformOperationsService.service_health("cloud")
        await record_audit(
            current_user,
            "ADMIN_STORAGE_TESTED",
            "storage",
            "connectivity test",
            {"healthy": result["healthy"]},
        )
        if not result["healthy"]:
            raise HTTPException(status_code=503, detail="Kho lưu trữ chưa sẵn sàng")
        return result

    @staticmethod
    async def integration_health():
        targets = ("worker", "ai", "cloud", "testing")
        services = await asyncio.gather(
            *(PlatformOperationsService.service_health(name) for name in targets)
        )
        services.append(await PlatformOperationsService._mongodb_health(include_status_code=True))
        return {
            "healthy": all(item["healthy"] for item in services),
            "services": services,
        }

    @staticmethod
    async def metrics():
        try:
            worker_response, testing_response = await asyncio.gather(
                internal_request("GET", "worker", "/xu-ly-nen/noi-bo/tong-quan"),
                internal_request("GET", "testing", "/kiem-thu/noi-bo/quan-tri/so-lieu"),
            )
            worker_response.raise_for_status()
            testing_response.raise_for_status()
            return {
                "jobs_by_status": worker_response.json()["jobs_by_status"],
                **testing_response.json(),
                "generated_at": datetime.now(timezone.utc),
            }
        except (httpx.HTTPError, KeyError, ValueError) as error:
            raise HTTPException(
                status_code=503, detail="Dịch vụ vận hành chưa sẵn sàng"
            ) from error

    @staticmethod
    async def export_audit(current_user: CurrentUser):
        events = await PlatformRepository.list_audit_logs(
            {}, 100000
        )
        stream = io.StringIO()
        fields = ("timestamp", "action", "actor_email", "target_user_id", "reason")
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for event in events:
            writer.writerow({field: event.get(field) for field in fields})
        await record_audit(
            current_user,
            "ADMIN_GLOBAL_AUDIT_EXPORTED",
            "platform",
            "audit export",
        )
        return stream.getvalue()

    @staticmethod
    async def service_health(name: str):
        try:
            response = await health_request(name)
            return {
                "service": name,
                "healthy": response.status_code < 400,
                "status_code": response.status_code,
                "details": response.json(),
            }
        except (httpx.HTTPError, ValueError):
            return {
                "service": name,
                "healthy": False,
                "status_code": None,
                "details": {"status": "unavailable"},
            }

    @staticmethod
    async def _job_action(
        job_id: str,
        action: str,
        current_user: CurrentUser,
        audit_action: str,
        audit_reason: str,
        conflict_message: str,
        failure_message: str,
    ):
        try:
            response = await internal_request(
                "POST", "worker", f"/xu-ly-nen/noi-bo/tac-vu/{job_id}/{action}"
            )
            response.raise_for_status()
            result = response.json()
        except httpx.HTTPStatusError as error:
            if error.response.status_code in {404, 409, 422}:
                raise HTTPException(
                    status_code=error.response.status_code, detail=conflict_message
                ) from error
            raise HTTPException(status_code=502, detail=failure_message) from error
        except httpx.HTTPError as error:
            raise HTTPException(
                status_code=503, detail="Dịch vụ tác vụ nền chưa sẵn sàng"
            ) from error
        await record_audit(current_user, audit_action, job_id, audit_reason)
        return result

    @staticmethod
    async def _mongodb_health(include_status_code: bool = False):
        try:
            await PlatformRepository.database_ready()
            result = {
                "service": "mongodb",
                "healthy": True,
                "details": {"status": "ready"},
            }
            if include_status_code:
                result["status_code"] = 200
            return result
        except Exception:
            result = {
                "service": "mongodb",
                "healthy": False,
                "details": {"status": "unavailable"},
            }
            if include_status_code:
                result["status_code"] = None
            return result
