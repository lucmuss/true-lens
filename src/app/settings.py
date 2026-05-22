from __future__ import annotations

import logging
import dj_database_url

from .env import BASE_DIR, env_bool, env_int, env_list, env_str

PROJECT_NAME = env_str("PROJECT_NAME", "TrueLens")
PROJECT_SLUG = env_str("PROJECT_SLUG", "true_lens")
APP_PUBLIC_URL = env_str("APP_PUBLIC_URL", "http://localhost:18087")

DJANGO_ENV = env_str("DJANGO_ENV", "development")
DJANGO_DEBUG = env_bool("DJANGO_DEBUG", False)

SECRET_KEY = env_str("DJANGO_SECRET_KEY", "change-me-in-env")
DEBUG = DJANGO_DEBUG
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", [])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "pwa",
    "modeltranslation",
    "django_htmx",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.github",
    "apps.common",
    "apps.security",
    "apps.accounts",
    "apps.candidates",
    "apps.credits",
    "apps.moderation",
    "apps.replication",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "apps.security.middleware.RequestFingerprintMiddleware",
    "apps.security.middleware.ApiGateMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "src" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.common.context_processors.global_flags",
            ],
        },
    },
]

WSGI_APPLICATION = "app.wsgi.application"
ASGI_APPLICATION = "app.asgi.application"

DATABASE_URL = env_str("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/true_lens")
DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=env_int("DB_CONN_MAX_AGE", 60),
        ssl_require=env_bool("DATABASE_SSL_REQUIRE", False),
    )
}

AUTH_USER_MODEL = "accounts.RecruiterUser"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 12}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "apps.accounts.password_validators.SpecialCharacterValidator"},
]

LANGUAGE_CODE = env_str("DJANGO_LANGUAGE_CODE", "de-de")
TIME_ZONE = env_str("DJANGO_TIME_ZONE", "Europe/Berlin")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "src" / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if env_bool("STATICFILES_USE_MANIFEST", DJANGO_ENV == "production")
            else "whitenoise.storage.CompressedStaticFilesStorage"
        )
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SITE_ID = env_int("DJANGO_SITE_ID", 1)

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_DEFAULT_HTTP_PROTOCOL = env_str("ACCOUNT_DEFAULT_HTTP_PROTOCOL", "https")
ACCOUNT_USER_MODEL_EMAIL_FIELD = "email"
ACCOUNT_ADAPTER = "apps.accounts.adapters.RecruiterAccountAdapter"
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = True
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_MAX_ATTEMPTS = 5
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_TIMEOUT = 900

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    },
    "github": {"SCOPE": ["user:email"]},
}

EMAIL_DELIVERY_MODE = (env_str("EMAIL_DELIVERY_MODE", "") or "").strip().lower()
USE_RESEND = env_bool("USE_RESEND", False)
if not EMAIL_DELIVERY_MODE:
    if USE_RESEND and env_str("RESEND_API_KEY"):
        EMAIL_DELIVERY_MODE = "resend"
    elif DJANGO_ENV == "production":
        EMAIL_DELIVERY_MODE = "smtp"
    else:
        EMAIL_DELIVERY_MODE = "file"

EMAIL_MODE_TO_BACKEND = {
    "smtp": "django.core.mail.backends.smtp.EmailBackend",
    "resend": "apps.accounts.email_backends.ResendEmailBackend",
    "file": "django.core.mail.backends.filebased.EmailBackend",
    "console": "django.core.mail.backends.console.EmailBackend",
    "locmem": "django.core.mail.backends.locmem.EmailBackend",
    "custom": env_str("DJANGO_EMAIL_BACKEND", ""),
}
if EMAIL_DELIVERY_MODE not in EMAIL_MODE_TO_BACKEND:
    raise ValueError("Invalid EMAIL_DELIVERY_MODE")
EMAIL_BACKEND = EMAIL_MODE_TO_BACKEND[EMAIL_DELIVERY_MODE]
EMAIL_FILE_PATH = env_str("EMAIL_FILE_PATH", str(BASE_DIR / "tmp" / "mail"))

