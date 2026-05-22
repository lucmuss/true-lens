# Recruiter Candidate Hub

Secure, fast recruiter web app for multi-step candidate lookup, masked profile reveal, voting, credits, and replication-ready operations.

## Stack
- Backend: Python 3.x, Django 6
- DB: PostgreSQL (`psycopg2-binary`, `dj-database-url`)
- Frontend: Django templates + HTMX + Tailwind + Alpine.js
- Auth/Security: `django-allauth`, Argon2, `django-ratelimit`, JS gate token, captcha gate
- Payments/Integrations: Stripe, Resend/SMTP, Sentry
- Extras: WeasyPrint, `django-pwa`, `django-modeltranslation`
- Runtime: Gunicorn + WhiteNoise + Nginx + Docker Compose
- Tooling: `uv`, `just`, Ruff, Black, Flake8, MyPy, Pytest

## Repository layout
- `requirements/`: structured product + architecture requirements
- `src/`: Django code
- `tests/`: pytest suites
- `docker/`: Dockerfile and nginx config
- `deploy/`: apps-stack deployment script
- `output/gui-screenshots/`: required UI screenshots

## Local development
1. Install deps:
```bash
uv sync --all-groups
```
2. Optional local DB profile (or use your own Postgres URL in `.env`):
```bash
docker compose --profile localdb up -d db
```
3. Migrate:
```bash
uv run python manage.py migrate
```
4. Seed default candidate attributes:
```bash
uv run python manage.py seed_attribute_definitions
```
5. Run:
```bash
uv run python manage.py runserver 0.0.0.0:8000
```

## Quality gates
```bash
uv run ruff check .
uv run black --check .
uv run flake8 src tests
uv run mypy src
uv run pytest -q
```

## Docker runtime
```bash
docker compose up -d --build
curl -fsS http://127.0.0.1:18087/healthz/
```

## Apps-stack deployment
Use:
```bash
bash deploy/deploy.sh
```
See [docs/apps-stack-deploy.md](docs/apps-stack-deploy.md) for required `/srv/docker/apps-stack/.env` keys.
