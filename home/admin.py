""" Welborn Productions - Home - Admin
    ...provides web admin for home app configuration.
"""
from django.contrib import admin
from solo.admin import SingletonModelAdmin
from home.models import home_config

admin.site.register(home_config, SingletonModelAdmin)
