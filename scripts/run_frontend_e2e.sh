#!/bin/sh
set -eu

docker compose exec -T authentication python tests/seed_frontend_e2e.py
docker compose -f docker-compose.yml -f docker-compose.test.yml --profile e2e run --rm frontend_e2e
