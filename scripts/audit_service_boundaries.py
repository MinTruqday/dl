import re
from pathlib import Path


root = Path(__file__).resolve().parents[1]
backend = root / "backend"
violations = []
for path in sorted(backend.glob("*/src/**/*.py")):
    service = path.relative_to(backend).parts[0].upper()
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
for violation in violations:
    print(violation)
print(f"cross_database_accesses={len(violations)}")
raise SystemExit(bool(violations))
