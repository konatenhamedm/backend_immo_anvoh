"""
Django settings pour le projet THIEBBRO IMMO.
Clean Architecture Backend avec PostgreSQL & Django REST Framework.
"""

import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Charger le fichier .env
load_dotenv(BASE_DIR / ".env")

# Ajouter le répertoire apps au sys.path
sys.path.insert(0, str(BASE_DIR / "apps"))

# DEBUG désactivé par défaut : il faut l'activer explicitement (DEBUG=True dans .env) en développement.
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        from django.core.exceptions import ImproperlyConfigured

        raise ImproperlyConfigured("SECRET_KEY doit être définie en production (variable d'environnement).")
    SECRET_KEY = "django-insecure-dev-only-key"

ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]

# Modèle Utilisateur personnalisé (Clean Architecture)
AUTH_USER_MODEL = "users.User"

# Applications installées
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Dépendances Tierces
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    # Modules Métier (Bounded Contexts)
    "apps.users",
    "apps.properties",
    "apps.simulators",
    "apps.crm",
    "apps.accreditation",
    "apps.messaging",
    "apps.investments",
    "apps.rentals",
    "apps.notifications",
    "apps.analytics",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # Obligatoirement avant CommonMiddleware
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

# Configuration Base de données (PostgreSQL par défaut avec fallback SQLite pour dev local immédiat)
db_engine = os.getenv("DB_ENGINE", "django.db.backends.postgresql")
db_name = os.getenv("DB_NAME", "thiebbro_immo_db")
db_user = os.getenv("DB_USER", "postgres")
db_password = os.getenv("DB_PASSWORD", "postgres")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "3306" if db_engine.endswith("mysql") else "5432")

if db_engine == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": db_engine,
            "NAME": db_name,
            "USER": db_user,
            "PASSWORD": db_password,
            "HOST": db_host,
            "PORT": db_port,
            # Connexions réutilisées (utile avec une base distante) ; 0 = une connexion par requête.
            "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "0")),
        }
    }
    # Base PostgreSQL distante (Neon, Supabase…) : le chiffrement est obligatoire (DB_SSLMODE=require).
    # connect_timeout : si le serveur n'est pas joignable (port bloqué), on échoue en quelques secondes au lieu de rester suspendu.
    if db_engine.endswith("postgresql"):
        DATABASES["default"]["OPTIONS"] = {"connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10"))}
        if os.getenv("DB_SSLMODE"):
            DATABASES["default"]["OPTIONS"]["sslmode"] = os.environ["DB_SSLMODE"]
    # MySQL / MariaDB (o2switch) : jeu de caractères complet (accents, emojis) et mode strict.
    if db_engine.endswith("mysql"):
        try:
            import MySQLdb  # noqa: F401  (mysqlclient, si installé)
        except ImportError:
            # Hébergement mutualisé sans compilateur : PyMySQL (100 % Python) se substitue à mysqlclient.
            import pymysql

            pymysql.install_as_MySQLdb()
        DATABASES["default"]["OPTIONS"] = {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
        }
        # Contrainte d'unicité conditionnelle (notifications) non supportée : la déduplication est faite dans le code.
        SILENCED_SYSTEM_CHECKS = ["models.W036"]

# Validation des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalisation
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Abidjan"
USE_I18N = True
USE_TZ = True

# Fichiers statiques et médias (Photos de biens, PDF, documents)
# En hébergement mutualisé (cPanel), ces dossiers doivent se trouver dans la racine web du site pour être servis par Apache :
# STATIC_ROOT / MEDIA_ROOT surchargent alors les valeurs par défaut (voir DEPLOIEMENT_O2SWITCH.md).
STATIC_URL = "/static/"
STATIC_ROOT = Path(os.getenv("STATIC_ROOT", BASE_DIR / "staticfiles"))

MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", BASE_DIR / "media"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "config.pagination.StandardPagination",
    "PAGE_SIZE": 12,
    # Toute route est protégée par défaut ; les routes publiques le déclarent explicitement (AllowAny).
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "120/min",
        "user": "600/min",
        "auth": os.getenv("AUTH_THROTTLE_RATE", "20/min"),  # connexion, inscription, changement de mot de passe
        "analytics": "240/min",  # envoi des événements de mesure par le navigateur (lots de 20 au plus)
        "public_forms": "10/min",  # formulaires publics (contact, WhatsApp, visite, « Trouver mon bien »)
    },
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "60"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Swagger / OpenAPI 3 (drf-spectacular)
SPECTACULAR_SETTINGS = {
    "TITLE": "THIEBBRO IMMO API",
    "DESCRIPTION": "API REST PropTech de la plateforme immobilière ivoirienne (Clean Architecture).",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "config.openapi.mark_response_fields_required",
    ],
    # Noms explicites pour les énumérations (sinon StatusCb7Enum… dans les types générés côté front).
    "ENUM_NAME_OVERRIDES": {
        "PropertyStatusEnum": "apps.properties.infrastructure.models.PropertyStatus",
        "VerificationStatusEnum": "apps.properties.infrastructure.models.VerificationStatus",
        "VisitStatusEnum": "apps.crm.infrastructure.models.VisitRequestStatus",
        "AccreditationStatusEnum": "apps.accreditation.infrastructure.models.AccreditationStatus",
        "DocumentStatusEnum": "apps.accreditation.infrastructure.models.DocumentStatus",
        "PlanStatusEnum": "apps.investments.infrastructure.models.PlanStatus",
        "SubscriptionStatusEnum": "apps.investments.infrastructure.models.SubscriptionStatus",
        "EntryStatusEnum": "apps.investments.infrastructure.models.EntryStatus",
        "RentStatusEnum": "apps.rentals.infrastructure.models.RentStatus",
        "PayoutStatusEnum": "apps.rentals.infrastructure.models.PayoutStatus",
        "IdentityStatusEnum": "apps.users.infrastructure.models.IdentityStatus",
        "UserRoleEnum": "apps.users.infrastructure.models.UserRole",
        "AcquisitionChannelEnum": "apps.crm.infrastructure.models.AcquisitionChannel",
        "ProjectDocumentKindEnum": "apps.properties.infrastructure.models.ProjectDocumentKind",
        "NotificationKindEnum": "apps.notifications.domain.kinds.KIND_CHOICES",
    },
}

# CORS : uniquement les origines déclarées (site Next.js, back-office). Plus d'ouverture totale, même en DEBUG.
cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

# Origines de confiance pour les formulaires POST (connexion à /admin/ en HTTPS), ex. https://api.thiebbro.ci
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

# Sécurité HTTP en production
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = ["rest_framework.renderers.JSONRenderer"]


# --- Notifications (e-mail) et relances -------------------------------------------------------------------------------
# En développement, les e-mails s'affichent dans la console du serveur. En production : EMAIL_HOST, EMAIL_HOST_USER…
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_FILE_PATH = os.getenv("EMAIL_FILE_PATH", "")  # avec EMAIL_BACKEND=…filebased.EmailBackend (tests de bout en bout)
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False").lower() in (
    "true",
    "1",
    "yes",
)  # port 465 ; exclusif avec TLS (587)
EMAIL_TIMEOUT = 10  # secondes : un serveur de messagerie lent ne doit pas bloquer une requête
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "THIEBBRO IMMO <no-reply@thiebbro.ci>")
# Adresse publique du site, utilisée pour les liens dans les e-mails.
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3100")

# Connexion avec Google : identifiant client OAuth « Web » (Google Cloud Console). Vide = fonction désactivée.
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
# Comptes équipe / notaire autorisés à se connecter avec Google (adresses séparées par des virgules). Par défaut : aucun.
GOOGLE_STAFF_EMAILS = [e.strip().lower() for e in os.getenv("GOOGLE_STAFF_EMAILS", "").split(",") if e.strip()]
