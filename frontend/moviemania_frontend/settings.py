import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,django_frontend', cast=lambda v: [s.strip() for s in v.split(',')])


DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

LOCAL_APPS = [
    'apps.movies',
    'apps.users',
    'apps.recommendations',
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # CSRF réactivé
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'moviemania_frontend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'moviemania_frontend.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('MYSQL_DATABASE', default='moviemania'),
        'USER': config('MYSQL_USER', default='moviemania'),
        'PASSWORD': config('MYSQL_PASSWORD', default='moviemania_password_2024'),
        'HOST': config('MYSQL_SERVER', default='mariadb'),
        'PORT': config('MYSQL_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

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
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

USERS_API_URL = config('USERS_API_URL', default='http://users_api:8000')
RECOMMENDATIONS_API_URL = config('RECOMMENDATIONS_API_URL', default='http://recommendations_api:8000')

SESSION_COOKIE_AGE = 3600  # 1 heure
SESSION_SAVE_EVERY_REQUEST = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

CSRF_COOKIE_SECURE = True  # CSRF cookie seulement en HTTPS
CSRF_COOKIE_HTTPONLY = False  # CSRF cookie accessible via JavaScript pour AJAX
CSRF_COOKIE_SAMESITE = 'Strict'  # Protection CSRF stricte
CSRF_TRUSTED_ORIGINS = [
    'https://localhost',
    'https://127.0.0.1',
]

SESSION_COOKIE_SECURE = True  # Session cookie seulement en HTTPS
SESSION_COOKIE_HTTPONLY = True  # Session cookie non accessible via JavaScript
SESSION_COOKIE_SAMESITE = 'Strict'  # Protection session stricte

if not DEBUG:
    SECURE_SSL_REDIRECT = True  # Redirection automatique vers HTTPS
    SECURE_HSTS_SECONDS = 31536000  # HSTS pour 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_SSL_REDIRECT = False  # Pas de redirection en développement
    SECURE_HSTS_SECONDS = 0  # Pas de HSTS en développement

SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
