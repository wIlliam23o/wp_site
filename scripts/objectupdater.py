"""objectupdater.py

    Helper functions for the updater scripts in this directory.
    Updates attributes of objects based on string input (command-line)

    -Christopher Welborn
"""

import datetime
import json
import pickle
import os
import re
import zlib

from sys import version_info as sysversion_info
PY3 = (sysversion_info.major == 3)

# fix for input function if py2 is used. (remove when py2 is disabled)
if not PY3:
    input = raw_input  # noqa

# Base usage string to build per-model usage strings from.
base_usage_str = """{name} v. {ver}

    Usage:
        {script} -A <file>
        {script} <identifier> -a [-F]
        {script} <identifier> [-d | -l | -j | -p]
        {script} <identifier> -u attribute:val
        {script} [-h | -v]
        {script} -f | -l

    Options:
        <identifier>           : {properid} identifier ({attrstr}).
        -a,--archive           : Show Archive string for a {lowerid}.
                                 When -F is used, data is written to file.
        -A file,--ARCHIVE file : Load object from archive file.
        -d,--delete            : Delete a {lowerid} (confirmation needed).
        -f,--fields            : List model fields.
        -F,--file              : When archiving, write to file.
        -h,--help              : Show this message.
        -j,--json              : Show JSON string for a {lowerid}.
        -l,--list              : List detailed {lowerid} info, or summary if
                                 no args were given.
        -p,--pickle            : Show Pickle string for a {lowerid}.
        -u data,--update data  : Update {lowerid} info with attribute:value
                                 or "attribute:spaced value"
        -v,--version           : Show version.
"""


def convert_attr(oldattr, val):
    """ Converts a string to the required type for a model/object.
        Arguments:
            oldattr  : Current attribute (with proper type.)
            val      : String value to convert from.

        Example:
            newdate = convert_attr(datetime.date(2001,1,1), '2012-12-12')
            newint = convert_attr(1, '456')
            newbool = convert_attr(True, 'false')
            # newdate is now a datetime.date(2012, 12, 12)
            # newint is now an int(456)
            # newbool is now a bool(False).

        It is mostly used like this though:
            mymisc = wp_misc.objects.get(alias='pidnet')
            strval = '2001-1-30'
            newval = convert_attr(mymisc.publish_date, strval)
            # newval is now a date(2001, 1, 30)
            # and can be safely set:
            # mymisc.publish_date = newval
    """
    # Retrieve conversion function needed for this type.
    # If they are the same, or the types are the same, no conversion is needed.
    if oldattr == val:
        return oldattr
    elif type(oldattr) == type(val):
        return val

    # This object needs conversion..
    convertfunc = get_convert_func(oldattr)
    # Convert the attribute to the required type.
    newattr = convertfunc(val)
    return newattr


def do_fields(model):
    """ List all the model fields. """

    print('\nFields for {}:'.format(model.__name__))
    tmpobject = model.objects.create()
    tmpobject.delete()
    fieldnames = get_model_fields(model)
    longestname = len(max(fieldnames, key=len))
    typepat = re.compile(r'\'([_\.\w]+)\'')
    for fieldname in fieldnames:
        attr = getattr(tmpobject, fieldname)
        fieldtype = str(type(int())) if fieldname == 'id' else str(type(attr))
        if fieldtype.startswith('<class'):
            # Make the type names prettier.
            typematch = typepat.search(fieldtype)
            typematchgrps = typematch.groups() if typematch else None
            if typematchgrps:
                fieldtype = typematchgrps[0]

        fieldfmt = str(fieldname).ljust(longestname)
        print('    {} : {}'.format(fieldfmt, fieldtype))
    return 0


def do_headerstr(ident, model, attrs=None):
    """ Print just the header string for an object.
        Arguments:
            ident  : name, title or part of a name to retrieve object.
            model  : model containing the objects to retrieve from
                     (wp_project, wp_blog, etc.)

        Keyword Arguments:
            attrs  : attributes to use when retrieving the object.
    """

    obj = get_object(ident, model, attrs=attrs)
    if not obj:
        print_notfound(ident, model, attrs)
        return 1
    headerstr = get_headerstr(obj)
    print('Found: {}'.format(headerstr))
    return 0


