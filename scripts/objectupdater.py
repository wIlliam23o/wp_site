"""objectupdater.py

    Helper functions for the updater scripts in this directory.
    Updates attributes of objects based on string input (command-line)

    -Christopher Welborn
"""

import datetime
import os
import re

# Base usage string to build per-model usage strings from.
base_usage_str = """{name} v. {ver}

    Usage:
        {script} <identifier> [-l]
        {script} <identifier> -u attribute:val
        {script} [-h | -v]
        {script} -f | -l
        
    Options:
        <identifier>           : {properid} identifier ({attrstr}).
        -f,--fields            : List model fields.
        -h,--help              : Show this message.
        -l,--list              : List detailed {lowerid} info, or summary if no args were given.
        -u data,--update data  : Update {lowerid} info with attribute:value or "attribute:spaced value"
        -v,--version           : Show version.     
"""


def do_fields(model):
    """ List all the model fields. """
    
    print('\nFields for {}:'.format(model.__name__))
    tmpobject = model.objects.create()
    tmpobject.delete()
    fieldnames = get_model_fields(model)
    longestname = max((len(f) for f in fieldnames))
    
    for fieldname in fieldnames:
        attr = getattr(tmpobject, fieldname)
        fieldtype = str(type(int)) if fieldname == 'id' else str(type(attr))
        spacing = (' ' * (longestname - len(fieldname)))
        print('    {}{} : {}'.format(str(fieldname), spacing, fieldtype))
    return 0


def do_headerstr(ident, model, attrs=None):
    """ Print just the header string for an object.
        Arguments:
            ident  : name, title or part of a name to retrieve object.
            model  : model containing the objects to retrieve from (wp_project, wp_blog, etc.)

        Keyword Arguments:
            attrs  : attributes to use when retrieving the object.
    """

    obj = get_object(ident, model, attrs=attrs)
    if not obj:
        print('Can\'t find an object with that {attrstr}/id!: {identstr}'.format(attrstr='/'.join(attrs),
                                                                                 identstr=ident))
        return 1
    headerstr = get_headerstr(obj)
    if headerstr:
        print('Found: {}'.format(headerstr))
    else:
        print('Can\'t find a proper info string with: {}'.format(ident))
        return 1
    return 0


def do_object_info(ident, model, attrs=None):
    """ Print info about an object.
        Arguments:
            ident  : name, title, or part of a name used to retrieve the object.
            model  : model containing the objects to retrieve from (wp_project, wp_blog, etc.)
        Keyword Arguments:
            attrs  : attributes to use when retrieving the object.
    """

    def formatchunks(val, chnklen, chnkspacelen):
        """ Split a long line into several lines. """
        chunks = []
        avalwork = val
        while avalwork:
            chunkstr = avalwork[:chnklen]
            avalwork = avalwork[chnklen:]
            if ' ' in avalwork:
                wrapped = avalwork[:avalwork.index(' ')]
                chunkstr = chunkstr + wrapped
                avalwork = avalwork[len(wrapped):]
            chunks.append(chunkstr.strip())
        chunkspacing = (' ' * chnkspacelen)
        return '{}\n{}'.format(chunks[0], chunkspacing) + ('\n{}'.format(chunkspacing).join(chunks[1:]))

    obj = get_object(ident, model, attrs=attrs)
    if not obj:
        print('Can\'t find an object with that {attrstr}/id!: {identstr}'.format(attrstr='/'.join(attrs),
                                                                                 identstr=ident))
        return 1

    pinfo = get_object_info(obj)
    keynames = sorted(list(pinfo.keys()))
    longestkey = max((len(k) for k in keynames))

    # retrieve proper header string for this model.
    headerstr = get_headerstr(obj)
    if headerstr:
        print('Info for {}:'.format(headerstr))
    else:
        print('Info:')

    functionlines = []
    for aname in sorted(list(pinfo.keys())):
        aval = pinfo[aname]['value']
        spacing = (' ' * ((longestkey - len(aname)) + 1))
        chunkspacelen = len(spacing) + len(aname) + 8
        chunklen = 100 - chunkspacelen
        # Split newline stuff.
        if '\n' in aval:
            newformat = []
            splitlines = aval.split('\n')
            for line in splitlines[1:]:
                newformat.append('{}{}'.format((' ' * chunkspacelen), line))
            aval = '{}\n{}'.format(splitlines[0], '\n'.join(newformat))
        elif len(aval) > chunklen:
            aval = formatchunks(aval, chunklen, chunkspacelen)

        # Grab function, printed later...
        if pinfo[aname]['function']:
            aname = '{}()'.format(aname)
            aval = '(function)'
            functionlines.append('    {}'.format(aname))
        else:
            spacing = '{}  '.format(spacing)
            print('    {}{}: {}'.format(aname, spacing, aval))
    # print functions last.
    if headerstr:
        print('\nFunctions for {}:'.format(headerstr))
    else:
        print('\nFunctions:')
    print('\n'.join(functionlines))
    
    print(' ')
    return 0
        

