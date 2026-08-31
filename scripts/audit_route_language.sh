#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$PROJECT_DIR"

FORBIDDEN_VERSIONED=$(rg -n '/api/qa|/api/admin|/v1(?:/|\b)' backend frontend scripts docker-compose.yml prometheus.yml \
  --glob '!**/node_modules/**' \
  --glob '!**/.next/**' \
  --glob '!**/pnpm-lock.yaml' \
  --glob '!backend/ai/tests/model_provider_stub.py' \
  --glob '!scripts/audit_route_language.sh' || true)

FORBIDDEN_ENGLISH=$(rg -n '/knowledge(?:/|\b)|/worker/internal|/google/callback|presigned-url|/noi-bo/qa/' backend docker-compose.yml prometheus.yml frontend/features/*/services frontend/shared/services \
  --glob '!**/node_modules/**' \
  --glob '!**/.next/**' \
  --glob '!**/pnpm-lock.yaml' \
  --glob '!backend/ai/tests/model_provider_stub.py' \
  --glob '!scripts/audit_route_language.sh' || true)

FOUND=$(printf '%s\n%s' "$FORBIDDEN_VERSIONED" "$FORBIDDEN_ENGLISH")

if [ -n "$FOUND" ]; then
  printf '%s\n' "$FOUND"
  exit 1
fi
