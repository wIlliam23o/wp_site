#!/usr/bin/env python3

'''updateobject.py
    Busybox-style command that updates various models depending on the
    name it is called by.
    If it is called using a symlink named 'updateproject', the wp_project model
    will be used to lookup objects. Same idea with 'updateblog', 'updatemisc',
    etc.
    The name determines which model we will start with, and what the friendly
    names for objects are ('Project', 'Blog Post', etc.). From there, its a
    matter of knowing what attributes are available for the model and
    modifiying them (when --update is used).
    So this single script takes on the form of multiple model viewers/editors.

    Model fields can be listed (base model attributes and types.)
    Objects can be listed
        (all attributes and values.)
    Objects can be modified
        (sets attributes on objects and save()s them to the DB)
    Objects can be looked up by ID, or their main identifiers.
        name, alias for wp_project and wp_misc
        title, slug for wp_blog
        filename for file_tracker

    Ex:
        with a link named updateblog pointing to updateobject.py:
            # Lists all info about this blog post object.
            ./updateblog first-post -l (or --list)

            # Updates view_count for this blog post object.
            ./updateblog first-post --update view_count:21

    Types are determined by examining the current value.
    If the current values type is int, then int(newvalue) is tryed.
    If it is unicode, then unicode(newvalue) [not applicable in Py3].
    If it fails to convert the type, the action is aborted.
    All basic python types work, plus datetime.date.

    See: objectupdater.py for the internal workings,
         this script (updateobject.py) is only the loader.

Created on Nov 1, 2013

@author: Christopher Welborn (cj@welbornprod.com)
'''

# Standard modules
import os
import sys
from collections import namedtuple

# For an implementation of the 'pastetree' script (when listing pastes)
IterPasteResult = namedtuple('IterPasteResult', ['level', 'paste'])

# Local helper modules.
try:
    import django_init
    if not django_init.init_django():
        print('\nUnable to initialize django!')
        sys.exit(1)
except ImportError as eximp:
    print('\nMissing django_init.py!:\n{}'.format(eximp))
    sys.exit(1)

try:
    import objectupdater
except ImportError as eximp:
    print('Missing local module!\nThis won\'t work!\n{}'.format(eximp))
    sys.exit(1)

# import model stuff.
try:
    from projects.models import wp_project
    from blogger.models import wp_blog
    from misc.models import wp_misc
    from downloads.models import file_tracker
    from apps.paste.models import wp_paste, repr_header as paste_repr_header

except ImportError as eximp:
    print('Unable to import model!\n{}'.format(eximp))
    sys.exit(1)

# import docopt
try:
    from docopt import docopt
except ImportError as eximp:
    print('Unable to import docopt!,\n{}'.format(eximp))
    sys.exit(1)

# Helpers for filtering/gathering alias names for updateobject.py
is_updatealias = lambda f: f.startswith('update') and (not 'updateobject' in f)
# Helper for trimming .py from a filename (for aliases, and _SCRIPT)
trim_pyext = lambda f: f[:-3] if f.endswith('.py') else f
# Directory where the alias scripts for updateobject.py can be found.
SCRIPTSDIR = django_init.scripts_dir

try:
    # Grab all updateobject aliases (but not updateobject).
    raw_scripts = os.listdir(SCRIPTSDIR)
    available_aliases = [trim_pyext(f) for f in raw_scripts if is_updatealias(f)]
except Exception as ex:
    print('\nUnable to list available aliases, this may or may not work!\n{}'.format(ex))
    available_aliases = None

# Info used to decide which model we're working on based on what the script name is.
modelinfo = {
    'project': {
        'name': 'Project',
        'model': wp_project,
        'attrs': ('name', 'alias'),
    },
    'blog': {
        'name': 'Blog',
        'model': wp_blog,
        'attrs': ('title', 'slug'),
    },
    'misc': {
        'name': 'Misc',
        'model': wp_misc,
        'attrs': ('name', 'alias'),
    },
    'file': {
        'name': 'FileTracker',
        'model': file_tracker,
        'attrs': ('filename',),
    },
    'paste': {
        'name': 'Paste',
        'model': wp_paste,
        'attrs': ('paste_id', 'id', 'title'),
    },

}
# modelinfo aliases.
modelinfo['proj'] = modelinfo['project']
modelinfo['post'] = modelinfo['blog']
modelinfo['tracker'] = modelinfo['file']

