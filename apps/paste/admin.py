from datetime import datetime
from django.contrib import admin
from apps.paste.models import wp_paste
from wp_main.utilities.wp_logging import logger
_log = logger('apps.paste.admin').log


def delete_all_expired(modeladmin, request, queryset):
    """ Delete expired pastes. """
    try:
        for paste in wp_paste.objects.order_by('publish_date'):
            if is_expired(paste):
                paste.delete()
            else:
                # Pastes are ordered by publish date,
                # If this one isn't expired, the rest aren't either.
                break
    except Exception as ex:
        _log.error('Error cleaning all expired pastes:\n{}'.format(ex))
delete_all_expired.short_description = 'Delete ALL expired pastes'


def delete_sel_expired(modeladmin, request, queryset):
    """ Deleted expired selected pastes. """
    try:
        for paste in queryset.order_by('publish_date'):
            if is_expired(paste):
                paste.delete()
            else:
                # This one isn't expired, the rest aren't either.
                # (ordered by publish_date)
                break
    except Exception as ex:
        _log.error('Error cleaning selected expired pastes:\n{}'.format(ex))
delete_sel_expired.short_description = 'Deleted selected expired pastes'


def disable_all_expired(modeladmin, request, queryset):
    """ Disable all expired pastes. """
    try:
        p = wp_paste.objects.filter(disabled=False).order_by('publish_date')
    except Exception as ex:
        _log.error('Error retrieving pastes:\n{}'.format(ex))
        p = []
    for paste in p:
        if is_expired(paste):
            paste.disabled = True
            paste.save()
        else:
            # This one isn't expired, the rest aren't either.
            break
disable_all_expired.short_description = 'Disable ALL expired pastes'


def disable_sel_expired(modeladmin, request, queryset):
    """ Disable selected expired pastes. """
    for paste in queryset.filter(disabled=False).order_by('publish_date'):
        if is_expired(paste):
            paste.disabled = True
            paste.save()
        else:
            # This one's not expired, neither are the rest.
            break
disable_sel_expired.short_description = 'Disable selected expired pastes'


def disable_pastes(modeladmin, request, queryset):
    """ disables pastes (.disabled = True) """
    queryset.update(disabled=True)
disable_pastes.short_description = 'Disable selected pastes'


def enable_pastes(modeladmin, request, queryset):
    """ enables pastes (.disabled = False) """
    queryset.update(disabled=False)
enable_pastes.short_description = 'Enable selected pastes'


def is_expired(paste):
    """ Determine if a paste is expired.
        Returns True if it is, otherwise False.
    """
    if paste.onhold:
        return False

    elapsed = (datetime.now() - paste.publish_date).total_seconds()
    days = (((elapsed / 60) / 60) / 24)
    return (days > 1)


class wp_pasteAdmin(admin.ModelAdmin):
    # enable actions above
    actions = [
        delete_all_expired,
        delete_sel_expired,
        disable_pastes,
        disable_all_expired,
        disable_sel_expired,
        enable_pastes,
    ]
    
admin.site.register(wp_paste, wp_pasteAdmin)
