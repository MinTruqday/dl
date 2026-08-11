import json
import pathlib
import re
import sys


HTTP_METHODS = {"delete", "get", "patch", "post", "put"}
EXTERNAL_FETCH_ARGUMENTS = {"previewUrl", "upload_url"}
IGNORED_DIRECTORY_NAMES = {
    ".git",
    ".next",
    ".turbo",
    "coverage",
    "dist",
    "node_modules",
}
FETCH_PATTERN = re.compile(r"fetch\s*\(\s*(`[^`]*`|[A-Za-z_$][\w$]*)", re.DOTALL)
ASSIGNMENT_PATTERN = re.compile(
    r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*`\$\{API_URL\}([^`]*)`"
)
FUNCTION_PATTERN = re.compile(
    r"(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{"
)
METHOD_PATTERN = re.compile(r"method\s*:\s*[\"']([A-Z]+)[\"']")
PARAMETER_PATTERN = re.compile(r"\$\{[^}]+\}")


def normalize(path: str) -> str:
    clean = path.split("?", 1)[0]
    if clean.count("${") > clean.count("}"):
        clean = clean.split("${", 1)[0]
    clean = PARAMETER_PATTERN.sub("{}", clean)
    clean = re.sub(r"/+", "/", clean)
    return clean if clean.startswith("/") else f"/{clean}"


def matches(frontend_path: str, backend_path: str) -> bool:
    frontend_parts = frontend_path.strip("/").split("/")
    backend_parts = backend_path.strip("/").split("/")
    if len(frontend_parts) != len(backend_parts):
        return False
    return all(
        frontend == "{}"
        or backend.startswith("{")
        or frontend == backend
        for frontend, backend in zip(frontend_parts, backend_parts)
    )


def load_operations(openapi_dir: pathlib.Path) -> set[tuple[str, str]]:
    operations = set()
    for source in openapi_dir.glob("*.json"):
        document = json.loads(source.read_text(encoding="utf-8"))
        for path, methods in document.get("paths", {}).items():
            for method in methods:
                if method.lower() in HTTP_METHODS:
                    operations.add((method.upper(), path))
    return operations


def load_frontend_calls(frontend_dir: pathlib.Path):
    calls = []
    external = []
    total_fetches = 0
    for source in frontend_dir.rglob("*"):
        if source.suffix not in {".ts", ".tsx"}:
            continue
        if any(part in IGNORED_DIRECTORY_NAMES for part in source.parts):
            continue
        text = source.read_text(encoding="utf-8")
        assignments = [
            (match.start(), match.group(1), match.group(2))
            for match in ASSIGNMENT_PATTERN.finditer(text)
        ]
        for match in FETCH_PATTERN.finditer(text):
            total_fetches += 1
            tail = text[match.end() : match.end() + 1200]
            closing = tail.find(");")
            call_options = tail[:closing] if closing >= 0 else tail
            method_match = METHOD_PATTERN.search(call_options)
            method = method_match.group(1) if method_match else "GET"
            line = text.count("\n", 0, match.start()) + 1
            argument = match.group(1)
            path = None
            if argument.startswith("`"):
                template = argument[1:-1]
                if template.startswith("${API_URL}"):
                    path = template[len("${API_URL}") :]
            else:
                candidates = [
                    assignment
                    for assignment in assignments
                    if assignment[0] < match.start() and assignment[1] == argument
                ]
                if candidates:
                    path = candidates[-1][2]
            if path is None:
                external.append((source, line, argument))
                continue
            if path.startswith("${"):
                functions = [
                    function
                    for function in FUNCTION_PATTERN.finditer(text)
                    if function.start() < match.start()
                ]
                function_name = functions[-1].group(1) if functions else ""
                literal_calls = re.findall(
                    rf"\b{re.escape(function_name)}\s*\(\s*[\"']([^\"']+)[\"']",
                    text,
                )
                if not literal_calls:
                    calls.append((method, "<unresolved>", source, line))
                    continue
                for literal_path in literal_calls:
                    calls.append((method, normalize(literal_path), source, line))
                continue
            calls.append((method, normalize(path), source, line))
    return calls, external, total_fetches


def main() -> int:
    openapi_dir = pathlib.Path(sys.argv[1])
    frontend_dir = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "frontend")
    operations = load_operations(openapi_dir)
    calls, external, total_fetches = load_frontend_calls(frontend_dir)
    missing = []
    for method, frontend_path, source, line in calls:
        if not any(
            method == backend_method and matches(frontend_path, backend_path)
            for backend_method, backend_path in operations
        ):
            missing.append((method, frontend_path, source, line))
    unexpected_external = [
        entry for entry in external if entry[2] not in EXTERNAL_FETCH_ARGUMENTS
    ]
    if unexpected_external:
        for source, line, argument in unexpected_external:
            print(f"{source}:{line}:UNRESOLVED:{argument}")
    if missing or unexpected_external:
        for method, path, source, line in missing:
            print(f"{source}:{line}:{method}:{path}")
        return 1
    print(
        f"frontend_backend_contract_audit_passed fetches={total_fetches} "
        f"internal_calls={len(calls)} external_fetches={len(external)} "
        f"operations={len(operations)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
