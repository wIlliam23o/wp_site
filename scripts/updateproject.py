#!/usr/bin/env python

'''updateproject.py
    Updates and lists project info for welbornprod.
    
Created on Nov 1, 2013

@author: cj
'''

# Standard modules
import datetime
import re
import sys

try:
    import django_init
except ImportError as eximp:
    print('Missing django_init module!\nThis won\'t work!\n{}'.format(eximp))
    sys.exit(1)
django_init.init_django(sys.path[0])

# import projects stuff.
try:
    from projects.models import wp_project
except ImportError as eximp:
    print('Unable to import model!\n{}'.format(eximp))
    sys.exit(1)

# import docopt
try:
    from docopt import docopt
except ImportError as eximp:
    print('Unable to import docopt!,\n{}'.format(eximp))
    sys.exit(1)

_NAME = 'UpdateProject'
_VERSION = '1.0.0'
_VERSIONSTR = '{} v. {}'.format(_NAME, _VERSION)
_SCRIPT = django_init.get_scriptfile(sys.argv[0])
usage_str = """{name} v. {ver}

    Usage:
        {script} <project> -l
        {script} <project> -u attribute:val
        {script} [-h | -v]
        {script} -f | -l
        
    Options:
        <project>              : Project identifier.
        -f,--fields            : List model fields.
        -h,--help              : Show this message.
        -l,--list              : List detailed project info, or summary of projects if none was given.
        -u data,--update data  : Update project info with attribute:value or "attribute:spaced value"
        -v,--version           : Show version.
        
""".format(name=_NAME, ver=_VERSION, script=_SCRIPT)


def main(argd):
    """ main entry point, expects arg dict from docopt. """
    ret = 0
    if argd['--list'] and (not argd['<project>']):
        ret = do_list()
    elif argd['--fields']:
        ret = do_fields()
    elif argd['<project>']:
        # Retrieve project info.
        if argd['--list']:
            ret = do_project_info(argd['<project>'])
        elif argd['--update']:
            ret = do_project_update(argd['<project>'], argd['--update'])
    else:
        # Default behavior (no args)
        ret = do_list()
    return ret


def do_fields():
    """ List all the model fields. """
    
    print('\nFields for wp_project:')
    tmpobject = wp_project.objects.create(name='testitem', alias='testitem')
    tmpobject.delete()
    fieldnames = get_model_fields()
    longestname = max((len(f) for f in fieldnames))
    
    for fieldname in get_model_fields():
        attr = getattr(tmpobject, fieldname)
        fieldtype = str(type(attr))
        spacing = (' ' * (longestname - len(fieldname)))
        print('    {}{} : {}'.format(str(fieldname), spacing, fieldtype))
    return 0


def do_list():
    """ List all project names/aliases/versions. """
    
    try:
        projs = [p for p in wp_project.objects.order_by('alias')]
    except Exception as ex:
        print('\nUnable to list projects!\n{}'.format(ex))
        return 1
    if not projs:
        print('\nNo projects found!')
        return 1
    
    longestname = max((len(p.name) for p in projs))
    longestalias = max((len(p.alias) for p in projs))

    
    print('Found {} projects:'.format(str(len(projs))))
    for proj in projs:
        namespace = (' ' * ((longestname - len(proj.name)) + 1))
        aliasspace = (' ' * ((longestalias - len(proj.alias)) + 1))
        print('    {name}{namespace}({alias}){aliasspace}v. {ver}'.format(name=proj.name, 
                                                                          alias=proj.alias, 
                                                                          ver=proj.version,
                                                                          namespace=namespace,
                                                                          aliasspace=aliasspace))
    return 0


def do_project_info(ident):
    """ Get info about a single project. """
    
    proj = get_project(ident)
    if not proj:
        print('\nCan\'t find a project with that name/alias/id!: {}'.format(ident))
        return 1
    
    pinfo = get_project_info(proj)
    keynames = sorted(list(pinfo.keys()))
    longestkey = max((len(k) for k in keynames))
    
    print('\nInfo for {} ({}) v. {}:'.format(proj.name, proj.alias, proj.version))
    
    functionlines = []
    for aname in sorted(list(pinfo.keys())):
        aval = pinfo[aname]['value']
        spacing = (' ' * ((longestkey - len(aname)) + 1))
        chunkspacelen = len(spacing) + len(aname) + 8
        chunklen = 100 - chunkspacelen
        if len(aval) > chunklen:
            # Split a long line into several lines.
            chunks = []
            avalwork = aval
            while avalwork:
                chunkstr = avalwork[:chunklen]
                avalwork = avalwork[chunklen:]
                if ' ' in avalwork:
                    wrapped = avalwork[:avalwork.index(' ')]
                    chunkstr = chunkstr + wrapped
                    avalwork = avalwork[len(wrapped):]
                chunks.append(chunkstr.strip())
            chunkspacing = (' ' * chunkspacelen)
            aval = '{}\n{}'.format(chunks[0], chunkspacing) + ('\n{}'.format(chunkspacing).join(chunks[1:]))
        if pinfo[aname]['function']:
            aname = '{}()'.format(aname)
            aval = '(function)'
            functionlines.append('    {}'.format(aname))
        else:
            spacing = '{}  '.format(spacing)
            print('    {}{}: {}'.format(aname, spacing, aval))
    # print functions last.
    print('\nFunctions for {} ({}) v. {}:'.format(proj.name, proj.alias, proj.version))
    print('\n'.join(functionlines))
    
    print(' ')
    return 0
        
    
