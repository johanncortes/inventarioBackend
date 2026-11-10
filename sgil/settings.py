"""
Configuración del proyecto SGIL (Sistema de Gestión de Inventario de Laboratorios).

Aquí se registran las apps, la base de datos, el idioma y la configuración de
Django REST Framework. Es un archivo compartido: cada integrante agrega lo suyo
dentro de sus marcadores (# ===== Área (Nombre) ===== ... # ===== Fin ... =====).
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-7hc21+8r@d&9-@kot(^gu4!kp1%kzk&@zj^pmlt47wic#@41zm'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Paquetes externos (están en requirements.txt)
    'rest_framework',             # Django REST Framework: serializers, vistas y API navegable
    'rest_framework.authtoken',   # crea la tabla de tokens para /api/token/ (Unidad IV)
    'django_filters',             # filtros con formulario en la API navegable

    # ===== Usuarios e inventario (Johann) =====
    'usuarios',
    'inventario',
    # ===== Fin Usuarios e inventario (Johann) =====

    # ===== Reservas (Martín) =====
    # ===== Fin Reservas (Martín) =====

    # ===== Incidencias (Diego) =====
    'incidencias',
    # ===== Fin Incidencias (Diego) =====
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

ROOT_URLCONF = 'sgil.urls'

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

WSGI_APPLICATION = 'sgil.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Base de datos MySQL. Cada integrante la crea en su computador con bd/crear_bd.sql.
# El ENGINE es el de MySQL, pero por debajo se conecta con PyMySQL
# (ver sgil/__init__.py), así no hay que compilar nada en Windows ni en macOS.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sgil_db',
        'USER': 'sgil',
        'PASSWORD': 'sgil123',   # solo es la base local de cada uno
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            # utf8mb4 = el mismo juego de caracteres de la base (tildes, ñ, etc.)
            'charset': 'utf8mb4',
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

# Español de Chile: los mensajes de error de Django y DRF salen en español.
LANGUAGE_CODE = 'es-cl'

# Hora de Chile. Django guarda las fechas en UTC en la base (USE_TZ = True)
# y las convierte a esta zona horaria al mostrarlas.
TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Configuración de Django REST Framework (se aplica a todas las vistas de la API).
REST_FRAMEWORK = {
    # Cómo sabe la API quién es el usuario:
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Sesión: es la que usa el botón "Log in" de la API navegable.
        'rest_framework.authentication.SessionAuthentication',
        # Token: el front (Unidad IV) manda "Authorization: Token <clave>".
        'rest_framework.authentication.TokenAuthentication',
    ],
    # Por defecto, todo pide haber iniciado sesión (sin sesión → 403).
    # Cada vista agrega después sus permisos por rol (usuarios/permisos.py).
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # Filtrar (?categoria=2), buscar (?search=) y ordenar (?ordering=) en los listados.
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    # Paginación por número de página (?page=2).
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 9,  # igual que el inventario del front (CA-01.3)
}
