#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Version for welbornprod.com
# (versioning didn't start until the move to python3,
#  2.0 is considered a new beginning because the project
#  is moving towards a backward-incompatible state,
#  where all python 2 'hacks' will be removed.)
WPVERSION = '2.1.1'

# file/path (path joining)
import os.path
import sys
SYSVERSION = sys.version

# Django messages framework, message-levels
#from django.contrib.messages import constants as message_constants
#MESSAGE_LEVEL = message_constants.ERROR

# DEBUG is in settings_local...

# decide which dirs to use based on hostname.
# determine parent dir for script
SCRIPT_PARENT = os.path.dirname(os.path.realpath(__file__))
# get application base dir
BASE_DIR = os.path.split(SCRIPT_PARENT)[0]
# get parent of application
BASE_PARENT = os.path.split(BASE_DIR)[0]

# test or live?
if 'webapps' in BASE_PARENT:
    # live site directories
    STATIC_PARENT = BASE_PARENT
    # Static dirs based on test/live site. Set in local_settings.
    STATIC_ROOT = 'unknown'
    MEDIA_URL = 'http://welbornprod.com/media/'
    SERVER_LOCATION = 'remote'
else:
    # local development directories
    STATIC_PARENT = '/var/www/'
    STATIC_ROOT = '/var/www/static'
    MEDIA_URL = 'http://127.0.0.1/media/'
    SERVER_LOCATION = 'local'


# Static/Media directories.
MEDIA_ROOT = os.path.join(STATIC_PARENT, "media")
    
# main app (location of settings.py)
MAIN_DIR = os.path.join(BASE_DIR, "wp_main")
TEMPLATES_BASE = os.path.join(MAIN_DIR, "templates")

# IP's debug_toolbar should be shown to.
# check for local internal_ips.txt,
# allow the ips in that file if it exists.
_internal_ips = ['127.0.0.1']
# KEY is in the variable name so django debug automatically
# hides it from debug.
KEY_INTERNAL_IPS_FILE = os.path.join(BASE_DIR, "internal_ips.txt")
if os.path.isfile(KEY_INTERNAL_IPS_FILE):
    try:
        with open(KEY_INTERNAL_IPS_FILE) as f_ips:
            ip_raw = f_ips.read()
            if '\n' in ip_raw:
                # list of ips in file.
                ips_list = []
                for ip_ in ip_raw.split('\n'):
                    ip_ = ip_.strip()
                    if len(ip_) > 7 and (not ip_.startswith('#')):
                        _internal_ips.append(ip_)
            else:
                # single ip in file
                _internal_ips.append(ip_raw)
    except Exception as ex:
        pass

# Add local dev ips to safe list.
_internal_ips.extend(['192.168.0.{}'.format(n) for n in range(2, 21)])
_internal_ips.extend(['192.168.1.{}'.format(n) for n in range(2, 21)])
# set global allowed ips
INTERNAL_IPS = tuple(_internal_ips)


# Admin info
ADMINS = (('Christopher Welborn', 'cj@welbornprod.com'), )
MANAGERS = ADMINS


# Database info (filled in with settings_local)
DATABASES = {
    'default': {
        'ENGINE': '',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

#------------------ Settings above this may be squashed by settings_local -----
# Fill in missing settings from local file (not in git).
SECRET_LOCAL_SETTINGS = os.path.join(BASE_DIR, 'settings_local.py')
# This is a hack. Badly recommended from several places on the internet.
# This could probably be done better with a secret JSON file, or even a
# sqlite database. The idea would be the same but it would only parse/read
# the data, and no code would be executed.
#     like: json.loads(open(secret_file).read())
# The only problem is the few 'decisions' that the local-settings-file makes.
# ...like setting 'SITE_VERSION' based on cwd. (harmless debug info but still)
if sys.version_info.major < 3:
    try:
        execfile(SECRET_LOCAL_SETTINGS)  # noqa
    except Exception as ex:
        sys.stderr.write('\n'.join([
            'Error including settings_local.py!',
            'This will not work.',
            '{}\n'.format(ex)]))
else:
    # Python 3 exec file is gone.
    try:
        exec(compile(open(SECRET_LOCAL_SETTINGS).read(),
                     SECRET_LOCAL_SETTINGS,
                     'exec'),
             globals(), locals())
    except Exception as ex:
        sys.stderr.write('\n'.join([
            'Error including settings_local.py!',
            'This will not work.',
            '{}\n'.format(ex)]))

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
if 'webapps' in BASE_PARENT and (not 'test' in BASE_PARENT):
    # Use db cache for live site.
    CACHES['default'] = CACHES['cache_db']
else:
    # Use dummy cache for local development, and test site.
    CACHES['default'] = CACHES['cache_dummy']


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

# SECRET_KEY SETTINGS
# Make this unique, and don't share it with anybody.
SECRET_KEY_FILE = os.path.join(BASE_DIR, "secretkey.txt")
if os.path.isfile(SECRET_KEY_FILE):
    try:
        with open(SECRET_KEY_FILE) as fread:
            SECRET_KEY = fread.read().replace('\n', '')
    except (IOError, OSError)as ex_access:
        # failed to read secretkey.txt
        SECRET_KEY = NONSECRET_KEY  # noqa
else:
    # no secret key exists.
    SECRET_KEY = NONSECRET_KEY  # noqa

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or
    # "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    TEMPLATES_BASE,
    os.path.join(TEMPLATES_BASE, 'admin/templates'),
    os.path.join(TEMPLATES_BASE, 'admindoc/templates'),
    # Include project pages as possible templates.
    os.path.join(BASE_DIR, 'projects/static/html'),
    # Include blog pages as possible templates.
    os.path.join(BASE_DIR, 'blogger/static/html'),
)

MIDDLEWARE_CLASSES = (
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
    
    # make requests available in templates...
    #'django.core.context_processors.request',
    
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

    # for making get_user_agent(request) available.
    'wp_user_agents',
    # local apps
    'wp_main',  # contains global template tags (wp_tags)
    'home',
    'projects',
    'viewer',
    'downloads',
    'blogger',
    'searcher',
    'misc',
    'apps',  # handles urls for all sub-apps.
    'apps.phonewords',
    'apps.paste',
    
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
    }
}
    

# Only turn error emails on with the remote server
# They are driving me nuts when I'm expirimenting locally and DEBUG == False.
if SERVER_LOCATION == 'remote':
    LOGGING['handlers'] = {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    }
    LOGGING['loggers'] = {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        }
    }

# Disable redirect panel (per new debug_toolbar method.)
DEBUG_TOOLBAR_CONFIG = {
    'DISABLE_PANELS': set(['debug_toolbar.panels.redirects.RedirectsPanel'])
}
# Don't automatically adjust project settings based on DEBUG!
DEBUG_TOOLBAR_PATCH_SETTINGS = False

# default login url
# (regex for wp_main.urls, put here to avoid future mismatches)
LOGIN_URL = "/login"
LOGIN_URL_REGEX = "^login/?.+"

# default page to visit after login (if 'next url' is not specified)
LOGIN_REDIRECT_URL = "/"
