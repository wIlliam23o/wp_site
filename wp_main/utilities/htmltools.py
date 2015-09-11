# -*- coding: utf-8 -*-

'''Welborn productions - Utilities - HtmlTools
    Provides html string manipulation, code injection/generation

   -Christopher Welborn <cj@welbornprod.com> - Mar 27, 2013
'''

import logging
import os.path
import base64
import re
from sys import version as sysversion

# Fixing html fragments (from shortening blog posts and other stuff)
from tidylib import tidy_fragment
TIDYLIB_IGNORE = (
    # These errors from tidylib will not be logged ever.
    # They apply mostly to whole html docs, not fragments.
    # Others are expected after splitting html content up into small chunks.

    # Caused by splitting. '<div class="test">' -> '"test">'
    '<div> unexpected or duplicate quote mark',
    # Caused by splitting. '<div> attribute lacks value'
    'lacks value',
    # These don't apply to html fragments.
    '<head> previously mentioned',
    'inserting implicit <body>',
    'inserting missing \'title\' element',
    'missing <!DOCTYPE> declaration',
    'plain text isn\'t allowed in <head> elements'
)
# Django template loaders
from django.template import RequestContext, Context, loader
from django.template.base import TemplateDoesNotExist
from django.conf import settings

# Basic utilities and highlighting
from wp_main.utilities import (highlighter, utilities)

log = logging.getLogger('wp.utilities.htmltools')

# Fix for python 3 in strip_()
if sysversion[0] == '3':
    unicode = str

# RegEx for finding an email address
# (not compiled, because it gets compiled with additional
#  regex in some functions)
re_email_address = r'[\d\w\-\.]+@[\d\w\-\.]+\.[\w\d\-\.]+'
# RegEx for fixing open tags (fix_open_tags())
re_closing_complete = re.compile('[\074]/\w+[\076]{1}')
re_closing_incomplete = re.compile(r'[\074]/\w+')
re_opening_complete = re.compile(r'[\074][\w "\'=\-\/]+[\076]{1}')
re_opening_incomplete = re.compile(r'[\074][\w "\'=\-]+')
re_start_tag = re.compile(r'[\074]\w+')


# These are used on the About page,
# they are used to create links out of certain words.
auto_link_list = (
    ('Arduino', 'http://arduino.cc'),
    ('BASIC', 'http://en.wikipedia.org/wiki/BASIC'),
    ('Django', 'http://djangoproject.com'),
    ('Haskell', 'https://www.haskell.org/'),
    ('HTML', 'http://en.wikipedia.org/wiki/HTML'),
    ('JavaScript', 'http://en.wikipedia.org/wiki/JavaScript'),
    ('Linux', 'http://linux.org'),
    ('Mint', 'http://linuxmint.com'),
    ('PostgreSQL', 'http://www.postgresql.org'),
    ('Puppy', 'http://puppylinux.org'),
    ('Python', 'http://www.python.org'),
    ('RaspberryPi', 'http://raspberrypi.org'),
    ('Raspberry Pi', 'http://raspberrypi.org'),
    ('Rust', 'http://www.rust-lang.org/'),
    ('Ubuntu', 'http://ubuntu.com'),
    ('VB', 'http://msdn.microsoft.com/en-us/vstudio/'),
    ('Visual Basic', 'http://msdn.microsoft.com/en-us/vstudio/'),
    ('Windows', 'http://www.windows.com'),
    ('ATTiny',
        'http://www.atmel.com/products/microcontrollers/avr/tinyavr.aspx'),
    ('(?P<CGROUP> C )',
        'http://en.wikipedia.org/wiki/C_(programming_language)'),
)

# Module Functions (not everything can be an html_content(), or should be.)


