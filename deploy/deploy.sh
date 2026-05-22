#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/srv/projects/web/recruiter-candidate-hub"
APPS_STACK_DIR="/srv/docker/apps-stack"
APPS_ENV_FILE="${APPS_STACK_DIR}/.env"
BRANCH="main"

if [ ! -f "${APPS_ENV_FILE}" ]; then
  echo "Missing ${APPS_ENV_FILE}"
  exit 1
fi

set -a
source "${APPS_ENV_FILE}"
set +a

export RCH_DATABASE_URL="postgresql://${RCH_DB_USER}:${RCH_DB_PASSWORD}@postgres:5432/${RCH_DB_NAME}"

cd "${APPS_STACK_DIR}"
docker compose up -d

for i in {1..30}; do
  if docker exec -e PGPASSWORD="$POSTGRES_SUPERPASSWORD" common-database \
    pg_isready -U "$POSTGRES_SUPERUSER" -d postgres >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

docker exec -e PGPASSWORD="$POSTGRES_SUPERPASSWORD" common-database \
  psql -U "$POSTGRES_SUPERUSER" -d postgres -v ON_ERROR_STOP=1 \
  -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${RCH_DB_USER}') THEN CREATE ROLE \"${RCH_DB_USER}\" LOGIN PASSWORD '${RCH_DB_PASSWORD}'; END IF; END \$\$;"
docker exec -e PGPASSWORD="$POSTGRES_SUPERPASSWORD" common-database \
  psql -U "$POSTGRES_SUPERUSER" -d postgres -v ON_ERROR_STOP=1 \
  -c "ALTER ROLE \"${RCH_DB_USER}\" WITH LOGIN PASSWORD '${RCH_DB_PASSWORD}';"
docker exec -e PGPASSWORD="$POSTGRES_SUPERPASSWORD" common-database \
  psql -U "$POSTGRES_SUPERUSER" -d postgres -v ON_ERROR_STOP=1 <<SQL
SELECT 'CREATE DATABASE "${RCH_DB_NAME}" OWNER "${RCH_DB_USER}"'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '${RCH_DB_NAME}')
\gexec
GRANT ALL PRIVILEGES ON DATABASE "${RCH_DB_NAME}" TO "${RCH_DB_USER}";
SQL

cd "${APP_DIR}"
git fetch origin "${BRANCH}"
git checkout "${BRANCH}"
git pull --ff-only origin "${BRANCH}"

docker compose up -d --build web nginx

docker compose exec -T web env DATABASE_URL="$RCH_DATABASE_URL" python manage.py migrate --noinput

APP_PORT="${RCH_APP_HOST_PORT:-18087}"
for i in {1..50}; do
  if curl -fsS "http://127.0.0.1:${APP_PORT}/healthz/" >/dev/null 2>&1; then
    echo "recruiter-candidate-hub healthy on port ${APP_PORT}"
    exit 0
  fi
  sleep 2
done

echo "Health check failed: http://127.0.0.1:${APP_PORT}/healthz/"
exit 1
