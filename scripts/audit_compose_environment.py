import json
import pathlib
import re
import subprocess
import sys


root = pathlib.Path(__file__).resolve().parents[1]
sensitive = {
    "GOOGLE_CLIENT_SECRET",
    "HF_TOKEN",
    "MINIO_ACCESS_KEY",
    "MINIO_SECRET_KEY",
    "PAYOS_API_KEY",
    "PAYOS_CHECKSUM_KEY",
    "SMTP_PASS",
    "TAVILY_API_KEY",
}
if len(sys.argv) > 1 and sys.argv[1] == "-":
    compose = json.load(sys.stdin)
else:
    rendered = subprocess.run(
        ["docker", "compose", "config", "--format", "json"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    compose = json.loads(rendered.stdout)
violations = []
for service, definition in compose.get("services", {}).items():
    config_path = (
        root
        / "backend"
        / service
        / "src"
        / "core"
        / "infrastructure"
        / "configuration.py"
    )
    if not config_path.is_file():
        continue
    source = config_path.read_text(encoding="utf-8")
    required = set(re.findall(r'os\.environ\["([A-Z0-9_]+)"\]', source))
    provided = set((definition.get("environment") or {}).keys())
    for name in sorted(required - provided):
        violations.append(f"{service}:missing:{name}")
    for name in sorted((provided & sensitive) - required):
        violations.append(f"{service}:excess_secret:{name}")
    for name in sorted(
        name for name in provided - required if name.endswith("_DB_NAME")
    ):
        violations.append(f"{service}:excess_database:{name}")
for violation in violations:
    print(violation)
print(f"compose_environment_violations={len(violations)}")
raise SystemExit(bool(violations))
