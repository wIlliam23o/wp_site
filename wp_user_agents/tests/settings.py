from os import path


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    },
}

INSTALLED_APPS = ['wp_user_agents']

MIDDLEWARE_CLASSES = (
    'wp_user_agents.middleware.UserAgentMiddleware',
)

ROOT_URLCONF = 'wp_user_agents.tests.urls'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 60,
    }
}

TEMPLATE_DIRS = (
    path.join(path.dirname(__file__), "templates"),
)
