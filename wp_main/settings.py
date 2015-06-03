#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Version for welbornprod.com
WPVERSION = '2.2.3'

# file/path (path joining)
import os.path
import sys
SYSVERSION = sys.version

import settings_local
TEMPLATE_DEBUG, DEBUG = settings_local.TEMPLATE_DEBUG, settings_local.DEBUG

# Django messages framework, message-levels
# from django.contrib.messages import constants as message_constants
# MESSAGE_LEVEL = message_constants.ERROR

# DEBUG is in settings_local...

# decide which dirs to use based on hostname.
# determine parent dir for script
SCRIPT_PARENT = os.path.dirname(os.path.realpath(__file__))
# get application base dir
BASE_DIR = os.path.split(SCRIPT_PARENT)[0]
# get parent of application
BASE_PARENT = os.path.split(BASE_DIR)[0]
# File for list of IP's to ban.
SECRET_BAN_FILE = os.path.join(BASE_DIR, 'wp_banned.lst')
# Load secretive settings.
SECRETS = settings_local.SecretSettings(BASE_DIR)
# Server/Site info.
ALLOWED_HOSTS = SECRETS.settings['allowed_hosts']
SECRET_KEY = SECRETS.settings['secret_key']
SITE_URL = SECRETS.site_url
SITE_VERSION = SECRETS.site_info['site_version']
SERVER_LOCATION = SECRETS.site_info['location']

# Static/Media directories.
STATIC_PARENT, STATIC_ROOT = SECRETS.static_parent, SECRETS.static_root
STATIC_URL = SECRETS.static_url
MEDIA_URL = SECRETS.site_info['media_url']
MEDIA_ROOT = os.path.join(STATIC_ROOT, "media")

# Email info.
EMAIL_HOST = SECRETS.settings['email']['host']
EMAIL_HOST_USER = SECRETS.settings['email']['user']
EMAIL_HOST_PASSWORD = SECRETS.email_pw
EMAIL_FROM_EMAIL = SECRETS.settings['email']['from_email']
SERVER_EMAIL = SECRETS.settings['email']['email']

# Database info (filled in with settings_local)
DATABASES = {'default': SECRETS.database}

# Cache Settings
CACHES = {
    'cache_db': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'welbornprod_cache',
    },

    'cache_dummy': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
# Set which cache to use.
if 'webapps' in BASE_PARENT and ('test' not in BASE_PARENT):
    # Use db cache for live site.
    CACHES['default'] = CACHES['cache_db']
else:
    # Use dummy cache for local development, and test site.
    CACHES['default'] = CACHES['cache_dummy']

# main app (location of settings.py)
MAIN_DIR = os.path.join(BASE_DIR, "wp_main")
TEMPLATES_BASE = os.path.join(MAIN_DIR, "templates")

# IP's debug_toolbar should be shown to.
INTERNAL_IPS = tuple(SECRETS.settings.get('internal_ips', []))

# Admin info
ADMINS = (('Christopher Welborn', 'cj@welbornprod.com'), )
MANAGERS = ADMINS


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': (
            TEMPLATES_BASE,
            os.path.join(TEMPLATES_BASE, 'admin/templates'),
            os.path.join(TEMPLATES_BASE, 'admindoc/templates'),
            # Include project pages as possible templates.
            os.path.join(BASE_DIR, 'projects/static/html'),
            # Include blog post html as possible templates.
            os.path.join(BASE_DIR, 'blogger/static/html'),
        ),
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],

        },
    }
]

MIDDLEWARE_CLASSES = (
    # WelbornProd IP bans..
    'middleware.requests.WpBanIpMiddleware',
    # Standard middleware chain.
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # django debug tools
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # special user-agent middleware...
    'wp_user_agents.middleware.UserAgentMiddleware',

)

ROOT_URLCONF = 'wp_main.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'wp_main.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # admin enabled:
    'django.contrib.admin',
    'django.contrib.admindocs',

    # django debug tools (for test-site and local development)
    'debug_toolbar',
    'django_extensions',

    # singleton configuration for home app.
    'solo',

    # for making get_user_agent(request) available.
    'wp_user_agents',
    # local apps
    'wp_main',  # contains global template tags (wp_tags)
    'apps',  # handles urls for all sub-apps.
    'apps.phonewords',
    'apps.paste',
    'blogger',
    'downloads',
    'home',
    'img',
    'misc',
    'projects',
    'sandbox',  # private sandbox for testing code or features.
    'searcher',
    'stats',  # provides stats for all models.
    'viewer',
)

# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': '\n'.join((
                '%(asctime)s - [%(levelname)s] %(name)s.%(funcName)s',
                '  %(filename)s:(%(lineno)d):',
                '      %(message)s\n'))
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': ('DEBUG' if DEBUG else 'ERROR'),
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(BASE_DIR, 'welbornprod.log'),
            'maxBytes': 2097152,
            'backupCount': 0
        }
    },
    'loggers': {
        'wp': {
            'handlers': ['file'],
            'level': ('DEBUG' if DEBUG else 'ERROR'),
            'propogate': True
        }
    }
}


# Only turn error emails on with the remote server
# They are driving me nuts when I'm experimenting locally and DEBUG == False.
if SERVER_LOCATION == 'remote':
    LOGGING['handlers']['mail_admins'] = {
        'level': 'ERROR',
        'filters': ['require_debug_false'],
        'class': 'django.utils.log.AdminEmailHandler'
    }
    LOGGING['loggers']['django.request'] = {
        'handlers': ['mail_admins'],
        'level': 'ERROR',
        'propagate': True,

    }

# Disable redirect panel (per new debug_toolbar method.)
DEBUG_TOOLBAR_CONFIG = {
    'DISABLE_PANELS': {'debug_toolbar.panels.redirects.RedirectsPanel'}
}
# Don't automatically adjust project settings based on DEBUG!
DEBUG_TOOLBAR_PATCH_SETTINGS = False

# default login url
# (regex for wp_main.urls, put here to avoid future mismatches)
LOGIN_URL = "/login"
LOGIN_URL_REGEX = "^login/?.+"

# default page to visit after login (if 'next url' is not specified)
LOGIN_REDIRECT_URL = "/"

TEST_RUNNER = 'django.test.runner.DiscoverRunner'
