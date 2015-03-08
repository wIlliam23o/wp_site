""" Welborn Productions - Stats - Tools
    Tools for gathering info about other models and their counts.
    (downloads, views, etc.)
"""
import logging
from functools import partial

from wp_main.utilities.utilities import get_attrs

log = logging.getLogger('wp.stats.tools')


def get_models_info(modelinfo):
    """ Retrieve several model's info.
        Returns a list of StatsGroup on success, or [] on failure.
        Arguments:
            modelinfo  : A dict with Models as keys, and for values it has a
                         dict of options.
                         Example:
                            get_models_info({wp_blog: {'orderby': '-posted'}})

                options for modelinfo:
                    orderby       : Attribute name to use with .orderby().
                    displayattr   : Attribute/s to display (title, name, id)
                    displayformat : Format string for display.
                                    Like: '{displayattr1} {displayattr2}'
        Returns a list of StatsGroups, or empty list on failure.
    """
    allstats = []
    for model, modelopts in modelinfo.items():
        modelgrp = get_model_info(
            model,
            orderby=modelopts.get('orderby', None),
            displayattr=modelopts.get('displayattr', None),
            displayformat=modelopts.get('displayformat', None))
        if modelgrp:
            allstats.append(modelgrp)
    return sorted(allstats, key=lambda sgrp: str(sgrp.name))


def get_model_info(model, orderby=None, displayattr=None, displayformat=None):
    """ Retrieves info about a model's objects.
        Returns a StatsGroup on success, or None on failure.
    """
    if not hasattr(model, 'objects'):
        log.error('Model with no objects attribute!: {}'.format(model))
        return None

    # Try getting Model._meta.verbose_name_plural. Use None on failure.
    name = getattr(getattr(model, '_meta', None), 'verbose_name_plural', None)
    # Build a new StatsGroup to use.
    stats = StatsGroup(name=name)
    if orderby:
        if not validate_orderby(model, orderby):
            log.error('Invalid orderby for {}: {}'.format(name, orderby))
            return None
        get_objects = partial(model.objects.order_by, orderby)
    else:
        get_objects = model.objects.all

    try:
        for obj in get_objects():
            statitem = get_object_info(
                obj,
                displayattr=displayattr,
                displayformat=displayformat)
            if statitem:
                stats.items.append(statitem)
    except Exception as ex:
        log.error('Error getting objects from: {}\n{}'.format(name, ex))

    return stats if stats else None


def get_object_info(obj, displayattr=None, displayformat=None):
    """ Retrieves a single objects info.
        Returns a StatsItem (with name, download_count, view_count).
    """

    dlcount = getattr(obj, 'download_count', None)
    viewcount = getattr(obj, 'view_count', None)
    name = ''
    if displayattr:
        if not isinstance(displayattr, (list, tuple)):
            displayattr = (displayattr,)
        if not displayformat:
            # Default format is using spaces as a separator.
            displayformat = ' '.join(('{{{}}}'.format(a) for a in displayattr))

        formatargs = {
            a.replace('.', '-'): get_attrs(obj, a, '') for a in displayattr
        }
        try:
            name = displayformat.format(**formatargs)
        except KeyError as ex:
            # KeyError might be hard to debug for this, especially in prod.
            # So, just add a more helpful error msg.
            errmsg = '\n'.join((
                'Error formatting stats object: {obj}',
                '  Error message: {msg}',
                '    displayattr: {attrs}',
                '     format str: {fmtstr}',
                '    format args: {fmtargs}',
            )).format(
                obj=obj,
                msg=ex,
                attrs=displayattr,
                fmtstr=displayformat,
                fmtargs=formatargs)
            log.error(errmsg)
            name = ''

    if not name:
        # Fall back to a known attribute if display formatting is missing
        # The order of these attributes matters. (shortname before name)
        trynames = ('image.name', 'shortname', 'slug', 'name', 'title')
        for obj_id_attr in trynames:
            name = get_attrs(obj, obj_id_attr, None)
            if name:
                break
        else:
            log.error('Object without a name!: {}'.format(obj))
    return StatsItem(name=name, download_count=dlcount, view_count=viewcount)


def validate_orderby(modelobj, orderby):
    """ Make sure this orderby is valid for this modelobj.
        It knows about the  '-orderby' style.
        Returns True if the orderby is good, else False.
    """

    try:
        tempobj = modelobj.objects.create()
    except Exception as ex:
        if hasattr(modelobj, '__name__'):
            mname = modelobj.__name__
        else:
            mname = 'unknown model'
        errmsg = '\nUnable to create temp object for: {}\n{}'
        log.error(errmsg.format(mname, ex))
        return None
    if orderby.startswith('-'):
        orderby = orderby.strip('-')
    goodorderby = hasattr(tempobj, orderby)
    # Delete the object that was created to test the orderby attribute.
    tempobj.delete()
    return goodorderby


class _NoValue(object):

    """ Something other than None to mean 'No value set'.
        It can mean 'missing this attribute originally'.
    """

    def __bool__(self):
        """ NoValue is like None, bool(NoValue) is always False. """
        return False

    def __repr__(self):
        return 'NoValue'

    def __str__(self):
        return self.__repr__()
NoValue = _NoValue()


class StatsGroup(object):

    """ Holds a collection of stats with a name (Projects, Posts, etc.)
        Each item in .items will be a StatsItem().
    """

    def __init__(self, name=None, items=None):
        self.name = name or 'Unknown'
        self.items = items or []
        self.id = None
        self.update_id()

    def __bool__(self):
        """ Returns True if any(self.items). """
        return any(self.items)

    def __repr__(self):
        """ A short and simple str representation for this group. """
        self.update_id()
        return '{}: ({} items)'.format(self.name, len(self.items))

    def __str__(self):
        """ A formatted str for this stats group. """
        self.update_id()
        return '{}:\n    {}'.format(
            self.name,
            '\n    '.join(
                (str(i).replace('\n', '\n    ') for i in self.items)))

    def update_id(self):
        """ Update the id for this stats group. """
        if self.id:
            return None
        if self.name is NoValue:
            return None
        self.id = self.name.lower().replace(' ', '-').replace('.', '')


class StatsItem(object):

    """ A single item with a name, download_count, and view_count. """

    def __init__(self, name=None, download_count=None, view_count=None):
        self.name = name or NoValue
        if download_count is None:
            self.download_count = NoValue
        else:
            self.download_count = download_count
        if view_count is None:
            self.view_count = NoValue
        else:
            self.view_count = view_count

    def __bool__(self):
        """ Returns False if all attributes are set to NoValue. """
        return not (
            (self.name is NoValue) and
            (self.download_count is NoValue) and
            (self.view_count is NoValue))

    def __repr__(self):
        """ Basic str representation. """
        name = 'No Name' if self.name is NoValue else self.name
        return '{}: {}, {}'.format(name, self.download_count, self.view_count)

    def __str__(self):
        name = 'No Name' if self.name is NoValue else self.name
        infolines = []
        if self.download_count is not NoValue:
            infolines.append('    downloads: {}'.format(self.download_count))
        if self.view_count is not NoValue:
            infolines.append('        views: {}'.format(self.view_count))
        if infolines:
            return '{}\n{}'.format(name, '\n'.join(infolines))
        # A stats item with no info!
        return '{} (No Info!)'.format(name)
