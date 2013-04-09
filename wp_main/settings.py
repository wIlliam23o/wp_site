#!/usr/bin/python2.6
# -*- coding: utf-8 -*-

# Django settings for wp_main project.

# file/path (path joining)
import os.path

DEBUG = True
TEMPLATE_DEBUG = True

# decide which dirs to use based on hostname.
# determine parent dir for script
SCRIPT_PARENT = os.path.dirname(os.path.realpath(__file__))
# get application base dir
BASE_DIR = os.path.split(SCRIPT_PARENT)[0]
# get parent of application
BASE_PARENT = os.path.split(BASE_DIR)[0]

# automatic settings for debug mode.
#import socket
#shostname = socket.gethostname()
#del socket

if "webapps" in BASE_PARENT:
    # live site directories
    #BASE_PARENT = "/home/cjwelborn/webapps/wp_site/"
    #BASE_DIR = os.path.join(BASE_PARENT, "wp_site")
    STATIC_PARENT = BASE_PARENT
    MEDIA_URL = "http://welbornprod.com/media/"
else:
    # local development directories
    #BASE_PARENT = "/home/cj/workspace/welbornprod"
    #BASE_DIR = os.path.join(BASE_PARENT, "wp_main")
    STATIC_PARENT= "/var/www/"
    MEDIA_URL = "http://127.0.0.1/media/"

# Static/Media directories. 
STATIC_ROOT = os.path.join(STATIC_PARENT, "static")
MEDIA_ROOT = os.path.join(STATIC_PARENT, "media")
    
# URL prefix for static files.
STATIC_URL = '/static/'
# main app (location of settings.py)
MAIN_DIR = os.path.join(BASE_DIR, "wp_main")
TEMPLATES_BASE = os.path.join(MAIN_DIR, "templates")

# IP's debug_toolbar should be shown to.
INTERNAL_IPS = ('127.0.0.1',
                # webfactional?
                '10.80.234.144',
                )

# Django's new security setting?
ALLOWED_HOSTS = ['*']


ADMINS = (
    ('Christopher Welborn', 'cj@welbornprod.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',       # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(BASE_DIR, 'wp_main.db'), # Or path to database file if using sqlite3.
        'USER': '',                                   # Not used with sqlite3.
        'PASSWORD': '',                               # Not used with sqlite3.
        'HOST': '',                                   # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                                   # Set to empty string for default. Not used with sqlite3.
    }
}

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
USE_TZ = True

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

# SECRET_KEY SETTINGS
NONSECRET_KEY = '2h&amp;yk)@#2v&amp;ja6nl-3_!!vbp)$3xy*h5pi1el4x#rx6djv-6(z'
# Make this unique, and don't share it with anybody.
SECRET_KEY_FILE = os.path.join(BASE_DIR, "secretkey.txt")
if os.path.isfile(SECRET_KEY_FILE):
    try:
        with open(SECRET_KEY_FILE) as fread:
            SECRET_KEY = fread.read().replace('\n', '')
    except (IOError, OSError)as ex_access:
        # failed to read secretkey.txt
        SECRET_KEY = NONSECRET_KEY
else:
    # no secret key exists.
    SECRET_KEY = NONSECRET_KEY

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.request",
    "django.core.context_processors.debug",
    "django.core.context_processors.media",
    "django.contrib.auth.context_processors.auth",
)

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # make requests available in templates...
    #'django.core.context_processors.request',
    
    # django debug tools
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # special user-agent middleware...
    'django_user_agents.middleware.UserAgentMiddleware',

)

ROOT_URLCONF = 'wp_main.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'wp_main.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    TEMPLATES_BASE,
    os.path.join(TEMPLATES_BASE, "admin/templates"),
    os.path.join(TEMPLATES_BASE, "admindoc/templates"),
)


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
    
    # django debug tools
    'debug_toolbar',
    # special user-agent middleware
    'django_user_agents',
    # local apps
    'wp_main', # contains global template tags (wp_tags)
    'home',
    'projects',
    'viewer',
    'downloads',
    'blogger',
    'searcher',
    
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
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
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },           
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

DEBUG_TOOLBAR_CONFIG = {'INTERCEPT_REDIRECTS' : False}
