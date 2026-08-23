import io
import pathlib
import tokenize


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_ROOTS = (ROOT / "backend", ROOT / "scripts")
violations = []
file_count = 0

for source_root in SOURCE_ROOTS:
    for source_file in source_root.rglob("*.py"):
        file_count += 1
        try:
            source = source_file.read_text(encoding="utf-8")
            tokens = tokenize.generate_tokens(io.StringIO(source).readline)
            for token in tokens:
                if token.type == tokenize.COMMENT:
                    relative = source_file.relative_to(ROOT)
                    violations.append(f"{relative}:{token.start[0]}:source_comment")
            if chr(0x2026) in source:
                relative = source_file.relative_to(ROOT)
                violations.append(f"{relative}:textual_ellipsis")
        except (SyntaxError, UnicodeDecodeError, tokenize.TokenError) as error:
            relative = source_file.relative_to(ROOT)
            violations.append(f"{relative}:invalid_python:{error}")

if violations:
    raise SystemExit("\n".join(violations))

print(f"python_source_style_audit_passed files={file_count}")
