# Browser-Agent Testcases

Diese Dateien beschreiben konkrete Szenarien für einen KI-Agenten, der die Web-App mit einem echten Browser testet.

## Setup (vor allen Tests)

```
Basis-URL: http://localhost:18087   (oder die Tailscale-URL)
Test-Recruiter: recruiter1@example.com / Test1234!secure
Admin-User:     admin@example.com   / Test1234!secure
```

Führe vor dem ersten Test aus:
```bash
uv run manage.py seed_dev_data
uv run manage.py seed_attribute_definitions
```

## Szenarien

1. [scenario-01-captcha-and-search.md](scenario-01-captcha-and-search.md)
2. [scenario-02-register-and-vote.md](scenario-02-register-and-vote.md)
3. [scenario-03-create-new-profile.md](scenario-03-create-new-profile.md)
4. [scenario-04-admin-dashboard.md](scenario-04-admin-dashboard.md)