def auto_link(content, link_list, **kwargs):
    """ Grabs words from HTML content and makes them links.
        see: auto_link_line()
        Only replaces lines inside certain tags.

        Keyword Arguments:
            All keyword arguments are added as attributes to the link.
            For python keywords like 'class',
            just put a _ in front or behind it.
            So _class="my-link-class" becomes <a href="" class="my-link-class">
            You can also just pass a dict as keyword args like this:
                my_attrs = {"target": "_blank", "class": "my-class"}
                auto_link(mycontent, my_link_list, **my_attrs)s
    """

    if isinstance(content, str):
        lines = content.split('\n')
        joiner = '\n'
    elif isinstance(content, (list, tuple)):
        joiner = None
        lines = content
    inside_p = False
    inside_span = False
    new_lines = []
    for line in iter(lines):
        linetrim = line.replace(' ', '').replace('\t', '')
        # start of tags
        if '<p' in linetrim:
            inside_p = True
        if '<span' in linetrim:
            inside_span = True

        # deal with good tags
        if inside_p or inside_span:
            line = auto_link_line(line, link_list, **kwargs)
        new_lines.append(line)

        # end of tags
        if '</p>' in linetrim:
            inside_p = False
        if '</span>' in linetrim:
            inside_span = False
    # end of content
    if joiner is None:
        return new_lines
    else:
        return joiner.join(new_lines)


def auto_link_line(line, link_list, **kwargs):
    """ Grabs words from HTML content and makes them links.
        Pass in a list of 2-tuples with [("Word", "Link Target"),]
        ex: (with auto_link())
            link_list = (("WelbornProd", "http://welbornprod.com"),
                         ("Django", "http://djangoproject.com"))
            new_html = auto_link(old_html, link_list)
        ex: (with auto_link_line())
            myline = "Testing auto_link_line() for WelbornProd."
            newline = auto_link_line(myline, link_list)

        Attributes can be added with keyword arguments
            new_html = auto_link(old_html, link_list,
                                 target="_blank", _class="link-class")
        * Notice the _ in front of 'class', because class is a python keyword.
        * All _'s are stripped from the keys before using them, so '_class'
        * becomes a 'class' attribute.
    """

    if not link_list:
        return line
    try:
        if len(link_list[0]) < 2:
            return line
    except (IndexError, TypeError):
        log.error('Invalid input to auto_link()!, '
                  'expecting a list/tuple of 2-tuple/lists')
        return line

    # build attributes, accepts '_class' as a 'class' attribute.
    make_attrstr = lambda k, v: ' {}="{}"'.format(k.strip('_'), v)

    attr_strings = [make_attrstr(k, v) for k, v in kwargs.items()]
    attr_string = ''.join(attr_strings) if len(attr_strings) > 0 else ''
    # replace text with links
    for link_pat, link_href in link_list:
        try:
            link_pat = r'[^\>]' + link_pat + r'[^\<]'
            re_pat = re.compile(link_pat)
            re_match = re_pat.search(line)
            if re_match is None:
                continue

            if not re_match.groups():
                # use only 1 group
                link_text = strip_all(
                    re_match.group(),
                    ' .,\'";:?/\\`~!@#$%^&*()_+-={}[]|')
            else:
                matchgroupdict = re_match.groupdict()
                # use first group dict key if found
                if matchgroupdict:
                    first_key = list(matchgroupdict)[0]
                    link_text = matchgroupdict[first_key]
                else:
                    # use first non-named group
                    link_text = re_match.groups()[0]

            # Replace the text with a link
            new_link = ''.join([
                '<a href="{}" '.format(link_href),
                'title="{}" '.format(link_text),
                '{}>'.format(attr_string),
                '{}</a>'.format(link_text),
            ])
            line = line.replace(link_text, new_link)
        except Exception as ex:
            log.error('Error in auto_link_line(): {}\n{}'.format(link_pat,
                                                                 ex))
            return line
    return line


def check_replacement(source_string, target_replacement):
    """ fixes target replacement string in inject functions.
        if {{ }} was ommitted, it adds it.
        if "{{target}}" is in source_string instead of "{{ target }}",
        it fixes the target to match.
        if nothing is needed,
        it returns the original target_replacement string.
        if the target_replacement isn't in the source_string, it returns false,
        so use [if check_replacement()],
        not [if check_replacement() in source_string].
    """

    # fix replacement if {{}} was omitted.
    if not target_replacement.startswith("{{"):
        target_replacement = "{{ " + target_replacement
    if not target_replacement.endswith("}}"):
        target_replacement = target_replacement + " }}"

    # this will look for '{{ target }}' and '{{target}}'...
    if target_replacement.replace(' ', '') in source_string:
        target_replacement = target_replacement.replace(' ', '')
    if target_replacement in source_string:
        return target_replacement
    else:
        return ''


