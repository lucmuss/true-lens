# Recruiter Candidate Hub

Sichere, schnelle Recruiter-Web-App für mehrstufige Kandidaten-Suche, maskierte Profilanzeige, Kategorie-Voting, Credit-System und replikationsfähige Architektur.

## Stack

| Bereich | Technologie |
| --- | --- |
| Backend | Python 3.13, Django 6 |
| Datenbank | PostgreSQL (`psycopg2-binary`, `dj-database-url`) |
| Frontend | Django-Templates + HTMX + Tailwind CSS + Alpine.js |
| Auth / Security | `django-allauth`, Argon2, `django-ratelimit`, JS-Gate-Token, Self-hosted Captcha |
| Payments | Stripe Checkout, Credit-Ledger |
| E-Mail | Resend API oder SMTP (konfigurierbar per `.env`) |
| Monitoring | Sentry/GlitchTip (optional, via `SENTRY_DSN`) |
| Deployment | Gunicorn + WhiteNoise + Nginx + Docker Compose (apps-stack) |
| Tooling | `uv`, `just`, Ruff, Black, MyPy, Pytest |

## Ordnerstruktur

```text
requirements/     Produktanforderungen (Markdown)
src/              Django-Quellcode (apps: accounts, candidates, credits, moderation, replication, security)
tests/            Pytest-Testsuite
testcases/        Browser-Agent-Szenarien für manuelle / KI-basierte Tests
docker/           Dockerfile & Nginx-Konfiguration
deploy/           Apps-Stack-Deployment-Skript
docs/             Zusätzliche Dokumentation
```

## Lokale Entwicklung

### 1. Abhängigkeiten installieren

```bash
uv sync --all-groups
```

### 2. Datenbank starten (lokal)

```bash
docker compose --profile localdb up -d db
```

### 3. Migrationen ausführen

```bash
uv run python manage.py migrate
```

### 4. Initiale Seed-Daten laden

```bash
uv run python manage.py seed_attribute_definitions
uv run python manage.py seed_dev_data
```

`seed_dev_data` erzeugt Recruiter-/Admin-Accounts nur, wenn sie noch nicht existieren.
Passwörter werden standardmäßig zufällig erzeugt und einmalig in der Command-Ausgabe angezeigt.

Für QA kann optional ein gemeinsames Passwort gesetzt werden:

```bash
uv run python manage.py seed_dev_data --password "MyS3cure!Password42"
```

Für produktionsnahe Umgebungen (`DEBUG=False`) ist ein explizites `--force` notwendig:

```bash
uv run python manage.py seed_dev_data --force
```

### 5. Dev-Server starten

```bash
uv run python manage.py runserver 0.0.0.0:8000
```

## Wichtige URLs (lokal)

| URL | Beschreibung |
| --- | --- |
| `/` | Landing Page mit Captcha-Gate |
| `/dashboard/` | Recruiter-Dashboard + Suche |
| `/votes/` | Vote-Historie |
| `/admin-overview/` | Custom Admin-Dashboard (nur Staff) |
| `/admin/` | Django-Admin |
| `/healthz/` | Health-Check Endpoint |
| `/accounts/login/` | Login |
| `/accounts/signup/` | Registrierung |

## Qualitätssicherung

```bash
uv run ruff check .
uv run black --check .
uv run mypy src
uv run pytest -q
```

## Docker (Apps-Stack)

```bash
docker compose up -d --build
curl -fsS http://127.0.0.1:18087/healthz/
```

Deployment-Details: [docs/apps-stack-deploy.md](docs/apps-stack-deploy.md)

## Browser-Tests (KI-Agent)

Vorgefertigte Szenarien unter `testcases/`:

| Szenario | Beschreibung |
| --- | --- |
| `scenario-01-captcha-and-search.md` | Captcha lösen + Profil über 3-Schritt-Suche finden |
| `scenario-02-register-and-vote.md` | Registrierung, E-Mail-Verifikation, Vote abgeben |
| `scenario-03-create-new-profile.md` | Neues Profil anlegen bei 0 Treffern |
| `scenario-04-admin-dashboard.md` | Admin-Dashboard, Moderation, Zugriffskontrolle |

## Sicherheitsarchitektur

- **Captcha-Gate:** Kein Suchzugang ohne gelöstes Captcha (self-hosted, kein externer Anbieter)
- **JS-Gate-Token:** Jeder API-Call benötigt einen zeitgebundenen Token (rotierend)
- **IP-Banning:** Progressive Sperrung bei Verstößen (konfigurierbar via `.env`)
- **Step-Timeout:** Jeder Suchschritt hat serverseitig ein Ablaufdatum
- **Profil-Maskierung:** Nachname, E-Mail, Telefon werden automatisch maskiert
- **Anonymes Voting:** Recruiter-Identität wird auf Wunsch nicht gespeichert
- **Vote-Retention:** Votes laufen nach konfiguriertem Zeitraum ab (Standard: 5 Jahre)

## Konfiguration (`.env`)

Alle kritischen Parameter sind über `.env` steuerbar:

```env
SEARCH_STEP_TIMEOUT_SECONDS=30    # Timer zwischen Suchschritten
PROFILE_VIEW_WINDOW_SECONDS=180   # Anzeigedauer eines gefundenen Profils
VOTE_COOLDOWN_DAYS=3              # Mindestabstand zwischen Votes eines Recruiters
VOTE_RETENTION_YEARS=5            # Ablaufzeit für einzelne Votes
ANON_LOOKUPS_PER_DAY=1            # Max. tägliche Suchen für anonyme Nutzer
CREDIT_PRICE_EUR=1.00             # Preis pro Credit (Stripe)
IP_BAN_THRESHOLD=8                # Strikes bis IP-Sperre
APP_LOG_LEVEL=INFO                # Log-Level (DEBUG/INFO/WARNING)
```

Vollständige Variablen: `.env.example`
