'''misc.types

    Welborn Productions - Misc - Types
    Provides type/language classifiers for Misc objects
    Created on Oct 20, 2013

@author: Christopher Welborn
'''
import logging

log = logging.getLogger('wp.misc.types')


class MiscType(object):

    """ Base class for any MiscType,
        They have all of this magic stuff right now because
        decisions are made based on the .filetype (MiscType) of a
        wp_misc. Views and Templates need to know whether or not
        it is a 'viewable' file type (viewed with the viewer app),
        and whether there is a 'warning' associated with the type.
        Like little warnings that say 'To install XChat scripts...'
    """

    def __init__(self, name, desc, **kwargs):
        """ Create a MiscType.
            Arguments:
                name      :  Short name for this type. (viewed on the site)
                desc      :  Friendly name, for Django field choices.

            Keyword Arguments:
                _attrname : Attribute name for MiscTypes
                            (if name.lower() isn't good enough for you.)
                viewable  : Boolean, True if this type is viewable with the
                            viewer.
                warning   : Any warning (string) associated with this type.
        """
        _attrname = kwargs.get('_attrname', None)
        viewable = kwargs.get('viewable', False)
        warning = kwargs.get('warning', None)

        self._attrname = _attrname if _attrname else name.lower()
        self.name = name
        self.description = desc
        self.warning = warning
        self.fieldchoice = (self.name, self.description)
        self.viewable = viewable

    def __eq__(self, other):
        """ Compare two MiscTypes """
        if hasattr(other, 'name'):
            return self.name == other.name
        elif hasattr(other, 'lower'):
            return self.name == other
        else:
            raise ValueError('Can\'t compare '
                             '{} to MiscType!'.format(str(type(other))))

    def __str__(self):
        """ String representation for this type (viewable on site) """
        return str(self.name)

    def __repr__(self):
        """ Same as __str__ right now. """
        return str(self.name)

    def attrname(self):
        """ Returns _attrname or make one up on the fly. """
        if self._attrname:
            return self._attrname
        else:
            self._attrname = self.name.lower()
            return self._attrname


# Create MiscTypes...
all_types = (
    MiscType('Code', 'Code File', viewable=True),
    MiscType('Snippet', 'Code Snippet', viewable=True),
    MiscType('Script', 'Script File', viewable=True),
    MiscType('Text', 'Text File', viewable=True),
    MiscType('None', 'None', viewable=True),
    MiscType('Executable', 'Executable File'),
    MiscType('Archive', 'Archive File'),
    MiscType(
        'HexChat', 'HexChat Script', viewable=True,
        warning=(
            'To use these xchat scripts you can either '
            'drop them in the HexChat config directory '
            '(usually ~/.config/hexchat/addons), '
            'or load the script manually by going to:\n'
            '<kbd>Window -> Plugins &amp; Scripts -> Load...</kbd>')),
    MiscType(
        'XChat', 'XChat Script', viewable=True,
        warning=(
            'To use these xchat scripts you can either '
            'drop them in the XChat2 config directory '
            '(usually ~/.xchat2), or load the script '
            'manually by going to:\n'
            '<kbd>Window -> Plugins &amp; Scripts -> Load...</kbd>')),
)

# Generate a map from String value to Actual value for MiscTypes.
# used to look up MiscTypes by name later (misctype_byname())
types_info = {mt.name: mt for mt in all_types}


def add_misctype(mt):
    """ Add a MiscType to this collection. """
    attrname = mt.attrname()
    setattr(MiscTypes, attrname, mt)


def add_misctype_list(misctypes):
    """ Add a list of MiscType to MiscTypes. """
    for mt in misctypes:
        add_misctype(mt)


def generate_fieldchoices():
    """ Generates a field choices list for Django's admin.
        Uses MiscType().name and .description, where .name is
        the database entry, and .description is in the dropdown
        menu for admin.
    """
    choices = []
    for misctype in types_info.values():
        choices.append((misctype.name, misctype.description))

    # Sort choices, apparently Django can't do this for you.
    choices = sorted(choices, key=lambda c: c[1])
    # set MiscTypes.fieldchoices for use in
    # misc.models.wp_misc.filetype field choices.
    MiscTypes.fieldchoices = choices


def misctype_byname(s):
    """ Retrieve a misc type by string name.
    """
    # TODO: Make django/database handle actual MiscTypes.
    #   This is here because the database started out
    #   storing simple string values, everything has been converted
    #   over to this smarter MiscType (except for the database.)
    #   When the model/database can handle actual MiscType objects
    #   this can be removed.

    try:
        misctype = types_info[s]
    except (KeyError, ValueError):
        # This type doesn't exist.
        log.error('Can\'t find that misctype: {}'.format(s))
        return None
    return misctype


class MiscTypes:

    """ Various MiscTypes, setup directly after init
        of this class. Holds attributes that refer to an actual MiscType.
        This allows you to do things like:
            thistype = misctype_byname(mymiscobj.filetype)
            if thistype.viewable:
                # ... code to view misc object here.
                if thistype.warning:
                    # Show warning for this type.
                    print(thistype.warning)
        The attributes for this class are dynamically created during the init
        for this module.
        (see global level function calls below)
    """
    pass

add_misctype_list(all_types)
generate_fieldchoices()


class Lang:

    """ Kindof an ENUM with helper functions. Instances should not be created.
        Example:
            m = wp_misc.objects.create(filetype=MiscType.script,
                                       language=Lang.python)
            if m.language in (Lang.python, Lang.py2, Lang.py3):
                print('This is file was written in Python.')
                print('Specifically: {}'.format(m.language))
    """
    python = 'Python'
    py = 'Python'
    python2 = 'Python 2'
    py2 = 'Python 2'
    python3 = 'Python 3'
    py3 = 'Python 3'
    pypy = 'PyPy'
    bash = 'Bash'
    c = 'C'
    cpp = 'C++'
    cplusplus = 'C++'
    perl = 'Perl'
    pl = 'Perl'
    visualbasic = 'Visual Basic'
    vb = 'Visual Basic'
    none = 'None'
    stackless = 'Stackless Python'

    @staticmethod
    def combine(*args):
        """ Combine 2 or more Lang attributes. """
        return ','.join(args)

    @staticmethod
    def split(langstring):
        """ The reverse of combine. """
        if ',' in langstring:
            return [l.strip() for l in langstring.split(',')]
        else:
            return [langstring.strip()]

    # Choices for misc.models.wp_misc.language admin fieldchoices.
    # Sort these manually here, by description. Django doesn't do it for you.
    fieldchoices = [('Bash', 'Bash'),
                    ('C', 'C'),
                    ('C++', 'C++'),
                    ('None', 'None'),
                    ('Perl', 'Perl'),
                    ('PyPy', 'PyPy'),
                    ('Python', 'Python (any)'),
                    ('Python 2', 'Python 2+'),
                    ('Python 3', 'Python 3+'),
                    ('Stackless Python', 'Stackless Python'),
                    ('Visual Basic', 'Visual Basic'),
                    ]