def do_project_update(ident, data):
    """ Updates a project found with ident (name/alias/id),
        data is attribute:value, or "attribute:spaced value".
        returns 0 on success, 1 on failure (with error msgs printed)
    """
    
    proj = get_project(ident)
    if not proj:
        print('\nCan\'t find a project with that name/alias/id!: {}'.format(ident))
        return 1
    
    attr, val = parse_update_data(data)
    if (not attr) or (not val):
        print('\nMissing update data!\nExpecting attribute:value or "attribute:spaced value"!')
        return 1
    
    if not hasattr(proj, attr):
        # No attr by that name.
        print('\nProject doesn\'t have that attribute!: {}'.format(attr))
        return 1
    
    # Check old setting.
    oldattr = getattr(proj, attr)
    if val == oldattr:
        print('\nproject.{} already set to: {}'.format(attr, val))
        return 1
    
    # Get attribute type.
    requiredtype = type(oldattr)
    
    # helper for converting to datetime.date type.
    def makedate(s):
        year, month, day = (int(p) for p in s.split('-'))
        return datetime.date(year, month, day)
    
    print('Required: ' + str(requiredtype))
    # Convert string arg val into actual type required.
    convertfunc = makedate if isinstance(oldattr, datetime.date) else requiredtype
    try:
        val = convertfunc(val)
        print('\nSetting project.{} = {} as {}'.format(attr, val, str(type(val))))
    except Exception as ex:
        print('\nError converting value to required type!: {}\n{}'.format(val, ex))
        return 1
    
    # Set the attribute.
    try:
        setattr(proj, attr, val)
    except Exception as ex:
        print('\nError updating project!:\n{}'.format(ex))
        return 1
    # Attribute set, now save it.
    try:
        proj.save()
    except Exception as ex:
        print('\nError saving updated project!\n{}'.format(ex))
        return 1

    
    # Success.
    print('Set and saved: project.{} = {}'.format(attr, val))
    return 0


def get_model_fields(includefunctions=False):
    # get attributes, without private attrs.
    tmpobject = wp_project.objects.create(name='testitem', alias='testitem')
    tmpobject.delete()
    attrs = [a for a in dir(tmpobject) if not a.startswith('_')]
    
    filtered = ('project', 'file_tracker_set', 'objects', 'wp_blog_set')
    # remove functions from attributes
    if not includefunctions:
        basicattrs = []
        for aname in attrs:
            # skip filtered attributes.
            if aname in filtered:
                continue
            try:
                attr = getattr(tmpobject, aname)
            except:
                print('skipping: {}'.format(aname))
                continue
            
            if not hasattr(attr, '__call__'):
                basicattrs.append(aname)
        attrs = basicattrs
    return attrs


def get_project(ident):
    """ Trys to retrieve a project by any identifier """
    
    try:
        intval = int(ident)
    except:
        intval = None
    
    # Try id
    if intval:
        proj = try_get(id=intval)
        if proj:
            return proj
    
    # Try alias
    proj = try_get(alias=ident)
    if proj:
        return proj
    
    # Try name
    proj = try_get(name=ident)
    if proj:
        return proj
    
    # Deeper search...
    proj = get_project_by_partname(ident)


def get_project_by_partname(partname, projects=None):
    """ Searches through project names/aliases for a match. """
    
    try:
        repat = re.compile(partname.lower())
    except Exception as ex:
        print('\nInvalid pattern for name!: {}\n{}'.format(partname, ex))
        return None
    
    # Retrieve list of projects if none was passed.
    if not projects:
        try:
            projects = wp_project.objects.order_by('name')
        except Exception as ex:
            print('\nUnable to retrieve projects!\n{}'.format(ex))
            return None
    
    for proj in projects:
        namematch = repat.search(proj.name.lower())
        if namematch:
            return proj
        aliasmatch = repat.search(proj.alias.lower())
        if aliasmatch:
            return proj
    
    # No match.
    return None


def get_project_info(proj, includefunctions=True):
    """ Retrieves all info about a project (wp_project object)
        returns a dict containing relavent info.
    """
    
    filtered = ('objects',)
    info = {}
    for aname in dir(proj):
        # private attributes (not part of the database model)
        if aname.startswith('_'):
            continue
        # filtered attributes (can't be accessed like this.
        if aname in filtered:
            continue
        attrval = getattr(proj, aname)
        isfunction = hasattr(attrval, '__call__')
        if isfunction and (not includefunctions):
            continue
        info[aname] = {}
        if aname.endswith('_set'):
            info[aname]['value'] = '\n'.join([str(o) for o in attrval.all()])
        else:
            info[aname]['value'] = str(attrval)
        info[aname]['function'] = isfunction
        
    return info


def parse_update_data(data):
    """ Parses the update data from the command line (attr:val) """
    if ':' in data:
        data = data.strip('"').strip("'")
        return data.split(':')
    else:
        return None,None
    
        
def try_get(**kwargs):
    """ Try doing a get(key=val), if it fails return None """
    
    try:
        proj = wp_project.objects.get(**kwargs)
    except wp_project.DoesNotExist:
        return None
    return proj


if __name__ == '__main__':
    mainargd = docopt(usage_str, version=_VERSIONSTR)
    mainret = main(mainargd)
    sys.exit(mainret)