def clean_html(source_string):
    """ runs the proper remove_ functions. on the source string
    """

    # these things have to be done in a certain order to work correctly.
    # hide_email, highlight, remove_comments, remove_whitespace
    if source_string is None:
        log.debug('Final HTML for page was None!')
        return ''

    return remove_whitespace(
        remove_comments(
            highlight(
                hide_email(
                    source_string))))


def fatal_error_page(message=None):
    """ If something really bad has happened and we can't rely on templates,
        this string can be passed in a Response.
        Arguments:
            message  : Optional extra message for response.
    """
    s = ('<html><head><title>Welborn Prod. - Fatal Error</title>',
         '<style>body {{font-family: Arial, sans-serif}}'
         '.header {{font-size:3em; color: blue;}}'
         '.msg {{font-size:1em; color: darkgrey;}}</style>'
         '<body><div class="header">',
         'Welborn Productions',
         '</div>',
         '<div class="msg">',
         '{}',
         '</div>')
    if message is None:
        message = 'Something has gone horribly wrong with the site.'
    return '\n'.join(s).format(message)


def filter_tidylib_errors(errortext):
    """ Filters lines in tidylib output based on TIDYLIB_IGNORE.
        Errors are only logged when DEBUG=True, but this will Help
        filter errors we don't care about. Like 'implicit <body>' in
        a small html fragment.
    """
    filtered = []
    for line in errortext.split('\n'):
        for ignored in TIDYLIB_IGNORE:
            if ignored in line:
                break
        else:
            # This line made it through.
            filtered.append(line)
    return '\n'.join(filtered).strip()


def find_email_addresses(source_string):
    """ finds all instances of email@addresses.com inside a wp-address
        classed tag.
        for hide_email().
    """

    # regex pattern for locating an email address.
    s_addr = ''.join([r'(<\w+(?!>)[ ]class[ ]?\=[ ]?[\'"]wp-address',
                      r'[\'"])(.+)?[ >](',
                      re_email_address,
                      ')',
                      ])
    re_pattern = re.compile(s_addr)
    raw_matches = re.findall(re_pattern, source_string)
    addresses_ = []
    for groups_ in raw_matches:
        # the last item is the address we want
        addresses_.append(groups_[-1])
    return addresses_


def find_mailtos(source_string):
    """ finds all instances of:
            <a class='wp-address' href='mailto:email@adress.com'></a>
        for hide_email().
        returns a list of href targets:
            ['mailto:name@test.com', 'mailto:name2@test2.com'],
        returns empty list on failure.

    """

    # regex pattern for finding href tag with 'mailto:??????'
    # and a wp-address class
    s_mailto = ''.join([r'<\w+(?!>)[ ]class[ ]?\=[ ]?[\'"]wp-address',
                        r'[\'"][ ]href[ ]?\=[ ]?["\']((mailto:)?',
                        re_email_address,
                        ')',
                        ])
    re_pattern = re.compile(s_mailto)
    raw_matches = re.findall(re_pattern, source_string)
    mailtos_ = []
    for groups_ in raw_matches:
        # first item is the mailto: line we want.
        mailtos_.append(groups_[0])
    return mailtos_


def fix_open_tags(source):
    """ Fixes missing tags in html fragments. """
    if not source:
        return source

    fixedhtml, errors = tidy_fragment(source)
    if settings.DEBUG and errors:
        errors = filter_tidylib_errors(errors)
        if errors:
            log.debug('Tidylib errors:\n{}'.format(errors))
    return fixedhtml


