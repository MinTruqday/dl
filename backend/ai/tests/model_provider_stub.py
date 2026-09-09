import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def schema_value(schema, name=""):
    if not isinstance(schema, dict):
        return None
    if "default" in schema:
        return schema["default"]
    if "enum" in schema and schema["enum"]:
        return schema["enum"][0]
    if "anyOf" in schema:
        return schema_value(schema["anyOf"][0], name)
    kind = schema.get("type")
    if kind == "object" or "properties" in schema:
        return {key: schema_value(value, key) for key, value in schema.get("properties", {}).items()}
    if kind == "array":
        return []
    if kind == "boolean":
        return True if name == "is_safe" else False
    if kind == "integer":
        return 0
    if kind == "number":
        return 0
    return "none" if name == "threat_category" else "Passed structural security inspection"


def response_for(payload):
    messages = payload.get("messages") or []
    prompt = "\n".join(str(item.get("content", "")) for item in messages)
    capability = re.search(r"capability[=: ]+([a-z_]+)", prompt)
    if capability:
        name = capability.group(1)
        suggestions = []
        if name == "security_test_generation":
            suggestions = [
                {"category": category, "title": f"Kiểm thử {category}", "preconditions": ["Môi trường kiểm thử sẵn sàng"], "action": f"Thực hiện tình huống {category}", "expected": "Hệ thống từ chối an toàn", "requirement_version_ids": []}
                for category in ("authorization", "input_validation", "session")
            ]
        elif name == "performance_plan_generation":
            suggestions = [
                {"workload_type": workload, "title": f"Tải {workload}", "virtual_users": 100, "requests_per_second": 50, "duration_minutes": 30, "ramp_pattern": "Tăng dần", "actions": ["Gọi luồng đăng nhập"], "expected": "Đáp ứng ngưỡng đã khai báo"}
                for workload in ("baseline", "load", "spike", "soak")
            ]
        elif name == "automation_script_generation":
            suggestions = [{"source": "import { test, expect } from '@playwright/test';\ntest('đăng nhập', async ({ page }) => { await page.goto(process.env.BASE_URL); await expect(page).toHaveURL(/.+/); });", "secret_placeholders": ["BASE_URL"]}]
        elif name in {"scenario_generation", "test_generation"}:
            category_match = re.search(r'\\?"categories\\?"\s*:\s*\[\s*\\?"([a-z_]+)', prompt)
            category = category_match.group(1) if category_match else "happy_path"
            suggestions = [{"title": f"Kiểm thử {category}", "category": category, "objective": "Xác minh hành vi trong yêu cầu", "preconditions": "Yêu cầu đã được chốt chuẩn", "steps": [{"action": "Thực hiện hành vi với dữ liệu phù hợp", "expected": "Kết quả khớp tiêu chí chấp nhận", "test_data": {}}], "expected": "Kết quả khớp tiêu chí chấp nhận", "acceptance_criterion_ids": []}]
        result = {
            "capability": name,
            "suggestions": suggestions,
            "evidence_refs": [],
            "confidence": 0.9,
            "warnings": [],
            "status": "SUCCESS",
            "degraded_mode": None,
            "model": {"provider": "stub", "model": payload.get("model", "integration-model")},
            "reason_codes": [],
            "workflow": {},
            "answer": "10",
        }
        output_schema = payload.get("format")
        if isinstance(output_schema, dict):
            properties = output_schema.get("properties", {})
            result = {key: value for key, value in result.items() if key in properties}
        return json.dumps(result, ensure_ascii=False)
    output_schema = payload.get("format")
    if isinstance(output_schema, dict):
        return json.dumps(schema_value(output_schema), ensure_ascii=False)
    return "OK"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.endswith("/tags"):
            self.send_json({"models": [{"name": "integration-model"}]})
            return
        if self.path.endswith("/ps"):
            self.send_json({"models": [{"name": "integration-model"}]})
            return
        self.send_error(404)

    def do_POST(self):
        if not self.path.endswith("/api/chat"):
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        content = response_for(payload)
        body = {"model": payload.get("model", "integration-model"), "message": {"role": "assistant", "content": content}, "done": True, "prompt_eval_count": 1, "eval_count": 1}
        if payload.get("stream"):
            encoded = (json.dumps(body, ensure_ascii=False) + "\n").encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return
        self.send_json(body)

    def send_json(self, value):
        encoded = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *_):
        return


ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
