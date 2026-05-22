# Apps-Stack Deployment

Project: TrueLens (`https://github.com/lucmuss/true_lens`)

Deploy target: shared postgres in `/srv/docker/apps-stack`.

## Required apps-stack env keys
In `/srv/docker/apps-stack/.env`:
- `RCH_DB_NAME`
- `RCH_DB_USER`
- `RCH_DB_PASSWORD`
- `RCH_APP_HOST_PORT` (optional, default 18087)
- `POSTGRES_SUPERUSER`
- `POSTGRES_SUPERPASSWORD`

## Deploy command
```bash
cd /srv/projects/web/recruiter-candidate-hub
bash deploy/deploy.sh
```

## What deploy does
1. Ensures shared postgres is running.
2. Waits for `pg_isready`.
3. Idempotently creates/updates role + database + grants.
4. Pulls latest `main`.
5. Rebuilds app containers.
6. Runs migrations.
7. Verifies `/healthz/`.

## Runtime verification
```bash
cd /srv/projects/web/recruiter-candidate-hub
docker compose ps
curl -fsS http://127.0.0.1:${RCH_APP_HOST_PORT:-18087}/healthz/
```
