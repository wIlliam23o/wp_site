#!/usr/bin/env python

'''updateproject.py
    Updates and lists project info for welbornprod.
    
Created on Nov 1, 2013

@author: cj
'''

# Standard modules
import os
import sys

# Local helper models.
try:
    import django_init
    import objectupdater
except ImportError as eximp:
    print('Missing local module!\nThis won\'t work!\n{}'.format(eximp))
    sys.exit(1)
django_init.init_django(sys.path[0])

# import model stuff.
try:
    from projects.models import wp_project
    from blogger.models import wp_blog
    from misc.models import wp_misc
    from downloads.models import file_tracker
except ImportError as eximp:
    print('Unable to import model!\n{}'.format(eximp))
    sys.exit(1)

# import docopt
try:
    from docopt import docopt
except ImportError as eximp:
    print('Unable to import docopt!,\n{}'.format(eximp))
    sys.exit(1)

try:
    SCRIPTSDIR = os.path.join(sys.path[0], 'scripts')
    # Grab all updateobject aliases (but not updateobject).
    is_updatealias = lambda f: f.startswith('update') and (not 'updateobject' in f)
    trim_pyext = lambda f: f[:-3] if f.endswith('.py') else f
    available_aliases = [trim_pyext(f) for f in os.listdir(SCRIPTSDIR) if is_updatealias(f)]
except Exception as ex:
    print('\nUnable to list available aliases, this may or may not work!')
    available_aliases = ['Unable to locate script aliases!']

# Info used to decide which model we're working on based on what the script name is.
modelinfo = {'project': {'name': 'Project',
                         'model': wp_project,
                         'attrs': ('name', 'alias'),
                         },
             'blog': {'name': 'Blog',
                      'model': wp_blog,
                      'attrs': ('title', 'slug'),
                      },
             'misc': {'name': 'Misc',
                      'model': wp_misc,
                      'attrs': ('name', 'alias'),
                      },
             'file': {'name': 'FileTracker',
                      'model': file_tracker,
                      'attrs': ('filename',),
                      },
             }
# modelinfo aliases.
modelinfo['proj'] = modelinfo['project']
modelinfo['post'] = modelinfo['blog']
modelinfo['tracker'] = modelinfo['file']

# Get name that this script was called by (used in determining which model we're working with.)
_SCRIPT = django_init.get_scriptfile(sys.argv[0])

# Determine which model we are working with.
modelname = None
for modelkey in modelinfo.keys():
    if modelkey in _SCRIPT:
        modelname = modelkey
        break
if not modelname:
    print('\nThis script is not designed to be ran directly!\n' +
          'It is meant to be called by one of its aliases,\n' + 
          '{}\n'.format(', '.join(available_aliases)))
    sys.exit(1)

modelused = modelinfo[modelname]
# Script info changes a little depending on how its called (busybox-style I guess)
_NAME = 'Update{}'.format(modelused['name'])
_VERSION = '1.1.0'
_VERSIONSTR = '{} v. {}'.format(_NAME, _VERSION)

base_usage = objectupdater.base_usage_str.format(name=_NAME, ver=_VERSION, script=_SCRIPT)
usage_str = base_usage.replace('object', modelused['name'].lower()).replace('Object', modelused['name'])


def main(argd):
    """ main entry point, expects arg dict from docopt. """
    ret = 0
    if argd['--list'] and (not argd['<identifier>']):
        ret = do_list()
    elif argd['--fields']:
        ret = objectupdater.do_fields(modelused['model'])
    elif argd['<identifier>']:
        # Retrieve project info.
        if argd['--list']:
            ret = objectupdater.do_object_info(argd['<identifier>'], 
                                               modelused['model'], 
                                               attrs=modelused['attrs'])
        elif argd['--update']:
            ret = objectupdater.do_object_update(argd['<identifier>'], 
                                                 argd['--update'], 
                                                 modelused['model'], 
                                                 attrs=modelused['attrs'])
        else:
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
    
    longestname = max((len(p.name) for p in projs))
    longestalias = max((len(p.alias) for p in projs))
    
    print('Found {} {}:'.format(str(len(projs)), objtype))
    for proj in projs:
        namespace = (' ' * ((longestname - len(proj.name)) + 1))
        aliasspace = (' ' * ((longestalias - len(proj.alias)) + 1))
        versionstr = 'v. {}'.format(proj.version) if proj.version else ''

        infostr = '    {name}{namespace}({alias}){aliasspace}{ver}'.format(name=proj.name, 
                                                                           alias=proj.alias, 
                                                                           ver=versionstr,
                                                                           namespace=namespace,
                                                                           aliasspace=aliasspace)
        if usemisc:
            infostr = '{} {}'.format(infostr, proj.filename)
        print(infostr)
    return 0

# Set list handler for this model.
listfuncs = {'Project': do_list_projects,
             'Misc': do_list_misc,
             'Blog': do_list_blogs,
             'FileTracker': do_list_filetrackers,
             }
do_list = listfuncs[modelused['name']]

# MAIN
if __name__ == '__main__':
    mainargd = docopt(usage_str, version=_VERSIONSTR)
    mainret = main(mainargd)
    sys.exit(mainret)
