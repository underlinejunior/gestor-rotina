"""
Django settings for config project.

Development remains convenient by default, while production-sensitive
configuration is controlled by environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv()

# Configuração do django-allauth para o Google
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
            'secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name, default=False):
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
        "sim",
    }


def _env_list(name, default=""):
    value = os.getenv(name, default)

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


# ---------------------------------------------------------------------------
# Ambiente / segurança
# ---------------------------------------------------------------------------

DEBUG = _env_bool("DJANGO_DEBUG", True)

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "").strip()

if not SECRET_KEY:
    if DEBUG:
        # Apenas para desenvolvimento local. Em produção a aplicação se recusa
        # a iniciar sem uma chave fornecida por variável de ambiente.
        SECRET_KEY = "django-insecure-dev-only-change-me"
    else:
        raise RuntimeError(
            "Defina DJANGO_SECRET_KEY no ambiente de produção."
        )

ALLOWED_HOSTS = _env_list(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost",
)

CSRF_TRUSTED_ORIGINS = _env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "",
)

# Segurança de sessão e navegador.
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

# Limites conservadores para uploads.
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 8 * 1024 * 1024
FILE_UPLOAD_PERMISSIONS = 0o640

# Em produção, HTTPS e cookies seguros são obrigatórios.
if not DEBUG:
    SECURE_SSL_REDIRECT = _env_bool(
        "DJANGO_SECURE_SSL_REDIRECT",
        True,
    )
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(
        os.getenv("DJANGO_HSTS_SECONDS", "31536000")
    )
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool(
        "DJANGO_HSTS_INCLUDE_SUBDOMAINS",
        True,
    )
    SECURE_HSTS_PRELOAD = _env_bool(
        "DJANGO_HSTS_PRELOAD",
        False,
    )

    if _env_bool("DJANGO_BEHIND_HTTPS_PROXY", False):
        SECURE_PROXY_SSL_HEADER = (
            "HTTP_X_FORWARDED_PROTO",
            "https",
        )


# ---------------------------------------------------------------------------
# Aplicação
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "usuarios",
    "tarefas",
    "gamificacao",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ---------------------------------------------------------------------------
# Senhas
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ---------------------------------------------------------------------------
# Internacionalização
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Fortaleza"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Arquivos estáticos e mídia privada
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Os arquivos ficam no storage do Django, mas NÃO são expostos por uma rota
# /media/ pública. Evidências fotográficas são entregues por view autenticada.
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ---------------------------------------------------------------------------
# Privacidade / LGPD
# ---------------------------------------------------------------------------

PRIVACY_POLICY_VERSION = os.getenv(
    "PRIVACY_POLICY_VERSION",
    "2026-08-25",
)

# Evidências antigas podem ser removidas por comando agendado, mantendo o
# histórico textual/estatístico da tarefa.
EVIDENCE_RETENTION_DAYS = int(
    os.getenv("EVIDENCE_RETENTION_DAYS", "180")
)

PRIVACY_CONTACT_EMAIL = os.getenv(
    "PRIVACY_CONTACT_EMAIL",
    "",
)


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "usuarios.Usuario"


# ---------------------------------------------------------------------------
# Google OAuth / django-allauth
# ---------------------------------------------------------------------------

from .google_auth_settings import aplicar_google_auth

aplicar_google_auth(globals())
