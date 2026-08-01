import re
from pathlib import Path


root = Path(__file__).resolve().parents[1]
backend = root / "backend"
violations = []
for path in sorted(backend.glob("*/src/**/*.py")):
    if path.name in {"configuration.py", "database.py", "mongo.py"}:
        continue
    service = path.relative_to(backend).parts[0].upper()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for owner in re.findall(r"settings\.([A-Z_]+)_DB_NAME", line):
            if owner != service:
                violations.append(f"{path.relative_to(root)}:{line_number} {service}->{owner}")
for violation in violations:
    print(violation)
print(f"cross_database_accesses={len(violations)}")
raise SystemExit(bool(violations))
