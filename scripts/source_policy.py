import ast
import io
import pathlib
import subprocess
import sys
import tokenize


ROOT = pathlib.Path(__file__).resolve().parents[1]
PYTHON_SUFFIXES = {".py"}
WEB_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".css", ".scss"}
CONFIG_SUFFIXES = {".yaml", ".yml", ".sh"}
TEXTUAL_ELLIPSIS = "." * 3
UNICODE_ELLIPSIS = chr(0x2026)


def tracked_files():
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    for raw_name in result.stdout.split(b"\0"):
        if not raw_name:
            continue
        path = ROOT / raw_name.decode()
        if path.is_file():
            yield path


def is_emoji(character):
    value = ord(character)
    return (
        0x1F000 <= value <= 0x1FAFF
        or 0x2600 <= value <= 0x27BF
        or value == 0xFE0F
    )


def add_text_issues(path, line, text, issues):
    if TEXTUAL_ELLIPSIS in text or UNICODE_ELLIPSIS in text:
        issues.append((path, line, "textual_ellipsis"))
    if any(is_emoji(character) for character in text):
        issues.append((path, line, "emoji"))


def scan_python(path, source, issues):
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            if token.type == tokenize.COMMENT:
                issues.append((path, token.start[0], "comment"))
    except tokenize.TokenError as error:
        issues.append((path, 1, f"tokenize_error:{error}"))
        return
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        issues.append((path, error.lineno or 1, "syntax_error"))
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            add_text_issues(path, node.lineno, node.value, issues)
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {
            "debug",
            "info",
            "warning",
            "error",
            "exception",
            "critical",
        }:
            continue
        if not node.args:
            continue
        message = node.args[0]
        if (
            len(node.args) == 1
            and isinstance(message, ast.Constant)
            and isinstance(message.value, str)
            and "{" in message.value
        ):
            issues.append((path, message.lineno, "uninterpolated_log"))
        try:
            rendered = ast.unparse(message)
        except Exception:
            rendered = ""
        lowered = rendered.lower()
        if "successfully" in lowered:
            issues.append((path, message.lineno, "verbose_success_log"))
        if "str(" in rendered and "error" in lowered:
            issues.append((path, message.lineno, "raw_exception_log"))


def scan_web(path, source, issues):
    index = 0
    line = 1
    length = len(source)
    while index < length:
        character = source[index]
        following = source[index + 1] if index + 1 < length else ""
        if character == "\n":
            line += 1
            index += 1
            continue
        if character == "/" and following == "/":
            issues.append((path, line, "comment"))
            index += 2
            while index < length and source[index] != "\n":
                index += 1
            continue
        if character == "/" and following == "*":
            issues.append((path, line, "comment"))
            index += 2
            while index < length:
                if source[index] == "\n":
                    line += 1
                if source[index] == "*" and index + 1 < length and source[index + 1] == "/":
                    index += 2
                    break
                index += 1
            continue
        if character == "/" and following not in {"", "/", "*"}:
            prior_index = index - 1
            while prior_index >= 0 and source[prior_index].isspace():
                prior_index -= 1
            prior = source[prior_index] if prior_index >= 0 else ""
            if prior in {"", "(", "=", ",", "[", "!", "?", ":", ";", "{"}:
                index += 1
                in_character_class = False
                while index < length:
                    character = source[index]
                    if character == "\\":
                        index += 2
                        continue
                    if character == "[":
                        in_character_class = True
                    elif character == "]":
                        in_character_class = False
                    elif character == "/" and not in_character_class:
                        index += 1
                        while index < length and source[index].isalpha():
                            index += 1
                        break
                    if character == "\n":
                        break
                    index += 1
                continue
        if character in {'"', "'", "`"}:
            if character == "'" and index > 0 and source[index - 1].isalnum():
                index += 1
                continue
            delimiter = character
            string_line = line
            value = []
            index += 1
            while index < length:
                character = source[index]
                if character == "\\":
                    if index + 1 < length:
                        value.extend((character, source[index + 1]))
                        index += 2
                        continue
                if character == delimiter:
                    index += 1
                    break
                if character == "\n":
                    line += 1
                value.append(character)
                index += 1
            add_text_issues(path, string_line, "".join(value), issues)
            continue
        index += 1
    for line_number, text in enumerate(source.splitlines(), 1):
        if UNICODE_ELLIPSIS in text or any(is_emoji(character) for character in text):
            add_text_issues(path, line_number, text, issues)


def scan_config(path, source, issues):
    for line_number, text in enumerate(source.splitlines(), 1):
        if text.lstrip().startswith("#"):
            issues.append((path, line_number, "comment"))
        add_text_issues(path, line_number, text, issues)


def main():
    issues = []
    for path in tracked_files():
        suffix = path.suffix.lower()
        if suffix not in PYTHON_SUFFIXES | WEB_SUFFIXES | CONFIG_SUFFIXES and not path.name.startswith("Dockerfile"):
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative_path = path.relative_to(ROOT)
        if suffix in PYTHON_SUFFIXES:
            scan_python(relative_path, source, issues)
        elif suffix in WEB_SUFFIXES:
            scan_web(relative_path, source, issues)
        else:
            scan_config(relative_path, source, issues)
    for path, line, issue in sorted(set(issues), key=lambda item: (str(item[0]), item[1], item[2])):
        print(f"{path}:{line}:{issue}")
    if issues:
        return 1
    print("source_policy_passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
