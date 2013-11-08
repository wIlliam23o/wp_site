'''misc.types
    
    Welborn Productions - Misc - Types
    Provides type/language classifiers for Misc objects
    Created on Oct 20, 2013

@author: Christopher Welborn
'''

class MiscType:
    """ Kindof an ENUM with helper functions. Instances should not be created.
        Ex:
            m = wp_misc.objects.create(filetype=MiscType.script, language=Lang.python)
            if MiscType.is_viewable(m.filetype):
                print('You can view this misc object.')
    """
    code = 'Code'
    snippet = 'Snippet'
    script = 'Script'
    text = 'Text'
    txt = 'Text'
    none = 'None'
    executable = 'Executable'
    exe = 'Executable'
    archive = 'Archive'
    arc = 'Archive'
    
    @staticmethod
    def combine(*args):
        """ Combine 2 or more MiscType attributes """
        return ','.join(args)
    
    @staticmethod
    def is_viewable(misctype):
        # Snippets should not need a whole new viewable file,
        # they should be in the .content or .contentfile.
        # Archives, and Executables are not viewable for obvious reasons.
        # None-types just mean no type was set, they are probably viewable.
        viewabletypes = (MiscType.script, MiscType.snippet, 
                         MiscType.code, MiscType.none)
        return (misctype in viewabletypes)
            
    # Choices for Django admin
    fieldchoices = (('Code', 'Code File'),
                    ('Snippet', 'Code Snippet'),
                    ('Script', 'Script File'),
                    ('Text', 'Text File'),
                    ('None', 'None'),
                    ('Executable', 'Executable File'),
                    ('Archive', 'Archive File'),
                    )
class Lang:
    """ Kindof an ENUM with helper functions. Instances should not be created.
        Example:
            m = wp_misc.objects.create(filetype=MiscType.script, language=Lang.python)
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
