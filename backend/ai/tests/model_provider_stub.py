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
    output_schema = payload.get("format")
    if isinstance(output_schema, dict):
        return json.dumps(schema_value(output_schema), ensure_ascii=False)
    capability = re.search(r"capability[=: ]+([a-z_]+)", prompt)
    if capability:
        return json.dumps(
            {
                "capability": capability.group(1),
                "suggestions": [],
                "evidence_refs": [],
                "confidence": 0,
                "warnings": [],
                "status": "SUCCESS",
                "degraded_mode": None,
                "model": {"provider": "stub", "model": payload.get("model", "integration-model")},
                "reason_codes": [],
                "workflow": {},
            },
            ensure_ascii=False,
        )
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
