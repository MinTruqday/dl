import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parents[1]
def main():
    issues = []
    dockerfiles = sorted((ROOT / "backend").glob("*/Dockerfile"))
    dockerfiles.append(ROOT / "frontend" / "Dockerfile")
    for path in dockerfiles:
        source = path.read_text(encoding="utf-8")
        users = re.findall(r"(?m)^USER\s+([^\s]+)", source)
        if not users or not re.fullmatch(r"[1-9]\d*:[1-9]\d*", users[-1]):
            issues.append(f"{path.relative_to(ROOT)}:numeric_non_root_user")
        if "HEALTHCHECK " not in source:
            issues.append(f"{path.relative_to(ROOT)}:healthcheck")

    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    frontend = compose.split("\n  frontend:\n", 1)[1].split("\n  notification:\n", 1)[0]
    if "env_file:" in frontend:
        issues.append("docker-compose.yml:frontend_secret_env_file")
    for required in ("NEXT_PUBLIC_API_URL", "NEXT_PUBLIC_WS_URL"):
        if required not in frontend:
            issues.append(f"docker-compose.yml:frontend_missing_{required.lower()}")

    if issues:
        print("\n".join(issues))
        return 1
    print(f"container_security_audit_passed images={len(dockerfiles)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
