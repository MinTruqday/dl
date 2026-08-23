import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def structured_content(prompt: str) -> str:
    if '"is_safe"' in prompt and '"risk_score"' in prompt:
        return json.dumps(
            {
                "is_safe": True,
                "risk_score": 0,
                "threat_category": "none",
                "reason": "Passed isolated integration model inspection",
            },
            ensure_ascii=False,
        )
    if (
        '"predicted_difficulty"' in prompt and '"reason_summary"' in prompt
    ) or "Đánh giá trực tiếp độ khó" in prompt:
        return json.dumps(
            {
                "predicted_difficulty": 3,
                "confidence": 0.8,
                "reason_summary": ["Yêu cầu vận dụng quy tắc đạo hàm cơ bản"],
            },
            ensure_ascii=False,
        )
    if (
        '"stem"' in prompt and '"answer_key"' in prompt
    ) or "Tạo đúng một câu hỏi đánh giá" in prompt:
        return json.dumps(
            {
                "stem": "Đạo hàm của x bình phương là biểu thức nào",
                "options": [
                    {"id": "A", "text": "Hai x"},
                    {"id": "B", "text": "x"},
                    {"id": "C", "text": "Hai"},
                    {"id": "D", "text": "x bình phương"},
                ],
                "answer_key": {"option_id": "A"},
                "solution": "Áp dụng quy tắc đạo hàm lũy thừa cho x bình phương",
                "primary_concept": "Đạo hàm",
                "primary_skill": "Tính đạo hàm",
                "learning_objective": "Tính được đạo hàm của hàm lũy thừa cơ bản",
            },
            ensure_ascii=False,
        )
    return "OK"


class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in {"/api/tags", "/api/ps"}:
            self.send_json({"models": [{"name": "integration-model"}]})
            return
        self.send_json({"status": "not_found"}, 404)

    def do_POST(self) -> None:
        if self.path != "/api/chat":
            self.send_json({"status": "not_found"}, 404)
            return
        size = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(size) or b"{}")
        prompt = "\n".join(
            str(message.get("content", ""))
            for message in payload.get("messages", [])
        )
        content = structured_content(prompt)
        self.send_json(
            {
                "model": "integration-model",
                "message": {"role": "assistant", "content": content},
                "done": True,
                "prompt_eval_count": len(prompt),
                "eval_count": len(content),
            }
        )

    def log_message(self, format: str, *args) -> None:
        return


ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