# Get the name that this script was called by
# (used in determining which model we're going to be working with.)
_SCRIPT = trim_pyext(os.path.split(sys.argv[0])[1])

# Determine which model we are working with.
modelname = None
for modelkey in modelinfo.keys():
    if modelkey in _SCRIPT:
        modelname = modelkey
        break
if not modelname:
    print('\nThis script is not designed to be ran directly!\n' +
          'It is meant to be called by one of its aliases:')
    if available_aliases:
        print('{}'.format(', '.join(available_aliases)))
        print('\nFor example, you could type: {} --help\n'.format(available_aliases[0]))
    else:
        print('Unable to locate aliases for updateobject.py!')
    sys.exit(1)

modelused = modelinfo[modelname]
# Script info changes a little depending on how its called (busybox-style I guess)
_NAME = 'Update{}'.format(modelused['name'])
_VERSION = '1.1.0'
_VERSIONSTR = '{} v. {}'.format(_NAME, _VERSION)

# Usage string to use with docopt.
usage_str = objectupdater.base_usage_str.format(
    name=_NAME,
    ver=_VERSION,
    script=_SCRIPT,
    properid=modelused['name'],
    lowerid=modelused['name'].lower(),
    attrstr=', '.join(modelused['attrs']))


def main(argd):
    """ main entry point, expects arg dict from docopt. """
    ret = 0
    # Args for simple object operations.
    id_args = [argd['<identifier>'], modelused['model'], modelused['attrs']]

    # Function map for simple object operations.
    id_funcs = {'--archive': {'func': objectupdater.do_object_archive,
                              'args': id_args,
                              'kwargs': {'usefile': argd['--file']},
                              },
                '--delete': {'func': objectupdater.do_object_delete,
                             'args': id_args,
                             },
                '--list': {'func': objectupdater.do_object_info,
                           'args': id_args,
                           },
                '--json': {'func': objectupdater.do_object_json,
                           'args': id_args,
                           },
                '--pickle': {'func': objectupdater.do_object_pickle,
                             'args': id_args,
                             },
                '--update': {'func': objectupdater.do_object_update,
                             'args': id_args,
                             'kwargs': {'data': argd['--update']},
                             },
                }

    if argd['--ARCHIVE']:
        # Create object from archive.
        ret = objectupdater.do_object_fromarchive(argd['--ARCHIVE'])
    elif argd['--list'] and (not argd['<identifier>']):
        ret = do_list()
    elif argd['--fields']:
        ret = objectupdater.do_fields(modelused['model'])
    elif argd['<identifier>']:
        # ID specific functions..
        handled = False
        for id_flag in id_funcs.keys():
            if argd[id_flag]:
                do_func = id_funcs[id_flag]['func']
                do_args = id_funcs[id_flag]['args']
                if 'kwargs' in id_funcs[id_flag].keys():
                    do_kwargs = id_funcs[id_flag]['kwargs']
                else:
                    do_kwargs = None
                if do_kwargs:
                    ret = do_func(*do_args, **do_kwargs)
                else:
                    ret = do_func(*do_args)
                handled = True
                break

        # Unhandled args, or no args.
        if not handled:
            # No args with identifier (do Header String print)
            ret = objectupdater.do_headerstr(argd['<identifier>'],
                                             modelused['model'],
                                             attrs=modelused['attrs'])

    else:
        # Default behavior (no args)
        ret = do_list()
    return ret


def do_list_blogs():
    """ List all blog post titles. """
    try:
        posts = [p for p in wp_blog.objects.order_by('-posted')]
    except Exception as ex:
        print('\nUnable to list blog posts!\n{}'.format(ex))
        return 1
    if not posts:
        print('\nNo posts found!')
        return 1

    print('Found {} blog posts:'.format(str(len(posts))))
    for post in posts:
        print('    {} ({})'.format(post.title, post.slug))

    return 0