def do_object_archive(ident, model, attrs, usefile=False):
    """ Prints the archive format of an object. """
    obj = get_object(ident, model, attrs=attrs)
    mname = model.__name__
    if not obj:
        print_notfound(ident, model, attrs)
        return 1

    headerstr = get_headerstr(obj)

    try:
        arcstr = get_object_archive(obj)
    except Exception as ex:
        print('Unable to archive that {}.\n{}'.format(mname, ex))
        return 1

    if usefile:
        # Write this data to a file
        if ' ' in headerstr:
            objname = headerstr.split()[0].lower()
        else:
            objname = headerstr.lower()
        filename = '{}.{}.wparc'.format(mname, objname)
        try:
            with open(filename, 'wb') as fwrite:
                fwrite.write(arcstr)
        except (IOError, OSError) as ex:
            print('\nUnable to write file: {}\n{}'.format(filename, ex))
            return 1
        # Write success.
        print('\nWrote archive for {} to: {}\n'.format(headerstr, filename))

    else:
        # Just print this data to the terminal
        print('\nArchive for {}:\n'.format(headerstr))

        # print the archive string.
        print(arcstr)

    return 0


def do_object_fromarchive(filename):
    """ Creates an object from an archive file. """

    if not os.path.isfile(filename):
        print('\nThat file doesn\'t exist: {}'.format(filename))
        return 1

    try:
        with open(filename, 'rb') as fread:
            data = fread.read()
    except (IOError, OSError) as exread:
        print('\nUnable to read from file: {}\n{}'.format(filename, exread))
        return 1

    # Got data, create the object.
    obj = get_object_fromarchive(data)
    if obj:
        print('\nCreated object from archive: {}'.format(repr(obj)))
        return 0
    else:
        print('\nUnable to create object from archive: {}'.format(filename))
        return 1


def do_object_delete(ident, model, attrs):
    """ Delete an object from the database. """

    obj = get_object(ident, model, attrs=attrs)
    if not obj:
        print_notfound(ident, model, attrs)
        return 1

    headerstr = get_headerstr(obj)
    answer = input('Are you sure you want to delete '
                   '{} (y/n): '.format(headerstr)).lower().strip()

    if answer[0] != 'y':
        print('\nCancelled delete.\n')
        return 1

    try:
        obj.delete()
        print('\nDeleted {}'.format(repr(obj)))
        return 0
    except Exception as ex:
        print('\nUnable to delete that {}!\n{}'.format(headerstr, ex))
        return 1


