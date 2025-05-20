"""Top level Django application settings."""

import importlib.metadata
import os
import sys
from datetime import timedelta
from pathlib import Path

import environ
from django.core.management.utils import get_random_secret_key
from jinja2 import StrictUndefined

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Application metadata

dist = importlib.metadata.distribution('keystone-api')
VERSION = dist.metadata['version']
SUMMARY = dist.metadata['summary']

# Developer settings

env = environ.Env()
DEBUG = env.bool('DEBUG', False)
FIXTURE_DIRS = [BASE_DIR / 'fixtures']

# Core security settings

_trusted_local = [
    "http://localhost:80",
    "https://localhost:443",
    "http://localhost:4200",
    "http://localhost:8000",
    "http://127.0.0.1:80",
    "https://127.0.0.1:443",
    "http://127.0.0.1:4200",
    "http://127.0.0.1:8000",
]

SECRET_KEY = os.environ.get('SECURE_SECRET_KEY', get_random_secret_key())
ALLOWED_HOSTS = env.list("SECURE_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

_SECURE_SSL_TOKENS = env.bool("SECURE_SSL_TOKENS", False)
SESSION_COOKIE_SECURE = _SECURE_SSL_TOKENS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = env.int("SECURE_SESSION_AGE", timedelta(days=14).total_seconds())

CSRF_TRUSTED_ORIGINS = env.list("SECURE_CSRF_ORIGINS", default=_trusted_local)
CSRF_COOKIE_SECURE = _SECURE_SSL_TOKENS
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", False)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_SUBDOMAINS", False)

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = env.list("SECURE_ALLOWED_ORIGINS", default=_trusted_local)

ALLOWED_FILE_TYPES = [
    # Documents
    "application/pdf",
    "application/rtf",
    "application/msword",  # .doc
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.oasis.opendocument.text",  # .odt
    "application/x-latex",  # .latex
    "application/x-tex",  # .tex

    # Spreadsheets
    "application/vnd.ms-excel",  # .xls
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.oasis.opendocument.spreadsheet",  # .ods

    # Presentations
    "application/vnd.ms-powerpoint",  # .ppt
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx

    # Plain and structured text
    "text/plain",  # .txt
    "text/markdown",  # .md
    "text/richtext",  # .rtx
    "text/csv",  # .csv

    # Images
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/svg+xml",
    "image/tiff",
    "image/bmp"
]

# App Configuration

ROOT_URLCONF = 'main.urls'
LOGIN_REDIRECT_URL = '/'
SITE_ID = 1

