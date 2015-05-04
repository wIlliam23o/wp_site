""" Welborn Productions - Apps - Paste - Admin
    ...Handles djang-admin site actions/listings for wp_paste objects.
    -Christopher Welborn 2014
"""

import logging
from django.contrib import admin, messages
from apps.paste.models import wp_paste
log = logging.getLogger('wp.apps.paste.admin')


def delete_expired(pastes):
    """ Delete all expired pastes, given a QuerySet/List of pastes. """
    try:
        pastes = pastes.order_by('publish_date')
    except AttributeError:
        # Can't sort a list of pastes using order_by.
        return -1

    deletedcount = 0
    for p in pastes:
        if p.is_expired():
            p.delete()
            deletedcount += 1

    return deletedcount


def delete_sel_expired(modeladmin, request, queryset):
    """ Deleted expired selected pastes. """
    querylen = len(queryset)
    delcount = delete_expired(queryset)
    pstr = 'paste' if delcount == 1 else 'pastes'
    msg = 'Deleted {} of {} selected {}.'.format(delcount, querylen, pstr)
    modeladmin.message_user(request, msg, level=messages.SUCCESS)
delete_sel_expired.short_description = 'Delete selected expired pastes'


def disable_expired(pastes):
    """ Disabled all expired pastes, given a QuerySet/List of pastes. """
    try:
        pastes = pastes.order_by('publish_date')
    except AttributeError:
        # Can't sort a list of pastes using order_by.
        return -1

    disabledcount = 0
    for p in pastes:
        if p.is_expired():
            p.disabled = True
            p.save()
            disabledcount += 1

    return disabledcount


def disable_sel_expired(modeladmin, request, queryset):
    """ Disable selected expired pastes. """
    discnt = disable_expired(queryset)
    msg = 'Disabled {} of {} selected pastes.'.format(discnt, len(queryset))
    modeladmin.message_user(request, msg, level=messages.SUCCESS)
disable_sel_expired.short_description = 'Disable selected expired pastes'


def disable_pastes(modeladmin, request, queryset):
    """ disables pastes (.disabled = True) """
    dcnt = queryset.update(disabled=True)
    pstr = plural(dcnt, 'paste')
    msg = 'Disabled {} {}.'.format(dcnt, pstr)
    modeladmin.message_user(request, msg, level=messages.SUCCESS)
disable_pastes.short_description = 'Disable selected pastes'


def enable_pastes(modeladmin, request, queryset):
    """ enables pastes (.disabled = False) """
    encnt = queryset.update(disabled=False)
    pstr = plural(encnt, 'paste')
    msg = 'Enabled {} {}.'.format(encnt, pstr)
    modeladmin.message_user(request, msg, level=messages.SUCCESS)
enable_pastes.short_description = 'Enable selected pastes'


def hold_sel(modeladmin, request, queryset):
    """ marks selected pastes as 'onhold' """
    heldcnt = queryset.update(onhold=True)
    pstr = plural(heldcnt, 'paste was', 'pastes were')
    msg = '{} {} marked as \'onhold\'.'.format(heldcnt, pstr)
    modeladmin.message_user(request, msg, level=messages.SUCCESS)
    return heldcnt
hold_sel.short_description = 'Hold selected pastes'


def plural(cnt, word, pluralform=None):
    """ Pluralize a word based on a count. """
    if cnt == 1:
        return word
    if pluralform is not None:
        return pluralform
    return '{}s'.format(word)


def privatize_sel(modeladmin, request, queryset):
    """ marks selected pastes as private. """
    selcnt = len(queryset)
    privcnt = queryset.update(private=True)
    pstr = plural(selcnt, 'paste was', 'pastes were')
    msg = '{} of {} {} marked as private.'.format(privcnt, selcnt, pstr)
    modeladmin.message_user(request, msg, level=messages.SUCCESS)
    return privcnt
privatize_sel.short_description = 'Privatize selected pastes'


def remove_hold_sel(modeladmin, request, queryset):
    """ marks selected pastes as not 'onhold' """
    p = queryset.filter(onhold=True)
    notheldcnt = p.update(onhold=False)
    pstr = plural(notheldcnt, 'paste was', 'pastes were')
    msg = '{} {} marked as not \'onhold\'.'.format(notheldcnt, pstr)
    modeladmin.message_user(request, msg, level=messages.SUCCESS)
    return notheldcnt
remove_hold_sel.short_description = 'Remove hold on selected pastes'


def unprivatize_sel(modeladmin, request, queryset):
    """ marks selected pastes as private. """
    selcnt = len(queryset)
    privcnt = queryset.update(private=False)
    pstr = plural(selcnt, 'paste was', 'pastes were')
    msg = '{} of {} {} marked as not private.'.format(privcnt, selcnt, pstr)
    modeladmin.message_user(request, msg, level=messages.SUCCESS)
    return privcnt
unprivatize_sel.short_description = 'Unprivatize selected pastes'


class wp_pasteAdmin(admin.ModelAdmin):  # noqa
    # enable actions above
    actions = [
        delete_sel_expired,
        disable_pastes,
        disable_sel_expired,
        enable_pastes,
        hold_sel,
        privatize_sel,
        remove_hold_sel,
        unprivatize_sel,
    ]


admin.site.register(wp_paste, wp_pasteAdmin)
