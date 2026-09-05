import ast
import pathlib
import re
import sys


FORBIDDEN_SEGMENTS = {
    "api",
    "v1",
    "auth",
    "login",
    "logout",
    "refresh",
    "freeze",
    "session",
    "sessions",
    "user",
    "users",
    "admin",
    "accept",
    "accept-with-edit",
    "platform",
    "qa",
    "knowledge",
    "worker",
    "callback",
    "doc",
    "email",
    "tag",
    "tags",
    "presigned-url",
}


FRONTEND_SOURCE_SUFFIXES = {".js", ".jsx", ".ts", ".tsx"}
FORBIDDEN_DYNAMIC_ROUTE_LITERALS = {"accept", "accept-with-edit"}


def route_literals(tree):
    decorator_ids = {
        id(decorator)
        for function in ast.walk(tree)
        if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef))
        for decorator in function.decorator_list
        if isinstance(decorator, ast.Call)
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function_name = node.func.attr if isinstance(node.func, ast.Attribute) else ""
        is_route_decorator = id(node) in decorator_ids and function_name in {
            "get",
            "post",
            "put",
            "patch",
            "delete",
        }
        is_router_constructor = isinstance(node.func, ast.Name) and node.func.id == "APIRouter"
        is_router_mount = function_name == "include_router"
        is_direct_route = function_name == "add_route"
        if not (is_route_decorator or is_router_constructor or is_router_mount or is_direct_route):
            continue

        values = []
        if is_router_constructor or is_router_mount:
            values.extend(keyword.value for keyword in node.keywords if keyword.arg == "prefix")
        elif node.args and isinstance(node.args[0], ast.Constant):
            values.append(node.args[0])
        for value in values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                yield value.value, node.lineno


def main():
    failures = []
    for path in sorted(pathlib.Path("backend").glob("*/src/**/*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            failures.append(f"{path}: không thể phân tích route: {exc}")
            continue
        for route, line in route_literals(tree):
            for segment in route.strip("/").split("/"):
                if segment.startswith("{") and segment.endswith("}"):
                    continue
                if segment.lower() in FORBIDDEN_SEGMENTS:
                    failures.append(f"{path}:{line}: route chứa segment không hợp lệ /{segment}")
    app_root = pathlib.Path("frontend/app")
    if app_root.exists():
        for path in sorted(app_root.rglob("page.*")):
            for segment in path.relative_to(app_root).parts[:-1]:
                if segment.startswith("(") or segment.startswith("["):
                    continue
                if segment.lower() in FORBIDDEN_SEGMENTS:
                    failures.append(
                        f"{path}: route giao diện chứa segment không hợp lệ /{segment}"
                    )
    for path in sorted(pathlib.Path("frontend").rglob("*")):
        if (
            path.suffix not in FRONTEND_SOURCE_SUFFIXES
            or {"node_modules", "coverage"}.intersection(path.parts)
            or any(part.startswith(".next") for part in path.parts)
        ):
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            failures.append(f"{path}: không thể đọc mã nguồn giao diện: {exc}")
            continue
        for line, content in enumerate(source.splitlines(), 1):
            route_content = re.sub(r"[A-Za-z][A-Za-z0-9+.-]*://[^\s'\"`]+", "", content)
            for segment in re.findall(
                r"/([A-Za-z][A-Za-z0-9-]*)(?=[/?#'\"`]|$)", route_content
            ):
                if segment.lower() in FORBIDDEN_SEGMENTS:
                    failures.append(
                        f"{path}:{line}: tham chiếu route chứa segment không hợp lệ /{segment}"
                    )
            if path.name.endswith(".service.js"):
                for segment in FORBIDDEN_DYNAMIC_ROUTE_LITERALS:
                    if re.search(rf"(['\"]){re.escape(segment)}\1", content):
                        failures.append(
                            f"{path}:{line}: route động chứa segment không hợp lệ /{segment}"
                        )
    if failures:
        print("\n".join(failures))
        return 1
    print("route_language_audit_passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