def do_list_filetrackers():
    """ List all filetrackers """

    try:
        files = [f for f in file_tracker.objects.order_by('filename')]
    except Exception as ex:
        print('\nUnable to list file trackers!\n{}'.format(ex))
        return 1
    if not files:
        print('\nNo file trackers found!')
        return 1

    print('Found {} file trackers:'.format(str(len(files))))
    for f in files:
        print('    {}'.format(f.filename))
    return 0


def do_list_misc():
    """ List all misc name, aliases """
    return do_list_projects(model=wp_misc)


def do_list_pastes():
    """ List all pastes (in a tree, like the pastetree script). """
    pastecnt = 0
    print(paste_repr_header())
    for pasteresult in iter_pastes():
        print_pasteresult(pasteresult)
        pastecnt += 1

    pastestr = 'paste' if pastecnt == 1 else 'pastes'
    print('\nFound {} {}.'.format(pastecnt, pastestr))


def do_list_projects(model=None):
    """ List all project or misc names/aliases/versions.
        If miscmodel is passed, it is used instead of wp_project
        since they are printed in the same fashion.
    """

    if not model:
        model = wp_project
        objtype = 'projects'
        usemisc = False
    else:
        objtype = 'misc objects'
        usemisc = True

    try:
        projs = [p for p in model.objects.order_by('alias')]
    except Exception as ex:
        print('\nUnable to list {}!\n{}'.format(objtype, ex))
        return 1
    if not projs:
        print('\nNo {} found!'.format(objtype))
        return 1
    # Instead of doing max(len()) on the projects twice, just iterate once
    # and update both longestname and longestalias.
    # longestname = max(len(p.name) for p in projs))
    # longestalias = max(len(p.alias) for p in projs))
    longestname = 0
    longestalias = 0
    for p in projs:
        paliaslen = len(p.alias)
        pnamelen = len(p.name)
        if paliaslen > longestalias:
            longestalias = paliaslen
        if pnamelen > longestname:
            longestname = pnamelen

    print('Found {} {}:'.format(str(len(projs)), objtype))
    infostrfmt = '    {name} ({alias}) {ver}'
    for proj in projs:
        versionstr = 'v. {}'.format(proj.version) if proj.version else ''
        infostrargs = {
            'name': str(proj.name).ljust(longestname),
            'alias': str(proj.alias).ljust(longestalias),
            'ver': versionstr,
        }
        infostr = infostrfmt.format(**infostrargs)
        if usemisc:
            infostr = '{} {}'.format(infostr, proj.filename)
        print(infostr)
    return 0


def iter_paste_children(paste, level=1):
    """ Iterate over all children of a paste, and children's children. """
    for p in paste.children.order_by('publish_date'):
        yield IterPasteResult(level, p)
        if p.children.count() > 0:
            yield from iter_paste_children(p, level=level + 1)


def iter_pastes(startpastes=None):
    """ Iterate over all pastes that have no parent.
        Given a 'startpastes' list, it will start from that paste only.
    """
    if startpastes is None:
        pastes = wp_paste.objects.filter(parent=None)
        pastes = pastes.order_by('publish_date')
    else:
        pastes = [startpastes]

    for p in pastes:
        yield IterPasteResult(0, p)
        if p.children.count() > 0:
            yield from iter_paste_children(p, level=1)


def print_pasteresult(iresult):
    """ Print a tuple result from iter_children/iter_pastes """
    indention = '  ' * iresult.level
    print('{}{!r}'.format(indention, iresult.paste))

# Set list handler for this model.
listfuncs = {'Project': do_list_projects,
             'Misc': do_list_misc,
             'Blog': do_list_blogs,
             'FileTracker': do_list_filetrackers,
             'Paste': do_list_pastes,
             }
do_list = listfuncs[modelused['name']]

# MAIN
if __name__ == '__main__':
    mainargd = docopt(usage_str, version=_VERSIONSTR)
    mainret = main(mainargd)
    sys.exit(mainret)
