from datetime import timedelta
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

# Local development settings shared by the team.
DEBUG = True
SECRET_KEY = 'ticket-system-local-development-secret-key'
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

CORS_ALLOWED_ORIGINS = [
	origin.strip()
	for origin in os.environ.get(
		'CORS_ALLOWED_ORIGINS',
		'http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174',
	).split(',')
	if origin.strip()
]

CORS_ALLOW_CREDENTIALS = False

INSTALLED_APPS = [
	'django.contrib.admin',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'django.contrib.staticfiles',
	'rest_framework',
	'rest_framework_simplejwt',
	'assignments',
    'customers',
    'technicians',
    'tickets',
	'authentication',
]

MIDDLEWARE = [
	'django.middleware.security.SecurityMiddleware',
	'ticket_system.cors.CorsMiddleware',
	'django.contrib.sessions.middleware.SessionMiddleware',
	'django.middleware.common.CommonMiddleware',
	'django.middleware.csrf.CsrfViewMiddleware',
	'django.contrib.auth.middleware.AuthenticationMiddleware',
	'django.contrib.messages.middleware.MessageMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ticket_system.urls'

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [],
		'APP_DIRS': True,
		'OPTIONS': {
			'context_processors': [
				'django.template.context_processors.request',
				'django.contrib.auth.context_processors.auth',
				'django.contrib.messages.context_processors.messages',
			],
		},
	},
]

WSGI_APPLICATION = 'ticket_system.wsgi.application'

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql',
		'NAME': os.environ.get('DB_NAME', 'ticket_system'),
		'USER': os.environ.get('DB_USER', 'postgres'),
		'PASSWORD': os.environ.get('DB_PASSWORD', 'Baccaymoy123005'),
		'HOST': os.environ.get('DB_HOST', 'localhost'),
		'PORT': os.environ.get('DB_PORT', '5432'),
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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

AUTH_USER_MODEL = 'authentication.Authentication'

REST_FRAMEWORK = {

	'DEFAULT_AUTHENTICATION_CLASSES':(
		'rest_framework_simplejwt.authentication.JWTAuthentication',
	),
	'DEFAULT_PERMISSION_CLASSES':(
		'rest_framework.permissions.IsAuthenticated',
	)
}

SIMPLE_JWT = {
    'CHECK_REVOKE_TOKEN': True,
	'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
	'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
	'AUTH_HEADER_TYPES': ['Bearer'],
}