def fix_p_spaces(source_string):
    """ adds a &nbsp; to the end of lines inside all <p> tags.
        removing newlines breaks the <p> functionality of adding
        spaces on linebreaks.
        this function will add a &nbsp; where needed but must be
        called before any remove_newlines() type function.
    """

    # no nones allowed
    if source_string is None:
        return source_string
    # fix for html_content()
    if isinstance(source_string, html_content):
        source_string = source_string.content
    # get lines
    if '\n' in source_string:
        slines = source_string.split('\n')
    else:
        slines = [source_string]

    # cycle thru lines
    inside_p = False
    modified_lines = []
    for i in range(0, len(slines)):
        sline = slines[i]
        strim = sline.replace('\t', '').replace(' ', '').lower()

        # process p tag.
        if inside_p:
            # Found end of tag.
            if "</p>" in strim or "</div>" in strim:
                # end of p tag? (the </p> line itself will not be processed.)
                # some times the </p> gets cut off due to blog-post previews.
                # in this case we will stop on the next </div>.
                inside_p = False
            else:
                # add space if not already spaced.
                if not strim.endswith('&nbsp;'):
                    sline += '&nbsp;'
        # start of p tag? (the <p> line itself will not be processed.)
        if (strim.startswith('<p>') or
                strim.startswith("<pid") or
                strim.startswith("<pclass")):
            inside_p = True

        # append line to list, modified or not.
        modified_lines.append(sline)

    # finished
    return '\n'.join(modified_lines)


def get_html_file(wpobj):
    """ finds html file to use for the content, if any.
        returns empty string on failure.
    """

    if hasattr(wpobj, 'html_url'):
        htmlattr = 'html_url'
    elif hasattr(wpobj, 'contentfile'):
        htmlattr = 'contentfile'
    else:
        log.error('Object doesn\'t have a html file attribute!: '
                  '{}'.format(wpobj.__name__))
        return ''
    if not hasattr(wpobj, 'alias'):
        log.error('Object doesn\'t have an \'alias\' attribute!: '
                  '{}'.format(wpobj.__name__))
        return ''
    # Get objects html_url/contentfile
    obj_file = getattr(wpobj, htmlattr)
    if not obj_file:
        # use default location if no manual override is set.
        possiblefile = 'static/html/{}.html'.format(wpobj.alias)
        html_file = utilities.get_absolute_path(possiblefile)
    elif obj_file.lower() == 'none':
        # html files can be disabled by putting None in the
        # html_url/contentfile field.
        return ''
    else:
        if os.path.isfile(obj_file):
            # already absolute
            html_file = obj_file
        else:
            # try absolute path
            html_file = utilities.get_absolute_path(obj_file)
    return html_file


def get_screenshots(images_dir, noscript_image=None):
    """ Retrieves html formatted screenshots box for all images in
        a directory.
        Returns None on failure.
        Arguments:
            images_dir          : Relative dir containing all the images.

        Keyword Arguments:
            noscript_image      : Path to image to show for <noscript> tag.

    """
    # accceptable image formats (last 4 chars)
    formats = ['.png', '.jpg', '.gif', '.bmp', 'jpeg']

    # Make sure we are using the right dir.
    # get absolute path for images dir,
    # if none exists then delete the target_replacement.
    images_dir = utilities.get_absolute_path(images_dir)
    if not images_dir:
        return None

    # Get useable relative dir (user-passed may be wrong format)
    relative_dir = utilities.get_relative_path(images_dir)

    # find acceptable pics
    try:
        all_files = os.listdir(images_dir)
    except Exception as ex:
        log.debug('Can\'t list dir: {}\n{}'.format(images_dir, ex))
        return None

    # Help functions for building screenshots.
    relative_img = lambda filename: os.path.join(relative_dir, filename)
    good_format = lambda filename: (filename[-4:] in formats)

    # Build acceptable pics list
    good_pics = [relative_img(f) for f in all_files if good_format(f)]

    # auto-pick noscript image if needed
    if (len(good_pics) > 0) and (noscript_image is None):
        noscript_image = good_pics[0]
    else:
        # no good pics.
        noscript_image = None

    # Render from template.
    screenshots = render_clean(
        'home/imageviewer.html',
        context={
            'images': good_pics,
            'noscript_image': noscript_image,
        })
    return screenshots


