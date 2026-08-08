import os
import pathlib
import re


root = pathlib.Path(__file__).resolve().parents[1]
source_path = root / "k8s" / ".env"
output_root = root / "k8s" / "generated"
values = {}
for raw_line in source_path.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    name, value = line.split("=", 1)
    values[name.strip()] = value

service_keys = {}
for config_path in sorted(
    (root / "backend").glob("*/src/core/infrastructure/configuration.py")
):
    service = config_path.relative_to(root / "backend").parts[0]
    source = config_path.read_text(encoding="utf-8")
    service_keys[service] = set(
        re.findall(r'os\.environ\["([A-Z0-9_]+)"\]', source)
    )
service_keys["frontend"] = {"NEXT_PUBLIC_API_URL", "NEXT_PUBLIC_WS_URL"}
service_keys["minio"] = {"MINIO_ROOT_PASSWORD", "MINIO_ROOT_USER"}
service_keys["ollama"] = {"LLM_MODEL"}

missing = []
output_root.mkdir(parents=True, exist_ok=True)
for service, keys in sorted(service_keys.items()):
    absent = sorted(keys - values.keys())
    missing.extend(f"{service}:{name}" for name in absent)
    if absent:
        continue
    destination = output_root / f"{service}.env"
    payload = "".join(f"{name}={values[name]}\n" for name in sorted(keys))
    destination.write_text(payload, encoding="utf-8")
    os.chmod(destination, 0o600)
for item in missing:
    print(f"missing_kubernetes_environment:{item}")
print(f"kubernetes_environment_violations={len(missing)}")
raise SystemExit(bool(missing))