def do_object_update(ident, data, model, attrs=None):
    """ Updates an object found with ident (name/alias/title/id/etc.),
        data is attribute:value, or "attribute:spaced value".
        returns 0 on success, 1 on failure (with error msgs printed)
        Arguments:
            ident  : name, title, or part of a name to retrieve object with.
            data   : update data in the form of (attr:val, or "attr:space value")
                     hasattr(object, attr) must be True.
            model  : model to retrieve objects from. (wp_project, wp_blog, etc.)

        Keyword Arguments:
            attrs  : attributes to search for a match (name, alias, title, etc.)
    """
    
    if (not attrs) or (not model):
        print('\nAttributes and Model must be supplied! Programmer error!')
        return 1
    mname = model.__name__
    obj = get_object(ident, model, attrs=attrs)
    if not obj:
        print('\nCan\'t find a {modelname} with that {attrstr}/id!: {identstr}'.format(modelname=mname,
                                                                                       attrstr='/'.join(attrs),
                                                                                       identstr=ident))
        return 1
    
    return update_object_bydata(obj, data)


def get_headerstr(obj):
    """ Get header string to print for this model. (wp_project, wp_blog, etc.)
        Arguments:
            model : model this object belongs to. (to determine header style.)
            obj   : object to get header info from. (obj.name, obj.title, etc.)
    """

    if not obj:
        return None
    # Header string for various models.
    headerstrings = {'wp_project': {'format': '{} ({}) v. {}', 
                                    'attrs': ('name', 'alias', 'version'),
                                    },
                     'wp_misc': {'format': '{} ({}) v. {}',
                                 'attrs': ('name', 'alias', 'version'),
                                 },
                     'wp_blog': {'format': '{}',
                                 'attrs': ('title',),
                                 },
                     'file_tracker': {'format': '{}',
                                      'attrs': ('filename',),
                                      },
                     }
    # Get current model name.                
    try:
        mname = obj.__class__.__name__
    except Exception as ex:
        print('\nError retrieving model name!:\n{}'.format(ex))
        return None

    if not mname in headerstrings.keys():
        print('\nget_headerstr(): No info for this model!: {}'.format(mname))
        return None

    # Try getting real attribute values from attribute names
    attrnames = headerstrings[mname]['attrs']
    try:
        attrvals = [getattr(obj, a) for a in attrnames]
    except Exception as ex:
        print('\nget_headerstr(): Error retrieving attributes: {}\n{}'.format(','.join(attrnames), ex))
        return None

    # Try formatting header string with attribute values.
    headerformat = headerstrings[mname]['format']
    try:
        headerstr = headerformat.format(*attrvals)
    except Exception as ex:
        print('\nget_headerstr(): Error formatting header string: {}\n{}'.format(headerformat, ex))
        return None
    # success
    return headerstr


def get_model_fields(model, includefunctions=False):
    # get attributes, without private attrs.
    tmpobject = model.objects.create(name='testitem', alias='testitem')
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
                #print('skipping: {}'.format(aname))
                continue
            
            if not hasattr(attr, '__call__'):
                basicattrs.append(aname)
        attrs = basicattrs
    return attrs


def get_object(ident, model, attrs=None):
    """ Trys to retrieve an object by any identifier
        Arguments:
            ident  : name, alias, title, id, etc. to get object by.
            model  : model containing objects to search/retrieve (wp_project, wp_blog, etc.)

        Keyword Arguments:
            attrs  : attributes to search. (id is always searched because all models contain an id.)
    """
    
    try:
        intval = int(ident)
    except:
        intval = None
    
    # Try id
    if intval:
        obj = try_get(model, id=intval)
        if obj:
            return obj
    
    # Try attributes.
    if not attrs:
        print('\nNo attributes supplied to objectupdater.get_object()! Programmer error.')
        return None
    # Build keyword args for attributes, and get().
    attrset = {}
    for aname in attrs:
        attrset[aname] = {aname: ident}

    # Try getting object by the attribute.
    for aname in attrs:
        argset = attrset[aname]
        obj = try_get(model, **argset)
        if obj:
            return obj

    # Deeper search (uses regex to search attributes)...
    obj = get_object_by_partname(ident, model, attrs=attrs)

    return obj


