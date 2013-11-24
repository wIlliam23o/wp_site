'''misc.types

    Welborn Productions - Misc - Types
    Provides type/language classifiers for Misc objects
    Created on Oct 20, 2013

@author: Christopher Welborn
'''


class MiscType(object):

    """ Base class for any MiscType. """

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

    @classmethod
    def make_misctype(cls, name, desc, **kwargs):
        """ Make a new MiscType.
            Arguments:
                desc       : Description for Django field-choices
                name       : Friendly name for Django field-choices

            Keyword Arguments: (same as __init__)
                _attrname  : name.lower(), can be accessed like:
                             MiscTypes._attrname
                warning    : Any warning associated with this type.
                             (retrieved in misc.index.html)
        """
        return cls(name, desc, **kwargs)

    @classmethod
    def make_misctypes(cls, misctypes):
        """ Creates a list of MiscTypes, from a list of
            tuples (name, description).
            Returns the list.
        """
        made = []
        for name, desc in misctypes:
            made.append(cls.make_misctype(name, desc))
        return made

# TODO: Make MiscTypes, comparable, warnings, makeable. Fix Them!
# Create MiscTypes...
all_types = (MiscType('Code', 'Code File', viewable=True),
             MiscType('Snippet', 'Code Snippet', viewable=True),
             MiscType('Script', 'Script File', viewable=True),
             MiscType('Text', 'Text File', viewable=True),
             MiscType('None', 'None', viewable=True),
             MiscType('Executable', 'Executable File'),
             MiscType('Archive', 'Archive File'),
             MiscType('XChat', 'XChat Script', viewable=True,
                      warning=('To use these xchat scripts you can either '
                               'drop them in the XChat2 config directory '
                               '(usually ~/.xchat2), or load the script '
                               'manually by going to Window -> Plugins -> '
                               'Scripts -> Load...')),
             )


def add_misctype(mt):
    """ Add a MiscType to this collection. """
    attrname = mt.attrname()
    setattr(MiscTypes, attrname, mt)


def add_misctype_list(misctypes):
    """ Add a list of MiscType to this collection. """
    for mt in misctypes:
        add_misctype(mt)


def generate_fieldchoices():
    choices = []
    for aname in [a for a in dir(MiscTypes) if not a.startswith('_')]:
        val = getattr(MiscTypes, aname)
        if isinstance(val, MiscType):
            choices.append((val, val.description))
    # set MiscTypes.fieldchoices
    #setattr(MiscTypes, 'fieldchoices', choices)
    MiscTypes.fieldchoices = choices


def misctype_byname(s):
    """ Determine a misc type by string name. """
    for aname in [a for a in dir(MiscTypes) if not a.startswith('_')]:
        val = getattr(MiscTypes, aname)
        if hasattr(val, 'name'):
            if val.name == s:
                return val
    return None


class MiscTypes:

    """ Various MiscTypes, setup directly after init. """
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

    # Choices for Django admin
    fieldchoices = (('Python', 'Python (any)'),
                    ('Python 2', 'Python 2+'),
                    ('Python 3', 'Python 3+'),
                    ('Bash', 'Bash'),
                    ('C', 'C'),
                    ('C++', 'C++'),
                    ('Perl', 'Perl'),
                    ('Visual Basic', 'Visual Basic'),
                    ('Stackless Python', 'Stackless Python'),
                    ('PyPy', 'PyPy'),
                    ('None', 'None'),
                    )
