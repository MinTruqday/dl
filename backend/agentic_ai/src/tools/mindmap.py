import json
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from loguru import logger


def _build_mindmap_tree(topic: str) -> dict:
    clean_topic = topic.strip().capitalize()
    return {
        "title": f"Sơ đồ tư duy: {clean_topic}",
        "root": {
            "id": "root",
            "name": clean_topic,
            "children": [
                {
                    "id": "branch-1",
                    "name": "Tổng quan & Mục tiêu",
                    "children": [
                        {"id": "node-1-1", "name": "Bối cảnh & Phạm vi áp dụng"},
                        {"id": "node-1-2", "name": "Mục đích & Kết quả đầu ra"},
                        {"id": "node-1-3", "name": "Tiêu chuẩn đánh giá thành công"},
                    ],
                },
                {
                    "id": "branch-2",
                    "name": "Thành phần cốt lõi",
                    "children": [
                        {"id": "node-2-1", "name": "Cấu trúc & Kiến trúc giải pháp"},
                        {"id": "node-2-2", "name": "Quy trình thực thi từng bước"},
                        {"id": "node-2-3", "name": "Công cụ & Tài nguyên hỗ trợ"},
                    ],
                },
                {
                    "id": "branch-3",
                    "name": "Triển khai & Vận hành",
                    "children": [
                        {"id": "node-3-1", "name": "Kế hoạch phân bổ giai đoạn"},
                        {"id": "node-3-2", "name": "Kiểm soát rủi ro & Bảo mật"},
                        {"id": "node-3-3", "name": "Tối ưu & Đánh giá định kỳ"},
                    ],
                },
            ],
        },
    }


@tool
async def generate_mindmap(topic: str, config: RunnableConfig) -> str:
    """
    <module_purpose>
    Generate a structured interactive mindmap diagram for a topic, concept, or project outline.
    </module_purpose>
    <contract>
    WHEN TO USE THIS TOOL:
    - Use this when the user explicitly asks to draw a mindmap, visualize a concept hierarchy, or create a diagram/mindmap for a topic.
    CRITICAL: Returns a structured mindmap tree representation for interactive canvas rendering.
    </contract>
    """
    try:
        tree_data = _build_mindmap_tree(topic)
        mermaid_code = "mindmap\n"
        mermaid_code += f"  root(({tree_data['root']['name']}))\n"
        for b in tree_data["root"]["children"]:
            mermaid_code += f"    {b['name']}\n"
            for sub in b.get("children", []):
                mermaid_code += f"      {sub['name']}\n"

        result_payload = {
            "status": "success",
            "topic": topic,
            "tree": tree_data,
            "mermaid": mermaid_code,
        }

        output_text = (
            f"Đã tạo sơ đồ tư duy cho chủ đề '{topic}':\n\n```mermaid\n{mermaid_code}```\n\n<!--MINDMAP_PAYLOAD:{json.dumps(result_payload, ensure_ascii=False)}-->"
        )
        return output_text
    except Exception as e:
        logger.exception("Failed to generate mindmap")
        return "Đã xảy ra lỗi khi khởi tạo sơ đồ tư duy"
