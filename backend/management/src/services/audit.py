import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from typing import Any, Dict, List, Optional
from src.core.infrastructure.mongo import mongo

class AuditService:
    @staticmethod
    def _compute_hash(log: Dict[str, Any]) -> str:
        raw = f"{log.get('_id', '')}:{log.get('actor_id', '')}:{log.get('action', '')}:{log.get('target_id', '')}:{log.get('timestamp', '')}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _enrich_log(log: Dict[str, Any]) -> Dict[str, Any]:
        item = dict(log)
        item["_id"] = str(item.get("_id", ""))
        ts = item.get("timestamp") or item.get("created_at")
        if isinstance(ts, datetime):
            item["timestamp"] = ts.isoformat()
        elif ts is not None:
            item["timestamp"] = str(ts)
        else:
            item["timestamp"] = datetime.now(timezone.utc).isoformat()

        action = str(item.get("action", ""))
        if not item.get("module"):
            if action.startswith("user.") or "auth" in action.lower():
                item["module"] = "authentication"
            elif action.startswith("document.") or "content" in action.lower():
                item["module"] = "content"
            elif action.startswith("license.") or "drm" in action.lower():
                item["module"] = "drm"
            elif action.startswith("finance.") or "wallet" in action.lower() or "withdrawal" in action.lower():
                item["module"] = "finance"
            elif action.startswith("ai.") or "agent" in action.lower() or "intervention" in action.lower():
                item["module"] = "agentic_ai"
            else:
                item["module"] = "management"

        if not item.get("severity"):
            action_lower = action.lower()
            if "fail" in action_lower or "denied" in action_lower or "error" in action_lower:
                item["severity"] = "ERROR"
            elif "ban" in action_lower or "security" in action_lower or "unauthorized" in action_lower:
                item["severity"] = "SECURITY"
            elif "config" in action_lower or "kyc" in action_lower or "critical" in action_lower:
                item["severity"] = "CRITICAL"
            elif "warn" in action_lower:
                item["severity"] = "WARNING"
            else:
                item["severity"] = "INFO"

        if not item.get("status"):
            action_lower = action.lower()
            if "fail" in action_lower or "error" in action_lower:
                item["status"] = "FAILED"
            elif "denied" in action_lower or "reject" in action_lower:
                item["status"] = "DENIED"
            else:
                item["status"] = "SUCCESS"

        if not item.get("hash"):
            item["hash"] = AuditService._compute_hash(item)

        return item

    @staticmethod
    def _build_filter(
        module: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        action: Optional[str] = None,
        actor_id: Optional[str] = None,
        search: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        query_conditions: List[Dict[str, Any]] = []

        if module:
            query_conditions.append({
                "$or": [
                    {"module": module},
                    {"action": {"$regex": f"^{module}", "$options": "i"}},
                ]
            })

        if severity:
            query_conditions.append({"severity": severity.upper()})

        if status:
            query_conditions.append({"status": status.upper()})

        if action:
            query_conditions.append({"action": {"$regex": action, "$options": "i"}})

        if actor_id:
            query_conditions.append({
                "$or": [
                    {"actor_id": actor_id},
                    {"actor_email": actor_id},
                ]
            })

        date_condition: Dict[str, Any] = {}
        if from_date:
            try:
                dt_from = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
                date_condition["$gte"] = dt_from
            except Exception:
                pass
        if to_date:
            try:
                dt_to = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
                date_condition["$lte"] = dt_to
            except Exception:
                pass
        if date_condition:
            query_conditions.append({
                "$or": [
                    {"timestamp": date_condition},
                    {"created_at": date_condition},
                ]
            })

        if search:
            regex_val = {"$regex": search, "$options": "i"}
            query_conditions.append({
                "$or": [
                    {"action": regex_val},
                    {"actor_id": regex_val},
                    {"actor_email": regex_val},
                    {"target_id": regex_val},
                    {"target_type": regex_val},
                    {"ip_address": regex_val},
                    {"module": regex_val},
                ]
            })

        if not query_conditions:
            return {}
        if len(query_conditions) == 1:
            return query_conditions[0]
        return {"$and": query_conditions}

    @staticmethod
    async def get_audit_logs(
        page: int = 1,
        page_size: int = 20,
        module: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        action: Optional[str] = None,
        actor_id: Optional[str] = None,
        search: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        query = AuditService._build_filter(
            module=module,
            severity=severity,
            status=status,
            action=action,
            actor_id=actor_id,
            search=search,
            from_date=from_date,
            to_date=to_date,
        )

        total = await mongo.count_documents("audit_logs", query)
        skip = (page - 1) * page_size
        cursor = mongo.find("audit_logs", query, sort=[("timestamp", -1)], skip=skip, limit=page_size)
        raw_logs = await cursor.to_list(length=page_size)

        items = [AuditService._enrich_log(log) for log in raw_logs]
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    @staticmethod
    async def get_audit_stats() -> Dict[str, Any]:
        total_events = await mongo.count_documents("audit_logs", {})
        now = datetime.now(timezone.utc)
        start_of_day = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

        today_events = await mongo.count_documents(
            "audit_logs",
            {"$or": [{"timestamp": {"$gte": start_of_day}}, {"created_at": {"$gte": start_of_day}}]}
        )

        security_alerts = await mongo.count_documents(
            "audit_logs",
            {
                "$or": [
                    {"severity": {"$in": ["SECURITY", "CRITICAL"]}},
                    {"action": {"$regex": "ban|security|unauthorized|denied|breach", "$options": "i"}},
                ]
            }
        )

        failed_operations = await mongo.count_documents(
            "audit_logs",
            {
                "$or": [
                    {"status": {"$in": ["FAILED", "DENIED", "ERROR"]}},
                    {"action": {"$regex": "fail|error|reject|denied", "$options": "i"}},
                ]
            }
        )

        admin_actions = await mongo.count_documents(
            "audit_logs",
            {
                "$or": [
                    {"action": {"$regex": "system\\.|user\\.shadowban|user\\.kyc|report\\.update|config", "$options": "i"}},
                    {"actor_role": "admin"},
                ]
            }
        )

        recent_sample = await mongo.find("audit_logs", {}, sort=[("timestamp", -1)], limit=200).to_list(length=200)
        module_counts: Dict[str, int] = {
            "authentication": 0,
            "management": 0,
            "content": 0,
            "drm": 0,
            "finance": 0,
            "agentic_ai": 0,
        }
        severity_counts: Dict[str, int] = {
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0,
            "SECURITY": 0,
        }

        for raw in recent_sample:
            enriched = AuditService._enrich_log(raw)
            mod = enriched.get("module", "management")
            sev = enriched.get("severity", "INFO")
            if mod in module_counts:
                module_counts[mod] += 1
            else:
                module_counts[mod] = 1
            if sev in severity_counts:
                severity_counts[sev] += 1
            else:
                severity_counts[sev] = 1

        return {
            "total_events": total_events,
            "today_events": today_events,
            "security_alerts": security_alerts,
            "failed_operations": failed_operations,
            "admin_actions": admin_actions,
            "module_distribution": module_counts,
            "severity_distribution": severity_counts,
        }

    @staticmethod
    async def export_audit_logs(
        format_type: str = "json",
        module: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        action: Optional[str] = None,
        actor_id: Optional[str] = None,
        search: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        query = AuditService._build_filter(
            module=module,
            severity=severity,
            status=status,
            action=action,
            actor_id=actor_id,
            search=search,
            from_date=from_date,
            to_date=to_date,
        )

        cursor = mongo.find("audit_logs", query, sort=[("timestamp", -1)], limit=1000)
        raw_logs = await cursor.to_list(length=1000)
        items = [AuditService._enrich_log(log) for log in raw_logs]

        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        normalized_format = format_type.lower()

        if normalized_format == "csv":
            output = io.StringIO()
            fieldnames = [
                "id",
                "timestamp",
                "actor_id",
                "actor_email",
                "module",
                "action",
                "severity",
                "status",
                "target_type",
                "target_id",
                "ip_address",
                "hash",
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for item in items:
                row = {
                    "id": item.get("_id", ""),
                    "timestamp": item.get("timestamp", ""),
                    "actor_id": item.get("actor_id", ""),
                    "actor_email": item.get("actor_email", ""),
                    "module": item.get("module", ""),
                    "action": item.get("action", ""),
                    "severity": item.get("severity", ""),
                    "status": item.get("status", ""),
                    "target_type": item.get("target_type", ""),
                    "target_id": item.get("target_id", ""),
                    "ip_address": item.get("ip_address", ""),
                    "hash": item.get("hash", ""),
                }
                writer.writerow(row)

            return {
                "format": "csv",
                "filename": f"kiem_toan_{timestamp_str}.csv",
                "content": output.getvalue(),
                "total_exported": len(items),
            }

        return {
            "format": "json",
            "filename": f"kiem_toan_{timestamp_str}.json",
            "content": items,
            "total_exported": len(items),
        }

    @staticmethod
    async def verify_audit_integrity(log_id: Optional[str] = None) -> Dict[str, Any]:
        if log_id:
            raw_log = await mongo.find_one("audit_logs", {"_id": log_id})
            if not raw_log:
                return {
                    "verified": False,
                    "checked_records": 0,
                    "tampered_records": 1,
                    "status": "NOT_FOUND",
                }
            enriched = AuditService._enrich_log(raw_log)
            calculated_hash = AuditService._compute_hash(enriched)
            is_valid = (raw_log.get("hash") is None) or (raw_log.get("hash") == calculated_hash)
            return {
                "verified": is_valid,
                "checked_records": 1,
                "tampered_records": 0 if is_valid else 1,
                "status": "SECURE" if is_valid else "TAMPERED",
            }

        cursor = mongo.find("audit_logs", {}, sort=[("timestamp", -1)], limit=100)
        raw_logs = await cursor.to_list(length=100)
        checked = len(raw_logs)
        tampered = 0

        for raw_log in raw_logs:
            enriched = AuditService._enrich_log(raw_log)
            calculated_hash = AuditService._compute_hash(enriched)
            if raw_log.get("hash") and raw_log.get("hash") != calculated_hash:
                tampered += 1

        return {
            "verified": tampered == 0,
            "checked_records": checked,
            "tampered_records": tampered,
            "status": "SECURE" if tampered == 0 else "INTEGRITY_WARNING",
        }

    @staticmethod
    async def get_moderator_activity_log(user_id: str) -> List[Dict[str, Any]]:
        res = await AuditService.get_audit_logs(actor_id=user_id, page=1, page_size=50)
        return res.get("items", [])
