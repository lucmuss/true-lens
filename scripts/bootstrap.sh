#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-run}"

CHECK_ON_START="${EXTERNAL_SERVICES_CHECK_ON_START:-}"
if [ -z "${CHECK_ON_START}" ]; then
  if [ "${DJANGO_ENV:-development}" = "production" ]; then
    CHECK_ON_START="true"
  else
    CHECK_ON_START="false"
  fi
fi

if [ "${CHECK_ON_START}" = "true" ] || [ "${CHECK_ON_START}" = "1" ] || [ "${CHECK_ON_START}" = "yes" ]; then
  python manage.py check_external_services
fi

python manage.py migrate --noinput
python manage.py seed_attribute_definitions || true
python manage.py collectstatic --noinput

if [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  python - <<'PY'
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
django.setup()
from django.contrib.auth import get_user_model

User = get_user_model()
email = os.getenv("DJANGO_SUPERUSER_EMAIL", "").strip().lower()
password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "")
if email and password and not User.objects.filter(email=email).exists():
    User.objects.create_superuser(email=email, password=password)
PY
fi

if [ "$MODE" = "run" ]; then
  exec gunicorn app.wsgi:application -c src/app/gunicorn.conf.py
fi