def hide_email(source_string):
    """ base64 encodes all email addresses for use with wptool.js
        reveal functions.
        for spam protection.
        (providing the email-harvest-bot doesn't decode Base64)
    """

    slines = source_string.split('\n')

    # Fix py3 with base64.encodebytes(), encode/decode also added.
    # (until I remove py2 completely)
    if hasattr(base64, 'encodebytes'):
        encode = getattr(base64, 'encodebytes')
    else:
        encode = getattr(base64, 'encodestring')

    final_output = []
    for sline in slines:
        mailtos_ = find_mailtos(sline)
        for mailto_ in mailtos_:
            b64_mailto = encode(mailto_.encode('utf-8'))
            sline = sline.replace(mailto_,
                                  b64_mailto.decode('utf-8').replace('\n', ''))

        emails_ = find_email_addresses(sline)
        for email_ in emails_:
            b64_addr = encode(email_.encode('utf-8'))
            sline = sline.replace(email_,
                                  b64_addr.decode('utf-8').replace('\n', ''))

        # add line (encoded or not)
        final_output.append(sline)
    return '\n'.join(final_output)


def highlight(content):
    """ Uses the highlighter tools to syntax highlight everything. """
    return highlighter.highlight_inline(
        highlighter.highlight_codes(
            content))


def load_html_file(sfile, request=None, context=None, template=None):
    """ Trys loading a template by name,
        If context is passed it is used to render the template.
        If a request was passed then RequestContext is used,
        otherwise Context is used.
        If no template is found, it trys loading html content from file.
        returns string with html content.

        This can all be short-circuited by passing in a pre-loaded template
        with: template=load.get_template(templatename)
    """

    if template is None:
        try:
            template = loader.get_template(sfile)
        except TemplateDoesNotExist:
            # It wasn't a template name.
            log.debug('Not a template: {}'.format(sfile))

    if template:
        # Found template for this file, use it.
        if context:
            if request:
                # Try creating a request context.
                try:
                    contextobj = RequestContext(request, context)
                except Exception as ex:
                    log.error((
                        'Error creating request context from: {}\n{}'
                    ).format(request, ex))
                    return ''
            else:
                # No request, use normal context.
                contextobj = Context(context)
        else:
            # No context dict given, use empty context.
            contextobj = Context({})

        # Have context, try rendering.
        try:
            content = template.render(contextobj)
            # Good content, return it.
            return content
        except Exception as ex:
            log.error(''.join([
                'Error rendering template: {} '.format(sfile),
                'Context: {}'.format(context),
                '\n{}'.format(ex),
            ]))
            return ''

    # no template, probably a filename. check it:
    log.debug('No template, falling back to HTML: {}'.format(sfile))
    if not os.path.isfile(sfile):
        # try getting absolute path
        spath = utilities.get_absolute_path(sfile)
        if os.path.isfile(spath):
            sfile = spath
        else:
            # no file found.
            log.debug('No file found at: {}'.format(sfile))
            return ''

    try:
        with open(sfile) as fhtml:
            # Successful file open, return the contents.
            return fhtml.read()
    except IOError as exIO:
        log.error('Cannot open file: {}\n{}'.format(sfile, exIO))
    except OSError as exOS:
        log.error((
            'Possible bad permissions opening file: {}\n{}'
        ).format(sfile, exOS))
    except Exception as ex:
        log.error('General error opening file: {}\n{}'.format(sfile, ex))
    return ''


def remove_comments(source_string):
    """ splits source_string by newlines and
        removes any line starting with <!-- and ending with -->.
    """

    def is_comment(line):
        """ returns true if line is a single-line comment. (html or js) """
        return ((line.startswith('<!--') and line.endswith('-->')) or
                (line.startswith('/*') and line.endswith('*/')))

    if ('\n' in source_string):
        keeplines = []

        for sline in source_string.split('\n'):
            strim = sline.replace('\t', '').replace(' ', '')
            if not is_comment(strim):
                keeplines.append(sline)
        return '\n'.join(keeplines)
    else:
        return source_string


def remove_newlines(source):
    """ Remove all newlines from an html string.
        Skips <pre> and <script> blocks.
        DEPRECATED
    """
    is_skipstart = lambda s: ('<pre' in s) or ('<script' in s)
    is_skipend = lambda s: ('</pre>' in s) or ('</script>' in s)
    newline = '{}\n'.format
    noline = lambda s: s.replace('\n', '')
    in_skip = False
    output = []
    for sline in source.split('\n'):
        sline_lower = sline.lower()
        # start of skipped tag
        if is_skipstart(sline_lower):
            in_skip = True
        # Add with newline if its a skipped tag, otherwise no newlines.
        output.append(newline(sline) if in_skip else noline(sline))
        # end of skipped tag
        if is_skipend(sline_lower):
            in_skip = False

    return ''.join(output)


