#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
      project: Welborn Productions - Statistics
     @summary: Gathers info about blog/project views/downloads and any other
               info I can grab.

      @author: Christopher Welborn <cj@welbornprod.com>
@organization: welborn productions <welbornprod.com>

   start date: May 25, 2013
'''

# TODO: Use the new stats app and stats/tools.py to gather info.

import sys

NAME = 'WpStats'
__VERSION__ = '1.5.0'

# Setup django environment if ran from the command line.
if __name__ == '__main__':
    try:
        try:
            # Import style for django.
            from scripts import django_init
        except ImportError:
            # Import style for cmdline.
            import django_init
        if not django_init.init_django():
            sys.exit(1)
    except ImportError as eximp:
        print('\nUnable to import django_init.py!:\n{}'.format(eximp))
        sys.exit(1)
    except Exception as ex:
        print('\nUnable to initialize django environment!:\n{}'.format(ex))
        sys.exit(1)

# Import welbornprod stuff
try:
    from blogger.models import wp_blog
    from projects.models import wp_project
    from downloads.models import file_tracker
    from misc.models import wp_misc
except ImportError as eximp:
    print("unable to import welbornprod modules!\n" +
          "are you in the right directory?\n\n" + str(eximp))
    sys.exit(1)

# import local tools
try:
    from scripts.wpdict import PrintBlock
except ImportError as eximp:
    print("unable to import wpdict.py!\n" +
          "is it in the same directory as this script?\n\n" + str(eximp))

# local tools were imported correctly.
# print( "local tools imported...\n")

# possible argument flags/options
possible_args = (('-a', '--all', 'Print info about all models.'),
                 ('-b', '--blog', 'Print info about blog posts.'),
                 ('-d', '--downloads',
                  'Print objects with the most downloads.'),
                 ('-f', '--files', 'Print info about file trackers.'),
                 ('-h', '--help', 'Show this message.'),
                 ('-m', '--misc', 'Print info about misc objects.'),
                 ('-o=', '--orderby',
                  'Order to use when printing object info.'),
                 ('-p', '--projects', 'Print info about projects.'),
                 ('-v', '--views', 'Print objects with the most views.'),
                 )
# print formatting for PrintBlock()
printblock_args = {
    'prepend_text': '    ',
    'append_key': ': ',
    'prepend_val': None
}

# default orders
orderby_projects = 'name'
orderby_posts = '-posted'
orderby_files = 'shortname'
orderby_misc = 'name'


def main(args):

    if len(args) == 0:
        return print_all()
    ret = None
    argd = make_arg_dict(args, possible_args)

    if argd['--help']:
        print_help()
        return 0

    orderby = argd['--orderby']
    if orderby is not None:
        orderby = orderby.lower()  # all my attr's are lowercase.

    if argd['--all']:
        return print_all(order=orderby)

    if argd['--blog']:
        ret = print_blogs_info(order=orderby)
    if argd['--projects']:
        ret = print_projects_info(order=orderby)
    if argd['--files']:
        ret = print_files_info(order=orderby)
    if argd['--misc']:
        ret = print_misc_info(order=orderby)
    if argd['--views']:
        ret = print_most_views()
    if argd['--downloads']:
        ret = print_most_downloads()

    if ret is None:
        # try getting object from argument...
        obj = get_object_byname(args[0])
        if obj is None:
            print("unable to locate info for: " + args[0])
            print("needs more info, like a project name or blog slug.")
            return 1
        return print_object_info(obj)


def make_arg_dict(args, arg_tuples):
    argdict = {}

    def find_val(opt):
        short_ = opt[0].strip('=')
        long_ = opt[1]
        for arg in args:
            if arg.startswith(short_) or arg.startswith(long_):
                if '=' in arg:
                    try:
                        opt, val = arg.split('=')
                        return val
                    except:
                        # invalid option syntax (users fault)
                        return None
                else:
                    # no '=' in option (users fault)
                    return None
        # option wasn't found in args
        return None

    # parse args
    for argoption in arg_tuples:
        if '=' in argoption[0]:
            # this is a setting, we need to find its value (if any)
            possibleval = find_val(argoption)
            argdict[argoption[1]] = possibleval
        else:
            # regular flag, its either there or it isn't.
            argdict[argoption[1]] = (
                (argoption[0] in args) or (argoption[1] in args))
    return argdict


def get_objects_safe(model_, orderby=None):
    """ Try to get model_.objects.all(),
        return None on failure.
    """
    try:
        if orderby:
            objs = model_.objects.order_by(orderby)
        else:
            objs = model_.objects.all()
        return objs
    except:
        return None


def get_object_id(obj):
    obj_type = get_object_type(obj).lower().replace(' ', '')
    if obj_type == 'project':
        return obj.name
    elif obj_type == 'blogpost':
        return obj.slug
    elif obj_type == 'file':
        return obj.shortname
    elif obj_type == 'misc':
        return obj.name
    else:
        return 'Unknown Object!'


def get_object_type(obj):
    if hasattr(obj, 'version'):
        return 'Project'
    elif hasattr(obj, 'posted'):
        return 'Blog Post'
    elif hasattr(obj, 'shortname'):
        return 'File'
    elif hasattr(obj, 'content'):
        return 'Misc'
    else:
        return 'Unknown'


def get_object_byname(partialname):
    """ Return any object by name or partial name. """
    # Tuple of Model, [SearchKeys], OrderBy
    models = ((wp_project, ['name'], orderby_projects),
              (wp_blog, ['title', 'slug'], orderby_posts),
              (wp_misc, ['filename'], orderby_misc),
              (file_tracker, ['shortname'], orderby_files),
              )
    objectinfo = {}
    # Build objects, search key, full key match.
    for model_, searchkeys, orderby in models:
        objectinfo[model_.__name__] = {
            'objects': get_objects_safe(model_, orderby=orderby),
            'getargs': searchkeys,
        }
    # Try full match using .get()
    for modelname in objectinfo.keys():
        for searchkey in objectinfo[modelname]['getargs']:
            try:
                getargs = {searchkey: partialname}
                obj = objectinfo[modelname]['objects'].get(**getargs)
                if obj:
                    return obj
            except:
                # Failed to get object, move to the next searchkey/model.
                continue

    # Try partial match, search all models
    for modelname in objectinfo.keys():
        # Search objects for this model
        for objitem in objectinfo[modelname]['objects']:
            # Try search key for this object (may be only one searchkey)
            for searchkey in objectinfo[modelname]['getargs']:
                # Get Model.objects.all()[thisobj].searchkey
                modelattr = getattr(objitem, searchkey)
                if modelattr.lower().startswith(partialname.lower()):
                    # Found a match.
                    return objitem

    return None


def print_all(order=None):
    returns = []
    returns.append(print_blogs_info(order))
    print(' ')
    returns.append(print_projects_info(order))
    print(' ')
    returns.append(print_misc_info(order))
    print(' ')
    returns.append(print_files_info(order))
    if any(returns):
        # at least one of the functions returned 1.
        return 1
    else:
        return 0


def print_blogs_info(order=None):
    """ Print all info gathered with get_blogs_info(),
        formatted with a PrintBlock()
    """
    if wp_blog.objects.count() == 0:
        print('\nNo blog posts to gather info for!')
        return 1

    if order is None:
        order = orderby_posts
    else:
        if not validate_orderby(wp_blog, order):
            print("Posts don't have a '" + order +
                  "' attribute, using the default: " + orderby_posts)
            order = orderby_posts
    blog_info = get_blogs_info(order)
    print("Blog Stats order by " + order + ":")
    blog_info.printblock(**printblock_args)
    print(' ')
    return 0


def print_misc_info(order=None):
    """ Print all info gathered with get_misc_info(), formatted with PrintBlock() """
    if wp_misc.objects.count() == 0:
        print('\nNo misc objects to gather info for!')
        return 1

    if order is None:
        order = orderby_misc
    else:
        if not validate_orderby(wp_misc, order):
            print('Misc objects don\'t have a \'' + order +
                  '\' attribute, using the default: ' + orderby_misc)
            order = orderby_misc

    misc_info = get_misc_info(order)
    print('Misc Stats ordered by ' + order + ':')
    misc_info.printblock(**printblock_args)
    print(' ')
    return 0


def print_projects_info(order=None):
    """ Print all info gathered with get_projects_info(), formatted with a PrintBlock() """
    if wp_project.objects.count() == 0:
        print('\nNo projects to gather info for!')
        return 1

    if order is None:
        order = orderby_projects
    else:
        if not validate_orderby(wp_project, order):
            print("Projects don't have a '" + order +
                  "' attribute, using the default: " + orderby_projects)
            order = orderby_projects
    proj_info = get_projects_info(order)
    print('Project Stats ordered by ' + order + ':')
    proj_info.printblock(**printblock_args)
    print(' ')

    return 0


def print_files_info(order=None):
    """ Print all info gathered with get_files_info(), formatted with a print block. """

    if file_tracker.objects.count() == 0:
        print('\nNo file-trackers to gather info for.')
        return 1

    if order is None:
        order = orderby_files
    else:
        if not hasattr(file_tracker.objects.all()[0], order.strip('-')):
            print("File Trackers don't have a '" + order +
                  "' attribute, using the default: " + orderby_files)
            order = orderby_files

    file_info = get_files_info(order)
    print("File Stats ordered by " + order + ":")
    file_info.printblock(**printblock_args)
    print(' ')

    return 0


def print_help():
    # calculate spacing for helpstr
    maxlen = 0
    for shortopt, longopt, helpstr in possible_args:
        optlen = len('{},{}'.format(shortopt, longopt))
        if optlen > maxlen:
            maxlen = optlen

    print('wpstats v. {}\n    Usage: wpstats [options]\n'.format(__VERSION__))
    print('Options:')
    for shortopt, longopt, helpstr in possible_args:
        optstr = '{},{}'.format(shortopt, longopt)
        optlen = len(optstr)
        spacinglen = ((maxlen - optlen) + 2)
        spacing = ' ' * spacinglen
        print('    {}{}: {}'.format(optstr, spacing, helpstr))
    print(' ')


def print_object_info(obj):
    obj_info = get_object_info(obj)
    if obj_info is None:
        return 1

    obj_type = get_object_type(obj)

    print('Stats for: ' + get_object_id(obj) + ' [' + obj_type + ']')
    obj_info.printblock(**printblock_args)
    print(' ')

    return 0


def print_most_views():
    pblock = get_most_info('-view_count')
    if pblock is None:
        print("couldn't retrieve print block for most views!\n")
        return 1
    else:
        print("Most views:")
        pblock.printblock(**printblock_args)
        print(' ')
        return 0


def print_most_downloads():
    pblock = get_most_info('-download_count')
    if pblock is None:
        print("couldn't retrieve print block for most downloads!\n")
        return 1
    else:
        print("Most downloads:")
        pblock.printblock(**printblock_args)
        print(' ')
        return 0


def get_misc_info(orderby=None):
    pblock = PrintBlock()
    if wp_misc.objects.count() == 0:
        return pblock

    if orderby is None:
        orderby = orderby_misc
    if not validate_orderby(wp_misc, orderby):
        orderby = orderby_misc

    for misc in wp_misc.objects.order_by(orderby):
        newpblock = get_miscobj_info(misc, pblock)
        if newpblock is not None:
            pblock = newpblock

    return pblock


def get_projects_info(orderby=None):
    pblock = PrintBlock()
    if wp_project.objects.count() == 0:
        return pblock

    if orderby is None:
        orderby = orderby_projects
    if not validate_orderby(wp_project, orderby):
        orderby = orderby_projects
    for proj in wp_project.objects.order_by(orderby):
        newpblock = get_project_info(proj, pblock)
        if newpblock is not None:
            pblock = newpblock

    return pblock


def get_blogs_info(orderby=None):
    pblock = PrintBlock()
    if wp_blog.objects.count() == 0:
        return pblock

    if orderby is None:
        orderby = orderby_posts
    if not validate_orderby(wp_blog, orderby):
        orderby = orderby_posts

    for post in wp_blog.objects.order_by(orderby):
        newpblock = get_post_info(post, pblock)
        if newpblock is not None:
            pblock = newpblock

    return pblock


def get_files_info(orderby=None):
    pblock = PrintBlock()
    if file_tracker.objects.count() == 0:
        return pblock

    filetrackers = file_tracker.objects.all()
    if filetrackers is None:
        return pblock
    elif filetrackers == []:
        return pblock

    if orderby is None:
        orderby = orderby_files
    if not validate_orderby(file_tracker, orderby):
        orderby = orderby_files

    for filetracker in filetrackers.order_by(orderby):
        newpblock = get_file_info(filetracker, pblock)
        if newpblock is not None:
            pblock = newpblock

    return pblock


def get_file_info(filetrack_obj, pblock=None):
    if filetrack_obj is None:
        return None
    if pblock is None:
        pblock = PrintBlock()

    try:
        pblock[filetrack_obj.shortname] = [
            "downloads: " + str(filetrack_obj.download_count)]
        pblock[filetrack_obj.shortname].append(
            "    views: " + str(filetrack_obj.view_count))
    except Exception as ex:
        print("unable to retrieve file tracker info!\n" + str(ex))
        return None
    return pblock


def get_miscobj_info(miscobj, pblock=None):
    """ Retrieve printblock info for a single misc object """
    if miscobj is None:
        return None
    if pblock is None:
        pblock = PrintBlock()

    try:
        pblock[miscobj.name] = ['downloads: ' + str(miscobj.download_count)]
        pblock[miscobj.name].append('    views: ' + str(miscobj.view_count))
    except Exception as ex:
        print('unable to retrieve misc object info!\n{}'.format(str(ex)))
        return None
    return pblock


def get_post_info(post_object, pblock=None):
    if post_object is None:
        return None
    if pblock is None:
        pblock = PrintBlock()

    try:
        pblock[post_object.slug] = [
            '    views: ' + str(post_object.view_count)]
    except Exception as ex:
        print("unable to retrieve blog post info!\n" + str(ex))
        return None

    return pblock


def get_object_info(obj):
    """ pass it an object from 'get_object_byname' and this will
        decide whether its a blog or project, and return its info.
    """

    if obj is None:
        return None

    if hasattr(obj, 'posted'):
        return get_post_info(obj)
    elif hasattr(obj, 'name'):
        return get_project_info(obj)
    elif hasattr(obj, 'shortname'):
        return get_file_info(obj)
    else:
        return None


def get_project_info(proj_object, pblock=None):
    if proj_object is None:
        return None

    if pblock is None:
        pblock = PrintBlock()

    try:
        pblock[proj_object.name] = [
            "downloads: " + str(proj_object.download_count)]
        pblock[proj_object.name].append(
            "    views: " + str(proj_object.view_count))
    except Exception as ex:
        print("unable to retrieve project info!\n" + str(ex))
        return None
    return pblock


def get_most_info(orderby):
    """ finds objects with the most views """

    models = (('[ Projects ]', wp_project, get_project_info),
              ('[ Misc ]', wp_misc, get_miscobj_info),
              ('[ Posts ]', wp_blog, get_post_info),
              ('[ Files ]', file_tracker, get_file_info))
    pblock = PrintBlock()
    # Cycle through all models.
    for header, modelobj, infofunc in models:
        # Make sure this orderby applies to this model (download_count doesn't
        # apply to all)
        if validate_orderby(modelobj, orderby):
            # Try getting top item (there might not be any items)
            topitem = try_top_item(modelobj, orderby)
            if topitem:
                # Build a new pblock from objects info.
                pblock[header] = [' ']
                # passing pblock mean that any info found gets added to it
                # and returned as newpblock, on failure newpblock is None.
                # ...but we still have pblock to work with.
                newpblock = infofunc(topitem, pblock)
                if newpblock is not None:
                    pblock = newpblock
    return pblock


def try_top_item(model_, orderby):
    if not orderby.startswith('-'):
        orderby = '-' + orderby
    try:
        topmost = model_.objects.order_by(orderby)[0]
        return topmost
    except Exception as ex:
        # no objects, or incorrect orderby.
        if hasattr(model_, '__name__'):
            modelname = model_.__name__
        else:
            modelname = 'unknown model'
        print(
            '\nUnable to get top-most item for {}: {}\n{}'.format(modelname, orderby, str(ex)))
        return None


def validate_orderby(modelobj, orderby):
    """ make sure this orderby is valid for this modelobj.
        also watches for -orderby.
    """

    try:
        tempobj = modelobj.objects.create()
    except Exception as ex:
        if hasattr(modelobj, '__name__'):
            mname = modelobj.__name__
        else:
            mname = 'unknown model'
        print(
            '\nUnable to create temp object for: {}\n{}'.format(mname, str(ex)))
        return False
    if orderby.startswith('-'):
        orderby = orderby.strip('-')
    goodorderby = hasattr(tempobj, orderby)
    tempobj.delete()
    return goodorderby


class StatsInfo(object):

    """ Holds info for stats.html template and home.view_stats() view. """

    def __init__(self, title=None, statlines=None):
        self.title = title
        self.statlines = statlines


class StatsCollection(object):

    """ Holds a collection of StatsInfo objects. """

    def __init__(self, *args):
        """ Adds a list of StatsInfo()'s on intialization """
        self.stats = []
        for arg in args:
            if arg is not None:
                self.stats.append(arg)

    def add(self, *args):
        for statsinfo in args:
            self.stats.append(statsinfo)


# START OF SCRIPT
if __name__ == "__main__":
    args = sys.argv[1:]
    sys.exit(main(args))