def do_object_info(ident, model, attrs):
    """ Print info about an object.
        Arguments:
            ident  : name, title, or part of a name used to retrieve the object
            model  : model containing the objects to retrieve from
                     (wp_project, wp_blog, etc.)
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
        return '{}\n{}{}'.format(
            chunks[0],
            chunkspacing,
            chunkspacing.join(chunks[1:]))

    obj = get_object(ident, model, attrs=attrs)
    if not obj:
        print_notfound(ident, model, attrs)
        return 1

    pinfo = get_object_info(obj)
    keynames = sorted(list(pinfo.keys()))
    longestkey = len(max(keynames, key=len))

    # retrieve proper header string for this model.
    headerstr = get_headerstr(obj)
    print('Info for {}:'.format(headerstr))

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
    print('\nFunctions for {}:'.format(headerstr))
    print('\n'.join(functionlines))

    print(' ')
    return 0


def do_object_json(ident, model, attrs):
    """ Retrieves an objects simple JSON representation.
        Keyword arguments are the same as do_object_info().
    """

    obj = get_object(ident, model, attrs=attrs)
    mname = model.__name__
    if not obj:
        print_notfound(ident, model, attrs)
        return 1

    headerstr = get_headerstr(obj)
    try:
        jsonstr = get_object_json(obj, model)
    except Exception as ex:
        print('Unable to retrieve JSON for that {}.\n{}'.format(mname, ex))
        return 1

    print('\nJSON for {}:\n'.format(headerstr))
    print(jsonstr.replace('",', '",\n'))
    return 1


def do_object_pickle(ident, model, attrs):
    """ Retrieve a pickle string for an object. """
    obj = get_object(ident, model, attrs=attrs)
    mname = model.__name__
    if not obj:
        print_notfound(ident, model, attrs)
        return 1

    headerstr = get_headerstr(obj)
    try:
        pstr = get_object_pickle(obj)
    except Exception as ex:
        print('Unable to pickle that {}.\n{}'.format(mname, ex))
        return 1

    print('\nPickle for {}:\n'.format(headerstr))
    print(pstr)
    return 1


def do_object_update(ident, model, attrs, data=None):
    """ Updates an object found with ident (name/alias/title/id/etc.),
        data is attribute:value, or "attribute:spaced value".
        returns 0 on success, 1 on failure (with error msgs printed)
        Arguments:
            attrs  : list of attributes to search for a match.
                     (name, alias, title, etc.)
            ident  : name, title, or part of a name to retrieve object with.
            model  : model to retrieve objects from.
                     (wp_project, wp_blog, etc.)

        Keyword Arguments:
            data   : update data in the form of
                     (attr:val, or "attr:space value")
                     Must be able to do getattr(obj, attr).
    """

    obj = get_object(ident, model, attrs=attrs)
    if not obj:
        print_notfound(ident, model, attrs)
        return 1

    return update_object_bydata(obj, data)


def get_convert_func(oldattr):
    """ Retrieves the conversion function needed based on oldattrs type. """
    # Get attribute type.
    requiredtype = type(oldattr)

    def makebool(s):
        """ helper for converting to bool (since bool("False") == True). """
        trues = ('true', '1')
        falses = ('false', '0')
        if s.lower() in trues:
            return True
        elif s.lower() in falses:
            return False
        else:
            print('\nError in makebool(). Value '
                  '\'{}\' was not found in acceptable values!'.format(s))
            return False

    def makedate(s):
        """ helper for converting to datetime.date type. """
        return datetime.date(*parse_date(s))

    def makedatetime(s):
        """ helper for converting to datetime.datetime type.
            (tzinfo is not handled yet.)
        """
        return datetime.datetime(*parse_datetime(s))

    def maketime(s):
        """ helper for converting to datetime.time type.
            (tzinfo is not handled yet.)
        """
        return datetime.time(*parse_time(s))

    # Convert string arg val into actual type required.
    # Some types are kinda 'dumb', and need help to be converted.
    convertfunc = None
    # Map to conversion functions for 'dumb' types.
    helpertypes = {datetime.date: makedate,
                   datetime.datetime: makedatetime,
                   datetime.time: maketime,
                   bool: makebool,
                   }
    # Find out if the old attribute is a 'dumb' type and
    # assign the conversion function.
    for helptype in helpertypes.keys():
        if isinstance(oldattr, helptype):
            convertfunc = helpertypes[helptype]
            break
    # No conversion function is set yet, it's not a 'dumb' type.
    if convertfunc is None:
        convertfunc = requiredtype

    # Return the function that will be used.
    return convertfunc


def get_headerstr(obj):
    """ Get header string to print for this model. (wp_project, wp_blog, etc.)
        Arguments:
            model : model this object belongs to. (to determine header style.)
            obj   : object to get header info from. (obj.name, obj.title, etc.)
    """
    # TODO: This could be built into the model, like a 'console_repr' attribute
    # TODO: ..then get_headerstr() would be: obj.console_repr()
    # TODO: ..so this hardcoded mess (attrs as strings that are loaded) dies.

    # Default header string.
    headerstr = 'object'
    if not obj:
        return headerstr
    # Header string for various models.
    headerstrings = {
        'wp_project': {
            'format': '{} ({}) v. {}',
            'attrs': ('name', 'alias', 'version'),
        },
        'wp_image': {
            'format': '{} - {} ({})',
            'attrs': ('image_id', 'title', 'filename')
        },
        'wp_misc': {
            'format': '{} ({}) v. {}',
            'attrs': ('name', 'alias', 'version'),
        },
        'wp_blog': {
            'format': '{}',
            'attrs': ('title',),
        },
        'wp_paste': {
            'format': '{} [{}] {}',
            'attrs': ('publish_date', 'paste_id', 'title')
        },
        'file_tracker': {
            'format': '{}',
            'attrs': ('filename',),
        },

    }
    # Get current model name.
    try:
        mname = obj.__class__.__name__
    except Exception as ex:
        print('\nError retrieving model name!:\n{}'.format(ex))
        return headerstr

    if mname not in headerstrings.keys():
        print('\nget_headerstr(): No info for this model!: {}'.format(mname))
        return headerstr

    # Try getting real attribute values from attribute names
    attrnames = headerstrings[mname]['attrs']
    try:
        attrvals = [getattr(obj, a) for a in attrnames]
    except Exception as ex:
        print('\nget_headerstr(): Error retrieving attributes: '
              '{}\n{}'.format(','.join(attrnames), ex))
        return headerstr

    # Try formatting header string with attribute values.
    headerformat = headerstrings[mname]['format']
    try:
        headerstr = headerformat.format(*attrvals)
    except Exception as ex:
        print('\nget_headerstr(): Error formatting header string: '
              '{}\n{}'.format(headerformat, ex))
        return headerstr
    # success
    return headerstr


def get_model_fields(model, includefunctions=False, exclude=None):
    # get attributes, without private attrs.
    if hasattr(model, 'alias'):
        testattrs = {'alias': 'testitem'}
    elif hasattr(model, 'slug'):
        testattrs = {'slug': 'testitem'}
    else:
        testattrs = {}
    if hasattr(model, 'name'):
        testattrs['name'] = 'testitem'
    elif hasattr(model, 'title'):
        testattrs['title'] = 'testitem'

    tmpobject = model.objects.create(**testattrs)
    tmpobject.delete()
    attrs = [a for a in dir(tmpobject) if not a.startswith('_')]
    # Default excluded fields.
    defaultfiltered = ['project', 'file_tracker_set',
                       'objects', 'wp_blog_set', 'pk', 'children']
    # Add user excluded fields.
    filtered = defaultfiltered + exclude if exclude else defaultfiltered

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
                # print('skipping: {}'.format(aname))
                continue

            if not hasattr(attr, '__call__'):
                basicattrs.append(aname)
        attrs = basicattrs
    return attrs


def get_object(ident, model, attrs=None):
    """ Trys to retrieve an object by any identifier
        Arguments:
            ident  : name, alias, title, id, etc. to get object by.
            model  : model containing objects to search/retrieve
                     (wp_project, wp_blog, etc.)

        Keyword Arguments:
            attrs  : attributes to search.
                     (id is always searched because all models contain an id.)
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


