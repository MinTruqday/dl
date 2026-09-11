#!/bin/sh
set -eu

docker compose -f docker-compose.yml -f docker-compose.test.yml --profile e2e up -d --build frontend_e2e_server
docker compose -f docker-compose.yml -f docker-compose.test.yml up -d --no-deps --wait authentication content cloud notification testing
docker compose exec -T authentication python tests/seed_frontend_e2e.py
docker compose -f docker-compose.yml -f docker-compose.test.yml --profile e2e run --rm frontend_e2e
