"""
Django settings for Student Micro-Freelancing Platform project.

Generated for local development (Pure Django, no DRF).
"""

from datetime import timedelta
import os
import ssl
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def load_local_env(path):
    """Load simple KEY=VALUE entries without introducing a secrets dependency."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_local_env(BASE_DIR / ".env")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-local-dev-key-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    
    # Local apps
    "accounts",
    'authentication',
    'admin_panel',
    "students",
    "clients",
    "ai",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


# Database
# CockroachDB Cloud is PostgreSQL-compatible. DATABASE_URL is intentionally
# sourced only from the environment/.env and is never embedded in source code.
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

# If a DATABASE_URL is provided (e.g. for CockroachDB), prefer it. Otherwise
# fall back to a local SQLite config for development.
if DATABASE_URL:
    database_url = urlparse(DATABASE_URL)
    if database_url.scheme not in ("postgres", "postgresql") or not database_url.hostname:
        raise RuntimeError("DATABASE_URL must be a valid PostgreSQL connection URL.")

    database_options = parse_qs(database_url.query)
    # Only enforce strict CockroachDB TLS when the URL explicitly requests it.
    # We prefer the system trust store over a repo-local cert so cloud deployments
    # continue to work without a checked-in root CA file.
    sslmode = database_options.get("sslmode", [None])[0]
    ca_cert_env = os.environ.get("PGSSLROOTCERT")

    database_options_payload = {"sslmode": sslmode or "verify-full"}
    system_ca = ssl.get_default_verify_paths().cafile
    if ca_cert_env:
        ca_certificate = Path(ca_cert_env)
        if not ca_certificate.exists():
            raise RuntimeError(
                f"CockroachDB CA certificate was not found at {ca_certificate!s}. "
                "Set PGSSLROOTCERT to the certificate path if you want to override the system trust store."
            )
        database_options_payload["sslrootcert"] = str(ca_certificate)
    elif system_ca:
        database_options_payload["sslrootcert"] = str(system_ca)

    if sslmode in {"verify-full", "verify-ca"} or ca_cert_env:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": database_url.path.lstrip("/"),
                "USER": unquote(database_url.username or ""),
                "PASSWORD": unquote(database_url.password or ""),
                "HOST": database_url.hostname,
                "PORT": str(database_url.port or 26257),
                "OPTIONS": database_options_payload,
            }
        }
    else:
        # DATABASE_URL is present but not explicitly configured for CockroachDB
        # (no sslmode=verify-full and no PGSSLROOTCERT). For local development
        # allow falling back to SQLite rather than raising a RuntimeError.
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }
else:
    # Local development fallback: use SQLite to avoid requiring CockroachDB.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Custom User Model
AUTH_USER_MODEL = 'accounts.User'


# Password validation
# https://docs.djangoproject.com/en/stable/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/stable/howto/static-files/

STATIC_URL = 'static/'


# Default primary key field type
# https://docs.djangoproject.com/en/stable/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# Gemini AI Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