INSTALLED_APPS = [
    'jazzmin',
    'auditlog',
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'health_check',
    'health_check.db',
    'health_check.storage',
    'health_check.contrib.migrations',
    'health_check.contrib.celery',
    'health_check.contrib.celery_ping',
    'health_check.contrib.redis',
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'django_celery_beat',
    'django_celery_results',
    'django_filters',
    'django_prometheus',
    'drf_spectacular',
    'plugins',
    'apps.admin_utils',
    'apps.allocations',
    'apps.authentication',
    'apps.health',
    'apps.logging',
    'apps.notifications',
    'apps.openapi',
    'apps.research_products',
    'apps.scheduler',
    'apps.users',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'apps.logging.middleware.LogRequestMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

TEMPLATES = [
    {  # The default backend required by Django builtins (e.g., the admin)
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
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
    {  # Jinja2 backend used when rendering user notifications
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        'APP_DIRS': True,
        "OPTIONS": {
            "undefined": StrictUndefined,
        },
    },
]

# Base styling for the Admin UI

USE_THOUSAND_SEPARATOR = True
JAZZMIN_SETTINGS = {
    "site_title": "Keystone",
    "site_header": "Keystone",
    "site_brand": "Keystone",
    "hide_apps": ["sites", "auth", "authtoken", "token_blacklist"],
    "order_with_respect_to": [
        "users",
        "allocations",
        "research_products",
        "sites"
    ],
    "icons": {},
    "login_logo": "fake/file/path.jpg",  # Missing file path hides the logo
}

# REST API settings

REST_FRAMEWORK = {
    'SEARCH_PARAM': '_search',
    'ORDERING_PARAM': '_order',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': env.str('API_THROTTLE_ANON', '120/min'),
        'user': env.str('API_THROTTLE_USER', '300/min')
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_FILTER_BACKENDS': (
        'plugins.filter.AdvancedFilterBackend',
        'rest_framework.filters.OrderingFilter',
        'rest_framework.filters.SearchFilter'
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Audit logging

AUDITLOG_CID_HEADER = "X-KEYSTONE-CID"  # Use uppercase and dashes

# Customize the generation of OpenAPI specifications

SPECTACULAR_SETTINGS = {
    'TITLE': f'Keystone API',
    'DESCRIPTION': SUMMARY,
    'VERSION': VERSION,
    'SERVE_INCLUDE_SCHEMA': False,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAuthenticated'],
    'ENUM_NAME_OVERRIDES': {
        'RequestStatusChoices': 'apps.allocations.models.AllocationRequest.StatusChoices',
        'ReviewStatusChoices': 'apps.allocations.models.AllocationReview.StatusChoices',
    }
}

# Redis backend and Celery scheduler

_redis_host = env.url('REDIS_HOST', '127.0.0.1').geturl()
_redis_port = env.int('REDIS_PORT', 6379)
_redis_db = env.int('REDIS_DB', 0)
_redis_pass = env.str('REDIS_PASSWORD', '')

REDIS_URL = f'redis://:{_redis_pass}@{_redis_host}:{_redis_port}'

CELERY_BROKER_URL = REDIS_URL + f'/{_redis_db}'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_RESULT_EXTENDED = True

# Email server

EMAIL_FROM_ADDRESS = env.str('EMAIL_FROM_ADDRESS', 'noreply@keystone.bot')
if _email_path := env.get_value('DEBUG_EMAIL_DIR', default=None):
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = _email_path

else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = env.str('EMAIL_HOST', 'localhost')
    EMAIL_PORT = env.int('EMAIL_PORT', 25)
    EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = env.str('your_email_password', '')
    EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', False)

# Database

DATABASES = dict()
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

_db_name = env.str('DB_NAME', 'keystone')
if env.bool('DB_POSTGRES_ENABLE', False):
    DATABASES['default'] = {
        'ENGINE': 'django_prometheus.db.backends.postgresql',
        'NAME': _db_name,
        'USER': env.str('DB_USER', ''),
        'PASSWORD': env.str('DB_PASSWORD', ''),
        'HOST': env.str('DB_HOST', 'localhost'),
        'PORT': env.str('DB_PORT', '5432'),
    }

else:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / f'{_db_name}.db',
        'timeout': 30,
        'PRAGMA': {
            'journal_mode': 'wal',
        }
    }

# Authentication

AUTH_USER_MODEL = "users.User"
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

PURGE_REMOVED_LDAP_USERS = env.bool("AUTH_LDAP_PURGE_REMOVED", False)
if AUTH_LDAP_SERVER_URI := env.url("AUTH_LDAP_SERVER_URI", "").geturl():
    import ldap
    from django_auth_ldap.config import LDAPSearch

    AUTHENTICATION_BACKENDS.append("django_auth_ldap.backend.LDAPBackend")

    AUTH_LDAP_ALWAYS_UPDATE_USER = True
    AUTH_LDAP_START_TLS = env.bool("AUTH_LDAP_START_TLS", True)
    AUTH_LDAP_BIND_DN = env.str("AUTH_LDAP_BIND_DN", "")
    AUTH_LDAP_BIND_PASSWORD = env.str("AUTH_LDAP_BIND_PASSWORD", "")
    AUTH_LDAP_USER_ATTR_MAP = env.dict('AUTH_LDAP_ATTR_MAP', default=dict())
    AUTH_LDAP_USER_SEARCH = LDAPSearch(
        env.str("AUTH_LDAP_USER_SEARCH", ""),
        ldap.SCOPE_SUBTREE,
        "(uid=%(user)s)"
    )

    if env.bool('AUTH_LDAP_REQUIRE_CERT', False):
        AUTH_LDAP_GLOBAL_OPTIONS = {ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Static file handling (CSS, JavaScript, Images)

MAX_FILE_SIZE = env.int('CONFIG_UPLOAD_SIZE', 2.5 * 1024 * 1024)  # 2.5 MB

STATIC_URL = '/static/'
STATIC_ROOT = Path(env.path('CONFIG_STATIC_DIR', BASE_DIR / 'static_files'))
STATIC_ROOT.mkdir(parents=True, exist_ok=True)

MEDIA_URL = '/media/'
MEDIA_ROOT = Path(env.path('CONFIG_UPLOAD_DIR', BASE_DIR / 'media'))
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

# Timezones

USE_TZ = True
CELERY_ENABLE_UTC = True
DJANGO_CELERY_BEAT_TZ_AWARE = True
TIME_ZONE = env.str('CONFIG_TIMEZONE', 'UTC')

# Logging

CONFIG_LOG_RETENTION = env.int('CONFIG_LOG_RETENTION', timedelta(days=14).total_seconds())
CONFIG_REQUEST_RETENTION = env.int('CONFIG_REQUEST_RETENTION', timedelta(days=14).total_seconds())

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "db": {
            "class": "apps.logging.handlers.DBHandler",
        }
    },
    "loggers": {
        "": {
            "level": env.str('CONFIG_LOG_LEVEL', 'WARNING'),
            "handlers": ["db"],
        },
        "apps": {
            "level": env.str('CONFIG_LOG_LEVEL', 'WARNING'),
            "handlers": ["db"],
            "propagate": False,
        },
    }
}
