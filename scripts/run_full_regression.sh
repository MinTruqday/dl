#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_DIR"

"$PROJECT_DIR/scripts/audit_route_language.sh"
if [ -f "$PROJECT_DIR/AGENTIC_AI_TEST_MANAGEMENT_MASTER_SPEC.md" ]; then
  python3 "$PROJECT_DIR/scripts/audit_master_spec.py"
else
  echo "master_spec_audit_skipped canonical_file_missing"
fi
docker compose up -d
for service in authentication content ai testing notification frontend worker; do
  attempts=0
  while [ "$attempts" -lt 90 ]; do
    container=$(docker compose ps -q "$service")
    state=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container" 2>/dev/null || true)
    if [ "$state" = "healthy" ] || [ "$state" = "running" ]; then
      break
    fi
    attempts=$((attempts + 1))
    sleep 2
  done
  if [ "$attempts" -ge 90 ]; then
    echo "service_not_ready $service"
    docker compose logs --tail=100 "$service"
    exit 1
  fi
done
docker compose exec -T testing python -m pytest -q
docker compose exec -T testing sh -lc 'for f in tests/integration_contracts.py tests/integration_api_artifacts.py tests/integration_test_planning_v42.py tests/integration_project_restore.py tests/integration_requirement_composition.py tests/integration_test_case_templates.py tests/integration_device_matrix.py tests/integration_project_notifications.py tests/integration_specialized_ai_design.py tests/integration_webhooks.py tests/integration_automation_scripts.py tests/integration_connectors.py tests/integration_automation_execution.py tests/integration_cicd.py tests/integration_collaboration.py tests/integration_run_resume_not_applicable.py tests/integration_bug_trace_suggestion.py tests/integration_bulk_operations.py tests/integration_vertical.py tests/integration_v43_catalog.py tests/integration_worker.py; do python "$f" || exit $?; done'
docker compose exec -T testing python tests/migration_audit.py
docker compose exec -T testing python tests/performance_smoke.py
docker compose exec -T ai python -m pytest -q -p no:cacheprovider tests/test_ai_architecture.py
docker compose run --rm --no-deps --user root -v "$PROJECT_DIR/backend/content/tests:/app/tests:ro" content sh -lc 'pip install -q pytest && pytest -q -p no:cacheprovider tests'
docker compose exec -T authentication sh -lc 'python tests/test_function_catalog.py && python tests/test_email_verification.py && for f in tests/integration_core_identity.py tests/integration_v42_platform.py tests/integration_v42_self_service.py tests/integration_v43_platform_controls.py; do python tests/seed_frontend_e2e.py >/dev/null || exit $?; python "$f" || exit $?; done'
docker compose exec -T notification python tests/test_function_catalog.py
docker compose exec -T frontend sh -lc 'pnpm format:check && pnpm lint && pnpm audit:source && pnpm test:unit'
docker compose run --rm --no-deps -v /app/.next-build frontend sh -lc 'NEXT_BUILD_DIST_DIR=.next-build pnpm build'
"$PROJECT_DIR/scripts/run_frontend_e2e.sh"
git diff --check
docker compose ps --format '{{.Service}} {{.Health}}'
