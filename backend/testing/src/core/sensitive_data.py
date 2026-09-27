import re



def secret_pattern():
    return re.compile('token|secret|password|authorization|cookie|api[-_]?key', re.I)


def redact_sensitive_text(value):
    
    
    result = re.sub(
        '(?i)([?&](?:token|secret|password|api[-_]?key)=)(?!Đã%20ẩn|Đã ẩn)[^&#\\s]+',
        lambda match: f"{match.group(1)}{replacement}",
        value,
    )
    for pattern_name in ("raw_assignment_pattern", "inline_value_pattern"):
        result = re.sub(
            {'redacted_value': 'Đã ẩn',
 'field_name_pattern': 'token|secret|password|authorization|cookie|api[-_]?key',
 'raw_assignment_pattern': '(password|secret|token|api[_-]?key)(\\s*[:=]\\s*)[\'\\"](?!\\$\\{|<|Đã '
                           'ẩn)[^\'\\"]{4,}[\'\\"]',
 'placeholder_pattern': '[A-Z][A-Z0-9_]{0,99}',
 'url_value_pattern': '(?i)([?&](?:token|secret|password|api[-_]?key)=)(?!Đã%20ẩn|Đã ẩn)[^&#\\s]+',
 'inline_value_pattern': '(?i)(authorization|token|secret|password|api[-_]?key)(\\s*[:=]\\s*)[\'"]?(?!Đã '
                         'ẩn)[^\'"\\s;,&]+'}[pattern_name],
            lambda match: f"{match.group(1)}{match.group(2)}{replacement}",
            result,
            flags=re.I,
        )
    return result


def redact_sensitive_data(value):
    
    if isinstance(value, dict):
        return {
            key: 'Đã ẩn'
            if secret_pattern().search(str(key))
            else redact_sensitive_data(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive_data(item) for item in value]
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value
