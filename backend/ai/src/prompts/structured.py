import json


def schema_instruction(schema):
    serialized = json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
    rules = [
        "Chỉ trả một giá trị JSON hợp lệ khớp schema",
        "Không thêm diễn giải markdown hoặc code fence",
        "Mọi thuộc tính required phải xuất hiện",
        "Thuộc tính nullable không sử dụng phải là null",
    ]
    if "target_fields" in serialized:
        rules.append("Không khai báo target field khi revised field tương ứng là null")
    return "\n".join([*rules, "OUTPUT_JSON_SCHEMA", serialized])


def correction_instruction(error):
    return "\n".join(
        [
            "Giá trị trước không đạt schema",
            f"Lỗi xác thực {str(error)[:1000]}",
            "Chỉ trả một giá trị JSON đã sửa",
        ]
    )


def tool_selection_instruction(tool_definitions, forced_name=None):
    rules = [
        "Chọn đúng một công cụ phù hợp yêu cầu",
        "Chỉ trả một đối tượng JSON gồm name và arguments",
        "name phải khớp một công cụ đã đăng ký",
        "arguments phải là một đối tượng JSON khớp schema của công cụ",
    ]
    if forced_name:
        rules.append(f"Bắt buộc dùng chính xác công cụ {forced_name}")
    rules.append(f"Công cụ đã đăng ký {tool_definitions}")
    return "\n".join(rules)


def tool_selection_correction_instruction(error):
    return "\n".join(
        [
            "Lựa chọn công cụ trước không hợp lệ",
            f"Lỗi xác thực {str(error)[:1000]}",
            "Chỉ trả một lệnh gọi công cụ JSON đã sửa",
        ]
    )