def remove_whitespace(source):
    """ Removes leading and trailing whitespace from lines,
        and removes blank lines.
        This ignores <pre> blocks, to keep <pre> formatting.
    """
    is_skipstart = lambda s: '<pre' in s
    is_skipend = lambda s: '</pre>' in s
    in_skip = False
    output = []
    for line in source.split('\n'):
        line_lower = line.lower()
        # start of skipped tag
        if is_skipstart(line_lower):
            in_skip = True
        trimmed = line if in_skip else line.strip()
        if trimmed:
            output.append(trimmed)
        # end of tag
        if is_skipend(line_lower):
            in_skip = False

    return '\n'.join(output)


def render_clean(template_name, **kwargs):
    """ runs render_html() through clean_html().
        renders template by name and context dict,
        RequestContext is used if 'request' kwarg is present.
        Keyword Arguments (same as render_html()):
              context      : dict to be used by Context() or RequestContext()
                   request : HttpRequest() object passed on to RequestContext()
                 link_list : link_list to be used with htmltools.auto_link()
                             Default: False
            auto_link_args : A dict containing kw arguments for auto_link()
                             Default: {}
            For these arguments, see: htmltools.render_html()
        passes resulting html through clean_html(),
        returns resulting html string.
    """

    return clean_html(render_html(template_name, **kwargs))


def render_html(template_name, **kwargs):
    """ renders template by name and context dict,
        returns the resulting html.
        Keyword arguments are:
            context      : Context or RequestContext dict to be used
                           RequestContext is used if a request is passed in
                           with 'request' kwarg.
                           Default: {}
                 request : HttpRequest object to pass on to RequestContext
                           Default: False (causes Context to be used)
               link_list : A link list in auto_link() format to be used
                           with auto_link() before returning content.
                           see: htmltools.auto_link()
                           Default: False (disables auto_link())
          auto_link_args : dict containing arguments for auto_link()
                           ex:
                           render_html("mytemplate",
                                       link_list=my_link_list,
                                       auto_link_args={"target":"_blank",
                                                       "class":"my-link-class",
                                                       })
                           Default: {}
    """
    context = kwargs.get('context', kwargs.get('context_dict', {}))
    request = kwargs.get('request', None)
    link_list = kwargs.get('link_list', None)
    auto_link_args = kwargs.get('auto_link_args', {})

    try:
        tmplate = loader.get_template(template_name)
        if isinstance(context, dict):
            if request:
                contextobj = RequestContext(request, context)
            else:
                contextobj = Context(context)
        else:
            # whole Context was passed
            contextobj = context

        rendered = tmplate.render(contextobj)
        if link_list:
            rendered = auto_link(rendered, link_list, **auto_link_args)
        return rendered
    except Exception:
        errstr = 'Unable to render html template'
        if request:
            errstr = '{} with request context'.format(errstr)
        message = '{}: {}'.format(errstr, template_name)
        utilities.logtraceback(log.error, message=message)

        return None


def strip_all(s, strip_chars):
    """ Strips all occurrences of strip_chars (str or list/tuple) from the
        beginning and end of a string.
        # Removes all x, y, and z characters from both ends.
        strip_all('xzythisyxz', 'zyx') == 'this'

        # The f and d are blocking the middle o's from being removed.
        strip_all('omnfoodnmo', 'mno') == 'food'
    """
    if not s:
        return s

    chars = tuple(strip_chars)
    while s.startswith(chars):
        s = s[1:]
    while s.endswith(chars):
        s = s[:-1]
    return s


def wrap_link(content_, link_url, alt_text=""):
    """ wrap content in <a href> """
    s = ""
    s_end = ""
    if link_url != "":
        s = "<a href='" + link_url + "'"
        if alt_text != "":
            s += " alt='" + alt_text + '"'
        s += ">"
        s_end = "</a>"

    return s + content_ + s_end
