import re
import subprocess
from pathlib import Path


root = Path(__file__).resolve().parents[1]
backend = root / "backend"
active_services = set(
    subprocess.run(
        ["docker", "compose", "config", "--services"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
)
violations = []
for path in sorted(backend.glob("*/src/**/*.py")):
    service_name = path.relative_to(backend).parts[0]
    if service_name not in active_services:
        continue
    service = service_name.upper()
    source = path.read_text(encoding="utf-8")
    for line_number, line in enumerate(source.splitlines(), 1):
        for owner in re.findall(r"settings\.([A-Z_]+)_DB_NAME", line):
            if owner != service:
                violations.append(f"{path.relative_to(root)}:{line_number} {service}->{owner}")
        for owner in re.findall(r'(?:os\.getenv\(|os\.environ\[)["\']([A-Z_]+)_DB_NAME', line):
            if owner != service:
                violations.append(f"{path.relative_to(root)}:{line_number} {service}->{owner}")
    if "list_database_names(" in source:
        violations.append(f"{path.relative_to(root)} {service}->ALL_DATABASES")
    if (
        "def get_db(self, db_name" in source
        or "database.client[target_db]" in source
        or "database.mongodb[target_db]" in source
    ):
        violations.append(f"{path.relative_to(root)} {service}->DYNAMIC_DATABASE")
    relative = path.relative_to(backend).as_posix()
    if service == "AI" and (
        "src.store.vector" in source or "src.store.graph" in source or "src.rag.pipeline" in source
    ):
        violations.append(f"{path.relative_to(root)} AI->RAG_IMPLEMENTATION")
    if (
        service == "AI"
        and "qdrant_client" in source
        and not relative.endswith("ai/src/memory/long_term.py")
    ):
        violations.append(f"{path.relative_to(root)} AI->RAG_VECTOR")
for violation in violations:
    print(violation)
print(f"cross_database_accesses={len(violations)}")
raise SystemExit(bool(violations))