def get_object_archive(obj):
    """ Retrieve archive format for an object.
        For storing and recreating objects at a later date.
    """

    # TODO: This should be on the model itself.
    # TODO: ..like: wp_blog.archive(filename=None), .archive_bytes()

    model = obj.__class__
    # Can't recreate an object with these fields.
    excludes = ['id', 'date_hierarchy', 'get_latest_by']
    modelfields = get_model_fields(model, exclude=excludes)

    # Types that need to be stringified.
    stringify = (datetime.date,
                 datetime.datetime,
                 datetime.time,
                 bool)

    # Create blank date, with model type saved.
    data = {'original_model': model}
    for field in modelfields:
        try:
            val = getattr(obj, field)
        except Exception as ex:
            print('Unable to archive attribute: {}\n{}'.format(field, ex))
            continue
        for stringedtype in stringify:
            if isinstance(val, stringedtype):
                val = str(val)

        data[field] = val

    # We now have a dict with attrs: values, we need to serialize it.
    pickledata = pickle.dumps(data)
    compressed = zlib.compress(pickledata)
    return compressed


def get_object_fromarchive(data):
    """ Creates an object from an archive. """

    # TODO: This should be on the model itself.
    # TODO: ..like: wp_blog.from_archive_bytes(b), .from_archive_file(filename)
    if isinstance(data, str):
        # We need bytes for these operations.
        data = bytes(data, 'utf-8')

    try:
        decompressed = zlib.decompress(data)
    except Exception as excomp:
        print('\nUnable to decompress this data!\n{}'.format(excomp))
        return None
    try:
        objdata = pickle.loads(decompressed)
    except Exception as expickle:
        print('\nUnable to unpickle this data!\n{}'.format(expickle))
        return None

    # We now have a dict with attrs: val
    # Get the model we will be using
    model = objdata['original_model']
    objdata.pop('original_model')
    # Original model was popped so we can pass all attributes to the
    # create() function for this model, and it won't get in the way.
    # See if this object already exists...

    try:
        obj = model.objects.get(**objdata)
        print('\nThis object already exists!: {}'.format(repr(obj)))
    except (model.DoesNotExist, model.MultipleObjectsReturned):
        try:
            obj = model.objects.create()
        except Exception as excreate:
            print('\nUnable to create this object!\n{}'.format(excreate))
            return None

    # Got a blank object, now fill in the info.
    for aname in objdata.keys():
        oldval = getattr(obj, aname)
        newval = convert_attr(oldval, objdata[aname])
        setattr(obj, aname, newval)

    obj.save()

    return obj


