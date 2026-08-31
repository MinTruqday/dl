#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_DIR"

docker compose up -d
docker compose exec -T testing python -m pytest -q
docker compose exec -T testing sh -lc 'for f in tests/integration_contracts.py tests/integration_api_artifacts.py tests/integration_test_planning_v42.py tests/integration_project_restore.py tests/integration_vertical.py tests/integration_v43_catalog.py tests/integration_worker.py; do python "$f" || exit $?; done'
docker compose exec -T testing python tests/migration_audit.py
docker compose exec -T testing python tests/performance_smoke.py
docker compose exec -T ai python -m pytest -q tests/test_ai_architecture.py
docker compose run --rm --no-deps --user root -v "$PROJECT_DIR/backend/content/tests:/app/tests:ro" content sh -lc 'pip install -q pytest && pytest -q tests'
docker compose exec -T authentication sh -lc 'for f in tests/integration_core_identity.py tests/integration_v42_platform.py tests/integration_v42_self_service.py tests/integration_v43_platform_controls.py; do python tests/seed_frontend_e2e.py >/dev/null || exit $?; python "$f" || exit $?; done'
docker compose exec -T frontend sh -lc 'pnpm format:check && pnpm lint && pnpm audit:source && pnpm test:qa && NEXT_BUILD_DIST_DIR=.next-build pnpm build'
"$PROJECT_DIR/scripts/run_frontend_e2e.sh"
git diff --check
docker compose ps --format '{{.Service}} {{.Health}}'