def get_object_by_partname(partname, model, attrs=None, objects=None):
    """ Searches through object attributes for a match. (name, alias, title, filename, etc.) 
        Arguments:
            partname  : regex or text to match attribute value with.
            model     : model containing objects to search (if no objects were provided.)

        Keyword Arguments:
            attrs     : attributes to search to find a match (name, alias, title, etc.)
            objects   : objects to search (won't fetch them again if you provide them here.)
    """
    
    if not attrs:
        print('\nNo attributes to search with! Programmer error!')
        return None

    try:
        repat = re.compile(partname.lower())
    except Exception as ex:
        print('\nInvalid pattern for name!: {}\n{}'.format(partname, ex))
        return None
    
    # Determing orderby
    orderbyinfo = {'wp_project': 'name',
                   'wp_blog': '-posted',
                   'wp_misc': 'name',
                   'file_tracker': 'filename',
                   }
    try:
        orderby = orderbyinfo[model.__name__]
    except Exception as ex:
        print('\nError determining orderby for: {}\n{}'.format(model.__name__, ex))
        return None

    # Retrieve list of projects if none was passed.
    if not objects:
        try:
            objects = model.objects.order_by(orderby)
        except Exception as ex:
            print('\nUnable to retrieve objects!\n{}'.format(ex))
            return None

    # Search objects.
    for obj in objects:
        # Search attributes of object.
        for aname in attrs:
            try:
                attrval = getattr(obj, aname)
                if hasattr(attrval, 'lower'):
                    attrval = attrval.lower()
            except Exception as ex:
                print('\nError retrieving attribute {}:\n{}'.format(aname, ex))
                continue
            attrmatch = repat.search(attrval)
            if attrmatch:
                return obj
    
    # No match.
    return None


def get_object_info(obj, includefunctions=True):
    """ Retrieves all info about a model object (wp_project, wp_blog, etc.)
        returns a dict containing relavent info.
    """
    
    filtered = ('objects',)
    info = {}
    for aname in dir(obj):
        # private attributes (not part of the database model)
        if aname.startswith('_'):
            continue
        # filtered attributes (can't be accessed like this.
        if aname in filtered:
            continue
        attrval = getattr(obj, aname)
        # Filter functions if applicable
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


def get_scriptname(argv0):
    """ Retrieve the short name that a script was called by.
        No .py, no /path.
        Arguments:
            argv0  :  the sys.argv[0] for whatever script you are using.
    """

    shortname = os.path.split(argv0)[1]
    return shortname[:-3] if shortname.endswith('.py') else shortname


def parse_update_data(data):
    """ Parses the update data from the command line (attr:val) """
    if ':' in data:
        data = data.strip('"').strip("'")
        return data.split(':')
    else:
        return None, None


def try_get(model, **kwargs):
    """ Try doing a get(key=val), if it fails return None """
    
    try:
        proj = model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None
    return proj


def update_object_bydata(obj, data, **kwargs):
    """ Updates an attributes of an object by raw command-line arg data ("attribute:value").
        see: update_object()

        Keyword Arguments:
            (same as update_object())
    """
    attr, val = parse_update_data(data)
    if (not attr) or (not val):
        print('\nMissing update data!\nExpecting attribute:value or "attribute:spaced value"!')
        return 1

    return update_object(obj, attr, val, **kwargs)


def update_object(obj, attr, val, objectname=None):
    """ Updates an attribute of an object, where attr is a string.
        Example:
            update_object(wp_project.objects.all()[0], 'name', 'First Project')

        Arguments:
            obj  : object to update.
            attr : attribute to change (hasattr(obj, attr) must be True))
            val  : value to assign attribute (string get converted to required type.)
    """
    
    try:
        objname = obj.__class__.__name__
    except:
        objname = 'object'

    if not hasattr(obj, attr):
        # No attr by that name.
        print('\n{} doesn\'t have that attribute!: {}'.format(objname, attr))
        return 1
    
    # Check old setting.
    oldattr = getattr(obj, attr)
    if val == oldattr:
        print('\n{}.{} already set to: {}'.format(objname, attr, val))
        return 1
    
    # Get attribute type.
    requiredtype = type(oldattr)
    
    # helper for converting to datetime.date type.
    def makedate(s):
        year, month, day = (int(p) for p in s.split('-'))
        return datetime.date(year, month, day)
    
    # Convert string arg val into actual type required.
    convertfunc = makedate if isinstance(oldattr, datetime.date) else requiredtype
    try:
        val = convertfunc(val)
        print('\nSetting {}.{} = {} as {}'.format(objname, attr, val, str(type(val))))
    except Exception as ex:
        print('\nError converting value to required type!: {}\n{}'.format(val, ex))
        return 1
    
    # Set the attribute.
    try:
        setattr(obj, attr, val)
    except Exception as ex:
        print('\nError updating {}!:\n{}'.format(objname, ex))
        return 1
    # Attribute set, now save it.
    try:
        obj.save()
    except Exception as ex:
        print('\nError saving updated {}!\n{}'.format(objname, ex))
        return 1

    # Success.
    print('Set and saved: {}.{} = {}'.format(objname, attr, val))
    return 0
