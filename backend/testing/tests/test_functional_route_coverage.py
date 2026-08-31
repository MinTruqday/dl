import ast
from pathlib import Path

from src.main import app


TEST_ROOT = Path(__file__).resolve().parent


def string_value(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(
            item.value if isinstance(item, ast.Constant) else "{}"
            for item in node.values
        )
    return None


def integration_operations():
    operations = []
    files = sorted(TEST_ROOT.glob("integration*.py"))
    files = [path for path in files if path.name != "integration_contracts.py"]
    for path in files:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            method = None
            request_path = None
            if (
                isinstance(node.func, ast.Name)
                and node.func.id in {"request", "call"}
                and len(node.args) >= 3
            ):
                method = string_value(node.args[1])
                request_path = string_value(node.args[2])
            elif (
                isinstance(node.func, ast.Attribute)
                and node.func.attr.lower() in {"get", "post", "put", "patch", "delete"}
                and node.args
            ):
                method = node.func.attr.upper()
                request_path = string_value(node.args[0])
            if method and request_path and "/api/qa/" in request_path:
                normalized = request_path[request_path.index("/api/qa/") :].split("?", 1)[0]
                operations.append((method.upper(), normalized, path.name))
    return operations


def route_matches(route_path, observed_path):
    route_segments = route_path.strip("/").split("/")
    observed_segments = observed_path.strip("/").split("/")
    return len(route_segments) == len(observed_segments) and all(
        route == observed or route.startswith("{")
        for route, observed in zip(route_segments, observed_segments)
    )


def test_every_runtime_operation_has_functional_integration_evidence():
    observed = integration_operations()
    runtime = [
        (method, route.path)
        for route in app.routes
        if route.path.startswith("/api/qa/")
        for method in route.methods or set()
        if method not in {"HEAD", "OPTIONS"}
    ]
    missing = [
        f"{method} {path}"
        for method, path in runtime
        if not any(
            method == observed_method and route_matches(path, observed_path)
            for observed_method, observed_path, _ in observed
        )
    ]
    assert len(runtime) >= 200
    assert missing == []
