import pathlib
import re
import sys


EXPECTED = {
    "agentic-ai",
    "authentication",
    "cloud",
    "collection",
    "compilation",
    "content",
    "drm",
    "finance",
    "frontend",
    "humanity",
    "management",
    "messaging",
    "notification",
    "usage",
    "websocket",
    "worker-service",
}

EXPECTED_API_PREFIXES = {
    "/ban-quyen",
    "/bao-ve",
    "/cong-tac",
    "/dau-trang",
    "/doc-hieu",
    "/drm",
    "/drm-ai",
    "/ghim",
    "/giam-sat",
    "/goi-cuoc",
    "/google",
    "/han-muc",
    "/ho-so",
    "/ket-xuat",
    "/kham-pha",
    "/kiem-tien",
    "/kiem-toan",
    "/lich-su",
    "/luu-tru",
    "/mcp",
    "/nap-tien",
    "/ngat-qua-trinh",
    "/nguoi-dung",
    "/noi-bat",
    "/phan-hoi",
    "/phien-ban",
    "/rut-tien",
    "/soan-thao",
    "/su-kien",
    "/suy-luan",
    "/tai-len",
    "/tai-lieu",
    "/thong-bao",
    "/thu-thap",
    "/thu-vien",
    "/tiep-nap",
    "/tin-nhan",
    "/tinh-chinh",
    "/toi-uu",
    "/tro-chuyen",
    "/van-hanh",
    "/vi-tien",
    "/ws",
    "/xac-thuc",
    "/xuat-ban",
}


def main():
    source = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
    required_secret_keys = set()
    for path in pathlib.Path("backend").glob("*/src/core/infrastructure/configuration.py"):
        required_secret_keys.update(
            re.findall(r'os\.environ\["([A-Z0-9_]+)"\]', path.read_text(encoding="utf-8"))
        )
    documents = re.split(r"(?m)^---\s*$", source)
    deployments = {}
    services = {}
    config_maps = set()
    secrets = set()
    secret_keys = set()
    ingress_paths = set()
    issues = []
    for document in documents:
        kind_match = re.search(r"(?m)^kind: ([^\n]+)$", document)
        name_match = re.search(r"metadata:\n  name: ([^\n]+)", document)
        kind = kind_match.group(1).strip() if kind_match else ""
        name = name_match.group(1).strip() if name_match else ""
        if kind == "Deployment":
            labels = re.findall(r"(?m)^\s+app: ([^\n]+)$", document)
            app = labels[0].strip() if labels else ""
            if app not in EXPECTED:
                continue
            deployments[app] = document
            expected_port = 3000 if app == "frontend" else 8000
            if f"containerPort: {expected_port}" not in document:
                issues.append(f"{app}:container_port")
            if not re.search(r"secretRef:\n\s+name: doclib-secrets", document):
                issues.append(f"{app}:secret_reference")
            if not re.search(r"configMapRef:\n\s+name: doclib-config", document):
                issues.append(f"{app}:config_reference")
            if "livenessProbe:" not in document or "readinessProbe:" not in document:
                issues.append(f"{app}:health_probes")
            if "runAsNonRoot: true" not in document or "allowPrivilegeEscalation: false" not in document:
                issues.append(f"{app}:security_context")
        elif kind == "Service":
            labels = re.findall(r"(?m)^\s+app: ([^\n]+)$", document)
            app = labels[-1].strip() if labels else name
            if app not in EXPECTED:
                continue
            services[app] = document
        elif kind == "ConfigMap":
            config_maps.add(name)
        elif kind == "Secret":
            secrets.add(name)
            secret_keys.update(re.findall(r"(?m)^  ([A-Z][A-Z0-9_]+):", document))
        elif kind == "Ingress":
            ingress_paths.update(re.findall(r"(?m)^\s+path: (/[^(/\s]+)", document))
    if set(deployments) != EXPECTED:
        issues.append(f"deployments:{','.join(sorted(EXPECTED.symmetric_difference(deployments)))}")
    if set(services) != EXPECTED:
        issues.append(f"services:{','.join(sorted(EXPECTED.symmetric_difference(services)))}")
    for app in EXPECTED:
        if app in deployments and app not in services:
            issues.append(f"{app}:service_missing")
    if "doclib-registry/" not in source:
        issues.append("image_registry_placeholder")
    if "doclib-config" not in config_maps:
        issues.append("config_map:doclib-config")
    if not any(name.startswith("doclib-secrets-") or name == "doclib-secrets" for name in secrets):
        issues.append("secret:doclib-secrets")
    missing_secret_keys = required_secret_keys - secret_keys
    if missing_secret_keys:
        issues.append(f"secret_keys:{','.join(sorted(missing_secret_keys))}")
    missing_paths = EXPECTED_API_PREFIXES - ingress_paths
    if missing_paths:
        issues.append(f"ingress_paths:{','.join(sorted(missing_paths))}")
    if "rewrite-target" in source:
        issues.append("ingress_rewrites_backend_prefixes")
    if issues:
        print("\n".join(issues))
        return 1
    print(f"kubernetes_audit_passed deployments={len(deployments)} services={len(services)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