def get_object_by_partname(partname, model, attrs=None, objects=None):
    """ Searches through object attributes for a match.
        (name, alias, title, filename, etc.)
        Arguments:
            partname  : regex or text to match attribute value with.
            model     : model containing objects to search
                        (if no objects were provided.)

        Keyword Arguments:
            attrs     : attributes to search to find a match
                        (name, alias, title, etc.)
            objects   : objects to search
                        (won't fetch them again if you provide them here.)
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
        print('\nError determining orderby for: '
              '{}\n{}'.format(model.__name__, ex))
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


def get_object_json(obj):
    """ Return simple json representation of an objects attributes. """

    data = {}
    model = obj.__class__
    for fieldname in get_model_fields(model):
        data[fieldname] = str(getattr(obj, fieldname))

    return json.dumps(data)


def get_object_pickle(obj):
    """ Returns a pickle string for this object. """

    try:
        pstr = pickle.dumps(obj)
        return pstr
    except Exception as ex:
        print('Unable to pickle that object!\n{}'.format(ex))
    return ''


def get_object_from_pickle(pstr):
    """ Returns an object from a pickle string. """

    try:
        o = pickle.loads(pstr)
        return o
    except Exception as ex:
        print('Unable to get an object from that string!\n{}'.format(ex))
    return None


def get_scriptname(argv0):
    """ Retrieve the short name that a script was called by.
        No .py, no /path.
        Arguments:
            argv0  :  the sys.argv[0] for whatever script you are using.
    """

    shortname = os.path.split(argv0)[1]
    return shortname[:-3] if shortname.endswith('.py') else shortname


def parse_date(s):
    """ Parses a str(date) and returns year, month, day.
        Does not return a date() because it may need to be used
        in creating a datetime.
    """
    if '-' not in s:
        return 1900, 0, 0

    year, month, day = (int(p) for p in s.split('-'))
    return year, month, day


def parse_datetime(s):
    """ Parses a str(datetime) and returns:
            year, month, day, hour, minute, second, microsec
        Does not return a datetime() because the info may be used
        elsewhere.
    """

    if ' ' not in s:
        return 1900, 0, 0, 0, 0, 0, 0

    datepart, timepart = s.split(' ')
    year, month, day = parse_date(datepart)
    hour, minute, second, microsec = parse_time(timepart)
    return year, month, day, hour, minute, second, microsec


def parse_time(s):
    """ Parses a str(time) and returns hour, min, sec, microsec.
        Does not return time() because it may need to be used
        in creating a datetime.
    """
    if ':' not in s:
        return 0, 0, 0, 0

    hourpart, minutepart, secondpart = s.split(':')
    hour = int(hourpart)
    minute = int(minutepart)
    if '.' in secondpart:
        second, microsec = (int(p) for p in secondpart.split('.'))
    else:
        second = int(secondpart)
        microsec = 0

    return hour, minute, second, microsec


def parse_update_data(data):
    """ Parses the update data from the command line (attr:val) """
    if ':' in data:
        data = data.strip('"').strip("'")
        return data.split(':')
    else:
        return None, None


def print_notfound(ident, model, attrs):
    """ Print a message when objects aren't found.
        Kept here so the message is consistent.
    """
    mname = model.__name__
    print('\nCan\'t find a {modelname} '.format(modelname=mname) +
          'with that {attrstr}'.format(attrstr='/'.join(attrs)) +
          '/id!: {identstr}'.format(identstr=ident))


def try_get(model, **kwargs):
    """ Try doing a get(key=val), if it fails return None """

    try:
        proj = model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None
    return proj


def update_object_bydata(obj, data, **kwargs):
    """ Updates an attributes of an object by raw command-line arg data
        ("attribute:value").
        see: update_object()

        Keyword Arguments:
            (same as update_object())
    """
    attr, val = parse_update_data(data)
    if (not attr) or (not val):
        print('\nMissing update data!\nExpecting attribute:value '
              'or "attribute:spaced value"!')
        return 1

    return update_object(obj, attr, val, **kwargs)


def update_object(obj, attr, val, objectname=None):
    """ Updates an attribute of an object, where attr is a string.
        Example:
            update_object(wp_project.objects.all()[0], 'name', 'First Project')

        Arguments:
            obj  : object to update.
            attr : attribute to change (hasattr(obj, attr) must be True))
            val  : value to assign attribute (string get converted to
                   required type.)
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

    try:
        # Use the conversion function to make sure proper types are set
        # (in Django/Database)
        val = convert_attr(oldattr, val)
        # A little bit 'prettier' type string than <type 'this'>.
        typestr = str(type(val)).strip('<').strip('>')
        print('\nSetting {}.{} = {} as {}'.format(objname, attr, val, typestr))
    except Exception as ex:
        print('\nError converting value to required type!: '
              '{}\n{}'.format(val, ex))
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
