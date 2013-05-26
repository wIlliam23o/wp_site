#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: Welborn Productions - Statistics
     @summary: Gathers info about blog/project views/downloads and any other
               info I can grab.
    
      @author: Christopher Welborn <cj@welbornprod.com>
@organization: welborn productions <welbornprod.com>
 
   start date: May 25, 2013
'''

import sys, os, os.path

# Append project's settings.py dir.
settings_dir = os.path.join(sys.path[0], "wp_main/")
sys.path.insert(0, settings_dir)

# Set django environment variable (if not set yet)
if not os.environ.has_key("DJANGO_SETTINGS_MODULE"):
    os.environ["DJANGO_SETTINGS_MODULE"] = "wp_main.settings"
    
# Import welbornprod stuff
try:
    from blogger.models import wp_blog
    from projects.models import wp_project
except ImportError as eximp:
    print "unable to import welbornprod modules!\n" + \
          "are you in the right directory?\n\n" + str(eximp)
    sys.exit(1)

# everything from welborn prod was imported correctly.
print "django environment ready..."

# import local tools
try:
    from wpdict import print_block
except ImportError as eximp:
    print "unable to import wpdict.py!\n" + \
          "is it in the same directory as this script?\n\n" + str(eximp)
          
# local tools were imported correctly.
print "local tools imported...\n"

# possible argument flags/options
possible_args = (('-a', '--all'),
                 ('-b', '--blog'),
                 ('-p', '--projects'),
                 ('-v', '--views'),
                 ('-d', '--downloads'),
                 )
# print formatting for print_block()
printblock_args = {'prepend_text': '    ',
                   'append_key': ': ',
                   'prepend_val': None}
def main(args):
    if len(args) == 0:
        return print_all()
    
    argd = make_arg_dict(args, possible_args)
    
    ret = None
    if argd['--all']:
        return print_all()
    
    if argd['--blog']:
        ret = print_blogs_info()
    if argd['--projects']:
        ret = print_projects_info()
    if argd['--views']:
        ret = print_most_views()
    if argd['--downloads']:
        ret = print_most_downloads()
    
    if ret is None:
        # try getting object from argument...
        obj = get_object_byname(args[0])
        if obj is None:
            print "unable to locate info for: " + args[0]
            print "needs more info, like a project name or blog slug."
            return 1
        return print_object_info(obj)


def make_arg_dict(args, arg_tuples):
    argdict = {}
    for argoption in arg_tuples:
        argdict[argoption[1]] = ((argoption[0] in args) or (argoption[1] in args))
    return argdict

def get_object_byname(partialname):
    try:
        obj = wp_project.objects.get(name=partialname)
    except:
        obj =None
    if obj is not None: return obj
    
    try:
        obj = wp_blog.objects.get(name=partialname)
    except:
        obj = None
    if obj is not None: return obj
    
    # search projects
    for proj in wp_project.objects.order_by('name'):
        if proj.name.lower().startswith(partialname.lower()):
            return proj
    
    # search blog posts
    for post in wp_blog.objects.order_by('-posted'):
        if post.slug.startswith(partialname.lower()):
            return post
    
    return None

def print_all():
    ret = print_blogs_info()
    print ' '
    ret2 = print_projects_info()

    return (ret or ret2)

def print_blogs_info():    
    blog_info = get_blogs_info()

    print "Blog Stats:"
    blog_info.printblock(**printblock_args)
    print ' '
    return 0


def print_projects_info():    
    proj_info = get_projects_info()

    print 'Project Stats:'
    proj_info.printblock(**printblock_args)
    print ' '
    
    return 0


def print_object_info(obj):
    obj_info = get_object_info(obj)
    if obj_info is None: return 1
    
    print 'Stats for: ' + obj_info.tracked_keys[0]
    obj_info.printblock(**printblock_args)
    print ' '
    
    return 0


def print_most_views():
    pblock = get_most_views()
    if pblock is None:
        print "couldn't retrieve print block for most views!\n"
        return 1
    else:
        print "Most views:"
        pblock.printblock(**printblock_args)
        print ' '
        return 0


def print_most_downloads():
    pblock = get_most_downloads()
    if pblock is None:
        print "couldn't retrieve print block for most downloads!\n"
        return 1
    else:
        print "Most downloads:"
        pblock.printblock(**printblock_args)
        print ' '
        return 0
    
    
def get_projects_info():
    pblock = print_block()
    for proj in wp_project.objects.order_by('name'):
        # intialize empty info for this project
        #pblock[proj.name] = [" "] # blank item on top...
        newpblock = get_project_info(proj, pblock)
        if newpblock is not None: pblock = newpblock
        # get download count
        #pblock[proj.name] = ["downloads: " + str(proj.download_count)]
        # get view count
        #pblock[proj.name].append("    views: " + str(proj.view_count))
    
    return pblock

def get_blogs_info():
    pblock = print_block()
    for post in wp_blog.objects.order_by('-posted'):
        newpblock = get_post_info(post, pblock)
        if newpblock is not None: pblock = newpblock
        # get view count
        #pblock[post.slug] = ["views: " + str(post.view_count)]
    return pblock

def get_post_info(post_object, pblock=None):
    if post_object is None: return None
    if pblock is None: pblock = print_block()
    
    try:
        pblock[post_object.slug] = ["views: " + str(post_object.view_count)]
    except Exception as ex:
        print "unable to retrieve blog post info!\n" + str(ex)
        return None
    
    return pblock

def get_object_info(obj):
    """ pass it an object from 'get_object_byname' and this will
        decide whether its a blog or project, and return its info.
    """
    
    if obj is None: return None
    
    if hasattr(obj, 'posted'):
        return get_post_info(obj)
    elif hasattr(obj, 'name'):
        return get_project_info(obj)
    else:
        return None
    
def get_project_info(proj_object, pblock=None):
    if proj_object is None: return None
    
    if pblock is None: pblock = print_block()
    
    try:
        pblock[proj_object.name] = ["downloads: " + str(proj_object.download_count)]
        pblock[proj_object.name].append("    views: " + str(proj_object.view_count))
    except Exception as ex:
        print "unable to retrieve project info!\n" + str(ex)
        return None
    return pblock

def get_most_views():
    """ finds objects with the most views """
    
    # find most popular project
    proj = wp_project.objects.order_by('-view_count')[0]
    
    # blog posts
    post = wp_blog.objects.order_by('-view_count')[0]
    
    pblock = print_block()
    pblock['[ Projects ]'] = [' ']
    newpblock = get_project_info(proj, pblock)
    if newpblock is None:
        print "couldn't retrieve print block for most project views!"
        pblock = print_block()
    else:
        pblock = newpblock
    # passing pblock to it adds the blog post info to the projects info. (for making a single print_block)
    pblock['[ Posts ]'] = [' ']
    postblock = get_post_info(post, pblock)
    if postblock is None:
        print "couldn't retrieve print block for most post views!"
    else:
        pblock = postblock
    
    return pblock


def get_most_downloads():
    """ finds project with the most downloads """
    
    # find most downloaded project.
    proj = wp_project.objects.order_by('-download_count')[0]
    
    pblock = get_project_info(proj)
    return pblock

# START OF SCRIPT
if __name__ == "__main__":
    args = sys.argv[1:]
    sys.exit(main(args))