EMAIL_HOST = env_str("DJANGO_EMAIL_HOST", "")
EMAIL_PORT = env_int("DJANGO_EMAIL_PORT", 587)
EMAIL_HOST_USER = env_str("DJANGO_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env_str("DJANGO_EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("DJANGO_EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("DJANGO_EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = env_int("DJANGO_EMAIL_TIMEOUT", 15)
DEFAULT_FROM_EMAIL = env_str("DJANGO_DEFAULT_FROM_EMAIL", "noreply@example.local")
SERVER_EMAIL = env_str("DJANGO_SERVER_EMAIL", DEFAULT_FROM_EMAIL)
RESEND_API_KEY = env_str("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = env_str("RESEND_FROM_EMAIL", "")

STRIPE_PUBLIC_KEY = env_str("STRIPE_PUBLIC_KEY", "")
STRIPE_SECRET_KEY = env_str("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = env_str("STRIPE_WEBHOOK_SECRET", "")
STRIPE_DEFAULT_CURRENCY = env_str("STRIPE_DEFAULT_CURRENCY", "eur")
CREDIT_PRICE_EUR = env_str("CREDIT_PRICE_EUR", "1.00")
GOOGLE_PLACES_API_KEY = env_str("GOOGLE_PLACES_API_KEY", "")

SENTRY_DSN = env_str("SENTRY_DSN", "")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment=env_str("SENTRY_ENVIRONMENT", DJANGO_ENV),
        traces_sample_rate=float(env_str("SENTRY_TRACES_SAMPLE_RATE", "0.05")),
        profiles_sample_rate=float(env_str("SENTRY_PROFILES_SAMPLE_RATE", "0.0")),
        send_default_pii=env_bool("SENTRY_SEND_PII", False),
    )

SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", DJANGO_ENV == "production")
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", DJANGO_ENV == "production")
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", DJANGO_ENV == "production")
SECURE_HSTS_SECONDS = env_int("DJANGO_SECURE_HSTS_SECONDS", 31536000 if DJANGO_ENV == "production" else 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", DJANGO_ENV == "production")
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", DJANGO_ENV == "production")
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
# Trust X-Forwarded-Proto from Nginx/Cloudflare reverse proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "landing"

RATELIMIT_ENABLE = env_bool("RATELIMIT_ENABLE", True)
RATELIMIT_DEFAULT_RATE = env_str("RATELIMIT_DEFAULT_RATE", "30/h")
EXTERNAL_SERVICES_CHECK_ON_START = env_str("EXTERNAL_SERVICES_CHECK_ON_START", "")
EXTERNAL_SERVICES_CHECK_STRICT = env_str("EXTERNAL_SERVICES_CHECK_STRICT", "")
EXTERNAL_SERVICES_CHECK_TIMEOUT = env_int("EXTERNAL_SERVICES_CHECK_TIMEOUT", 10)

SEARCH_STEP_TIMEOUT_SECONDS = env_int("SEARCH_STEP_TIMEOUT_SECONDS", 30)
PROFILE_VIEW_WINDOW_SECONDS = env_int("PROFILE_VIEW_WINDOW_SECONDS", 180)
ANON_LOOKUPS_PER_DAY = env_int("ANON_LOOKUPS_PER_DAY", 1)
AUTH_LOOKUPS_PER_DAY = env_int("AUTH_LOOKUPS_PER_DAY", 1)
AUTH_NEW_RECORDS_PER_WEEK = env_int("AUTH_NEW_RECORDS_PER_WEEK", 1)
VOTE_COOLDOWN_DAYS = env_int("VOTE_COOLDOWN_DAYS", 3)
VOTE_RETENTION_YEARS = env_int("VOTE_RETENTION_YEARS", 5)

API_JS_GATE_TTL_SECONDS = env_int("API_JS_GATE_TTL_SECONDS", 120)
API_JS_GATE_ROTATION_SECONDS = env_int("API_JS_GATE_ROTATION_SECONDS", 15)
IP_BAN_THRESHOLD = env_int("IP_BAN_THRESHOLD", 8)
IP_BAN_MINUTES = env_int("IP_BAN_MINUTES", 60)

CANDIDATE_ATTRIBUTE_CONFIG_PATH = env_str(
    "CANDIDATE_ATTRIBUTE_CONFIG_PATH",
    str(BASE_DIR / "src" / "apps" / "candidates" / "attribute_defaults.json"),
)

APP_LOG_LEVEL = env_str("APP_LOG_LEVEL", "DEBUG" if DJANGO_DEBUG else "INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
        "verbose": {
            "format": "[{asctime}] {levelname} {name} pid={process}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": APP_LOG_LEVEL,
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "apps": {"handlers": ["console"], "level": APP_LOG_LEVEL, "propagate": False},
        "apps.security": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps.candidates": {"handlers": ["console"], "level": APP_LOG_LEVEL, "propagate": False},
        "apps.credits": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

REPLICATION_ENABLED = env_bool("REPLICATION_ENABLED", True)
REPLICATION_FACTOR = env_int("REPLICATION_FACTOR", 3)
REPLICATION_SHARED_SECRET = env_str("REPLICATION_SHARED_SECRET", "change-me")
COORDINATOR_DOWN_THRESHOLD_SECONDS = env_int("COORDINATOR_DOWN_THRESHOLD_SECONDS", 3600)

# PWA
PWA_APP_NAME = PROJECT_NAME
PWA_APP_SHORT_NAME = "TrueLens"
PWA_APP_DESCRIPTION = "Secure candidate lookup"
PWA_APP_THEME_COLOR = "#111827"
PWA_APP_BACKGROUND_COLOR = "#f3f4f6"
PWA_APP_DISPLAY = "standalone"
PWA_APP_SCOPE = "/"
PWA_APP_START_URL = "/"
PWA_APP_ICONS = [{"src": "/static/img/icon-192.png", "sizes": "192x192"}]

# Content security policy baseline (header set in middleware)
CSP_SCRIPT_SRC = ["'self'", "https://unpkg.com", "https://cdn.tailwindcss.com"]
CSP_STYLE_SRC = ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com", "https://cdn.tailwindcss.com"]
CSP_FONT_SRC = ["'self'", "https://fonts.gstatic.com"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": env_str("DJANGO_LOG_LEVEL", "INFO"),
    },
}
