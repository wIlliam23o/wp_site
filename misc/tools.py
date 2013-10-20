'''
    Welborn Productions - misc - MiscTypes
    Holds a class and helpers for Misc types (Script, text, etc.)
    
Created on Oct 20, 2013

@author: Christopher Welborn
'''

from misc.models import wp_misc
from wp_main.utilities import htmltools, utilities
from wp_main.utilities.wp_logging import logger

_log = logger('misc').log

class MiscType:
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
    python = 'Python'
    py = 'Python'
    python2 = 'Python 2'
    py2 = 'Python 2'
    python3 = 'Python 3'
    py3 = 'Python 3'
    bash = 'Bash'
    c = 'C'
    cpp = 'C++'
    cplusplus = 'C++'
    perl = 'Perl'
    pl = 'Perl'
    visualbasic = 'Visual Basic'
    vb = 'Visual Basic'
    none = 'None'

    # Choices for Django admin
    fieldchoices = (('Python', 'Python (any)'),
                    ('Python 2', 'Python 2+'),
                    ('Python 3', 'Python 3+'),
                    ('Bash', 'Bash'),
                    ('C', 'C'),
                    ('C++', 'C++'),
                    ('Perl', 'Perl'),
                    ('Visual Basic', 'Visual Basic'),
                    ('None', 'None'),
                    )

def get_long_desc(miscobj):
    """ Gets the long description to use for this wp_misc,
        if contentfile is set, it trys that.
        otherwise it uses .content.
    """
    
    # Try html file first.
    htmlfile = htmltools.get_html_file(miscobj)
    content = ''
    if htmlfile:
        content = htmltools.load_html_file(htmlfile)
    if content:
        return content

    # Try .content since html content failed.
    content = miscobj.content
    if not content:
        _log.error('Object has no content!: {}'.format(miscobj.name))
    return content


def get_visible_objects():
    """ Get all objects that aren't disabled. """
    
    objs = wp_misc.objects.get(disabled=False)
    return objs

def get_by_identifier(ident):
    """ Retrieve a misc object by Name, Alias, or ID. """
    
    #  Methods to try with utilities.get_object_safe
    tryargs = ({'id': ident},
               {'name': ident},
               {'alias': ident})
    
    for argset in tryargs:
        obj = utilities.get_object_safe(**argset)
        if obj:
            return obj
    
    # No object found.
    return None
