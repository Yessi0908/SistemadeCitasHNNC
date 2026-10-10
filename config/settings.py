import os
from pathlib import Path
from datetime import timedelta
from django.core.exceptions import ImproperlyConfigured
from django.utils.csp import CSP
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ImproperlyConfigured(
        'Defina SECRET_KEY en el archivo .env (copie desde .env.example).'
    )
DEBUG = os.getenv('DEBUG', 'False') == 'True'
if not DEBUG and (len(SECRET_KEY) < 50 or SECRET_KEY.startswith('cambiar')):
    raise ImproperlyConfigured(
        'En producción SECRET_KEY debe tener al menos 50 caracteres aleatorios. Genérela con: '
        'python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"'
    )
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]
if DEBUG and os.getenv('ALLOWED_HOSTS') is None:
    ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'drf_spectacular',
    'app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.csp.ContentSecurityPolicyMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'hospital_nicolasacruz'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,
    }
}


if os.getenv('USE_SQLITE', 'False') == 'True':
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    {'NAME': 'app.validadores.PalabrasInstitucionalesValidator'},
]

LANGUAGE_CODE = 'es-gt'
TIME_ZONE = 'America/Guatemala'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'app.Usuario'

def _primera_imagen_existente(*nombres):
    for nombre in nombres:
        ruta = BASE_DIR / nombre
        if ruta.exists():
            return ruta
    return BASE_DIR / nombres[0]


# Logo del hospital, o el del Ministerio si aún no hay logo hospitalario
LOGO_RUTA = _primera_imagen_existente('Logohospi.jpg', 'LogoMinisterio.jpg')
# Logo del Ministerio de Salud (encabezado derecho de documentos)
LOGO_SIGSA = BASE_DIR / 'LogoMinisterio.jpg'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_THROTTLE_RATES': {
        'login': os.getenv('LIMITE_LOGIN_IP', '10/min'),
    },
    # Proxies de confianza delante de Django (1 si se usa NGINX). Con 0 se ignora X-Forwarded-For.
    'NUM_PROXIES': int(os.getenv('NUM_PROXIES', 0)),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('JWT_ACCESS_MINUTES', 480))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_DAYS', 1))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'API — Sistema Hospitalario HNNCJ',
    'DESCRIPTION': 'API REST del Hospital Nacional Nicolasa Cruz Jalapa. Use JWT: inicie sesión en POST /api/auth/login/ y pegue el token access en Authorize.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAdminUser'],
    'SERVE_AUTHENTICATION': ['rest_framework.authentication.SessionAuthentication'],
    'COMPONENT_SPLIT_REQUEST': True,
    'SECURITY': [{'BearerAuth': []}],
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'BearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            },
        },
    },
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

CORS_ALLOW_ALL_ORIGINS = DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS: NGINX termina TLS y avisa a Django con la cabecera X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', str(not DEBUG)) == 'True'
# Con certificado autofirmado, HSTS impide "continuar de todos modos": instale el certificado en cada PC.
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', 0 if DEBUG else 31536000))
SECURE_HSTS_INCLUDE_SUBDOMAINS = False

SECURE_CSP = {
    'default-src': [CSP.SELF],
    'script-src': [CSP.SELF, 'https://cdn.jsdelivr.net'],
    'style-src': [CSP.SELF, 'https://cdn.jsdelivr.net'],
    'img-src': [CSP.SELF, 'data:', 'blob:'],
    'font-src': [CSP.SELF, 'https://cdn.jsdelivr.net', 'data:'],
    'connect-src': [CSP.SELF],
    'object-src': [CSP.NONE],
    'base-uri': [CSP.SELF],
    'form-action': [CSP.SELF],
    'frame-ancestors': [CSP.NONE],
}
# Swagger UI y ReDoc (solo administradores) necesitan scripts en línea.
CSP_DOCUMENTACION_API = {
    **SECURE_CSP,
    'script-src': [CSP.SELF, 'https://cdn.jsdelivr.net', CSP.UNSAFE_INLINE],
    'style-src': [CSP.SELF, 'https://cdn.jsdelivr.net', 'https://fonts.googleapis.com', CSP.UNSAFE_INLINE],
    'font-src': [CSP.SELF, 'https://fonts.gstatic.com', 'https://cdn.jsdelivr.net', 'data:'],
    'worker-src': [CSP.SELF, 'blob:'],
}

MAX_INTENTOS_LOGIN = int(os.getenv('MAX_INTENTOS_LOGIN', 5))
BLOQUEO_MINUTOS = int(os.getenv('BLOQUEO_MINUTOS', 15))
CODIGO_HOSPITAL = '263'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'hospital-cache',
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django.security': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
    },
}
