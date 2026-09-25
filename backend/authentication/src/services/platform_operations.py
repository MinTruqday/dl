import asyncio
import csv
import io
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException

from src.clients.service_gateway import health_request, internal_request
from src.core.dependency import CurrentUser
from src.core.policies import platform_policy
from src.repositories.platform import PlatformRepository
from src.schemas.platform import ActionReason, SmtpTestRequest
from src.services.email import EmailService
from src.services.platform import record_audit

OPERATIONS_POLICY = platform_policy()["operations"]


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
            OPERATIONS_POLICY["audit_actions"]["jobs_viewed"],
            "platform",
            "operations",
        )
        return jobs

    @staticmethod
    async def retry_job(job_id: str, current_user: CurrentUser):
        return await PlatformOperationsService._job_action(
            job_id,
            OPERATIONS_POLICY["job_actions"]["retry"],
            current_user,
            OPERATIONS_POLICY["audit_actions"]["job_retried"],
            "operations retry",
            "Tác vụ không tồn tại hoặc không đủ điều kiện chạy lại",
            "Không thể chạy lại tác vụ nền",
        )

    @staticmethod
    async def cancel_job(job_id: str, current_user: CurrentUser):
        return await PlatformOperationsService._job_action(
            job_id,
            OPERATIONS_POLICY["job_actions"]["cancel"],
            current_user,
            OPERATIONS_POLICY["audit_actions"]["job_canceled"],
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
                    "status": OPERATIONS_POLICY["background_job_failed_status"],
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
            OPERATIONS_POLICY["audit_actions"]["dead_letter_discarded"],
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
                OPERATIONS_POLICY["audit_actions"]["smtp_test_failed"],
                str(payload.recipient),
                payload.reason,
            )
            raise HTTPException(status_code=503, detail="Không thể gửi thư kiểm tra") from error
        await record_audit(
            current_user,
            OPERATIONS_POLICY["audit_actions"]["smtp_tested"],
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
                "status": OPERATIONS_POLICY["unavailable_status"],
                "checks": {"consumers": OPERATIONS_POLICY["unavailable_status"]},
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
            OPERATIONS_POLICY["audit_actions"]["dead_letter_requeued"],
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
        services = OPERATIONS_POLICY["platform_health_services"]
        results = await asyncio.gather(
            *(PlatformOperationsService.service_health(name) for name in services)
        )
        results.append(await PlatformOperationsService._mongodb_health())
        await record_audit(
            current_user,
            OPERATIONS_POLICY["audit_actions"]["platform_health_viewed"],
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
            OPERATIONS_POLICY["audit_actions"]["storage_tested"],
            "storage",
            "connectivity test",
            {"healthy": result["healthy"]},
        )
        if not result["healthy"]:
            raise HTTPException(status_code=503, detail="Kho lưu trữ chưa sẵn sàng")
        return result

    @staticmethod
    async def integration_health():
        targets = OPERATIONS_POLICY["integration_health_services"]
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
            {}, OPERATIONS_POLICY["audit_export_maximum_records"]
        )
        stream = io.StringIO()
        fields = OPERATIONS_POLICY["audit_export_fields"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for event in events:
            writer.writerow({field: event.get(field) for field in fields})
        await record_audit(
            current_user,
            OPERATIONS_POLICY["audit_actions"]["global_audit_exported"],
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
                "details": {"status": OPERATIONS_POLICY["unavailable_status"]},
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
                "service": OPERATIONS_POLICY["mongodb_service"],
                "healthy": True,
                "details": {"status": OPERATIONS_POLICY["ready_status"]},
            }
            if include_status_code:
                result["status_code"] = 200
            return result
        except Exception:
            result = {
                "service": OPERATIONS_POLICY["mongodb_service"],
                "healthy": False,
                "details": {"status": OPERATIONS_POLICY["unavailable_status"]},
            }
            if include_status_code:
                result["status_code"] = None
            return result
