# -*- coding: utf-8 -*-

'''
      project: welborn productions - utilities - html
     @summary: provides html string manipulation, code injection/generation
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 27, 2013
'''


# Files/Paths
import os.path
from sys import version as sysversion
# Global settings
#from django.conf import settings

# Regex for email hiding
import re
import base64

# Django template loaders
from django.template import RequestContext, Context, loader

# Basic utilities
from wp_main.utilities import utilities
# Code highlighting
from wp_main.utilities import highlighter
# Log
from wp_main.utilities.wp_logging import logger
_log = logger("utilities.htmltools").log

# Fix for python 3 in strip_()
if sysversion[0] == '3':
    unicode = str

# RegEx for finding an email address
# (not compiled, because it gets compiled with additional regex in some functions)
re_email_address = r'[\d\w\-\.]+@[\d\w\-\.]+\.[\w\d\-\.]+'
# RegEx for fixing open tags (fix_open_tags())
re_closing_complete = re.compile('[\074]/\w+[\076]{1}')
re_closing_incomplete = re.compile(r'[\074]/\w+')
re_opening_complete = re.compile(r'[\074][\w "\'=\-\/]+[\076]{1}')
re_opening_incomplete = re.compile(r'[\074][\w "\'=\-]+')
re_start_tag = re.compile(r'[\074]\w+')


class html_content(object):

    """ class to hold html content, and perform various operations on it. 
        set self.content on initialization, set(), set_if(content, True), or through self.content = "stuff".
        functions modify the content and return the modified html_content object.
        
        ex:
            html_stuff = htmltools.html_content("<span>This will be a link soon.</span>")
            html_link = html_stuff.wrap_link("http://mylink.com")
            html_nolines = html_stuff.remove_newlines()
            # original html stuff is still at: html_stuff, or html_stuff.content
    """
    
    def __init__(self, content=''):
        self.content = content

    def __repr__(self):
        """ return content from this class """
        
        return str(self.content)
    
    def __str__(self):
        """ return content from this class """
        
        return str(self.content)

    def __unicode__(self):
        """ return content from this class """
        
        return self.__str__(self.content)

    def __add__(self, other):
        """ concatenate content to this one """
        
        return html_content(self.content + other)
    
    def __len__(self):
        """ returns the length of the content string """
        
        return len(self.content)
    
    def __iter__(self):
        """ provides iteration of the content by character """
        
        for character_ in self.content:
            yield character_
    
    def __contains__(self, other):
        """ provides the 'if in' method for content """
        
        return (other in self.content)  # (self.content.find(other) > -1)
    
    def __lt__(self, other):
        """ comparison on the content """
        
        return (self.content < other)
    
    def __gt__(self, other):
        """ comparison on the content """
        
        return (self.content > other)
    
    def __le__(self, other):
        """ comparison on the content """
        
        return (self.content <= other)
    
    def __ge__(self, other):
        """ comparison on the content """
        
        return (self.content >= other)
    
    def __eq__(self, other):
        """ comparison on the content """
        
        return (self.content == other)
    
    def __ne__(self, other):
        """ comparison on the content """
        
        return (self.content != other)
    
    def set(self, content):
        """ sets self.content,
            if another html_content object is passed it copies the .content from it.
        """
        
        if isinstance(content, (html_content)):
            # another html_content instance (causes recursion with __contains__)
            self.content = content.content
        else:
            # regular content
            self.content = content
        
    def set_if(self, condition_, content):
        """ sets self.content if condition_ is True """
        
        if condition_:
            self.set(content)
            
    def append(self, append_text):
        """ appends text to the end of content (just like __add__).. """
        
        self.content += append_text
        return self
    
    def append_line(self, append_line):
        """ appends a new line of text to content. """
        
        self.content += '\n' + append_line
        return self
    
    def append_lines(self, lines_):
        """ appends a list/tuple of lines to content """
        
        if isinstance(lines_, (list, tuple)):
            self.content += '\n' + ('\n'.join(lines_))
        return self
    
    def prepend(self, prepend_text):
        """ prepends text to the beginning of content """
        
        self.content = prepend_text + self.content
        return self
    
    def prepend_line(self, prepend_line):
        """ prepends a line of text to content. """
        
        self.content = prepend_line + '\n' + self.content
        return self

    def prepend_lines(self, lines_):
        """ prepends a list/tuple of lines to content """
        
        if isinstance(lines_, (list, tuple)):
            self.content = '\n'.join(lines_) + '\n' + self.content
        return self
    
    def split(self, split_by=' '):
        """ just like str.split() """
        
        return self.content.split(split_by)
    
    def replace(self, replace_what, replace_with):
        """ just like str.replace(), except it modifies the content """
        
        self.content = self.content.replace(replace_what, replace_with)
        return self
    
    def replace_if(self, replace_what, replace_with):
        """ runs replace() if replace_what equates to true. """
        
        if replace_what:
            self.replace(replace_what, replace_with)
        return self
    
    def tostring(self):
        """ returns string represenation of content. (like str(html_content())) """
        
        return str(self.content)
    
    def contains(self, contains_what):
        """ returns True if contains_what in content.
            if a List or Tuple of strings is passed, it will return True
            if ANY of the strings are found.
        """
        
        # list/tuple of strings to check
        if isinstance(contains_what, (list, tuple)):
            for str_itm in contains_what:
                if str_itm in self.content:
                    return True
            return False
        
        # regular string check
        return (contains_what in self.content)
    
    def wrap_link(self, link_url='', alt_text=''):
        """ wrap content in an <a href=link_url> """
        
        self.content = wrap_link(self.content, link_url, alt_text)
        return self
    
    def auto_link(self, link_list, **kwargs):
        """ auto link specific words in the content.
            see: htmltools.auto_link()
        """
        
        self.content = auto_link(self.content, link_list, **kwargs)
        return self
    
    def check_replacement(self, target_replacement):
        """ fixes target replacement string in inject functions.
            if {{ }} was ommitted, it adds it.
            if "{{target}}" is in source_string instead of "{{ target }}",
            it fixes the target to match.
            if nothing is needed, it returns the original target_replacement string.
            if the target_replacement isn't in the source_string, it returns false,
            so use [if check_replacement()], not [if check_replacement() in source_string].
        """
        
        return check_replacement(self.content, target_replacement)
        
    def inject_article_ad(self, target_replacement="{{ article_ad }}"):
        """ basically does a text replacement, 
            see: htmltools.inject_article_ad()
        """
        
        self.content = inject_article_ad(self.content, target_replacement)
        return self
    
    def inject_screenshots(self, images_dir, **kwargs):
        """ inject code for screenshots box.
            see: htmltools.inject_screenshots()
        """
        self.content = inject_screenshots(self.content, images_dir, **kwargs)
        return self
        
    def inject_sourceview(self, project, **kwargs):
        """ injects code for source viewing.
            see: htmltools.inject_sourceview()
        """
        request = kwargs.get('request', None)
        link_text = kwargs.get('link_text', None)
        desc_text = kwargs.get('desc_text', None)
        target_replacement = kwargs.get('target_replacement', '{{ source_view }}')
        self.content = inject_sourceview(project, self.content, request,
                                         link_text, desc_text, target_replacement)
        return self
        
    def remove_comments(self):
        """ splits source_string by newlines and 
            removes any line starting with <!-- and ending with -->. 
        """
                
        self.content = remove_comments(self.content)
        return self
    
    def remove_newlines(self):
        """ remove all newlines from a string 
            skips some tags, leaving them alone. like 'pre', so
            formatting doesn't get messed up.
        """
            
        self.content = remove_newlines(self.content)
        return self
    
    def remove_whitespace(self):
        """ removes leading and trailing whitespace from lines,
            and removes blank lines.
        """

        self.content = remove_whitespace(self.content)
        return self

    def highlight(self):
        """ runs all highlighting functions (inline/embedded) """
        
        # self.highlight_embedded()
        self.highlight_inline()
        self.highlight_codes()

        return self
    
    def highlight_codes(self):
        """ highlight all wp highlight codes. """

        self.content = highlighter.highlight_codes(self.content)
        return self

    def highlight_inline(self):
        """ highlight all inline 'pre class=[language]' content (if any) """
        
        if self.contains(("<pre class=", "<pre class =")):
            self.content = highlighter.highlight_inline(self.content)
        
        return self
    
    # TODO: Remove this when all objects use highlight_codes() style.
#    def highlight_embedded(self):
#        """ highlight all embedded lines in content (if any)
# Soon to be deprecated in favor of highlight_codes().#
#
#        """
#
#        if self.contains("highlight-embedded"):
#            self.content = highlighter.highlight_embedded(self.content)
#
#        return self
    
    def hide_email(self):
        """ base64 encodes all email addresses for use with wptool.js reveal functions.
            for spam protection.
        """
        
        if '\n' in self.content:
            slines = self.content.split('\n')
        else:
            # single line
            slines = [self.content]

        # Fixing python 3 until i remove py2 completely
        if hasattr(base64, 'encodebytes'):
            encode = base64.encodebytes
        else:
            encode = base64.encodestring
        
        final_output = []
        # encode/decode has been added for py3 (until i remove py2)
        for sline in slines:
            mailtos_ = find_mailtos(sline)
            for mailto_ in mailtos_:

                b64_mailto = encode(mailto_.encode('utf-8')).replace('\n', '')
                sline = sline.replace(mailto_, b64_mailto.decode('utf-8'))

            emails_ = find_email_addresses(sline)
            for email_ in emails_:
                b64_addr = encode(email_.encode('utf-8')).replace('\n', '')
                sline = sline.replace(email_, b64_addr.decode('utf-8'))

            # add line (encoded or not)
            final_output.append(sline)
        self.content = '\n'.join(final_output)
        return self
    
    def find_mailtos(self):
        """ finds all instances of <a class='wp-address' href='mailto:email@adress.com'></a> for hide_email().
            returns a list of href targets ['mailto:name@test.com', 'mailto:name2@test2.com'],
            returns empty list on failure.
        
        """
        
        # regex pattern for finding href tag with 'mailto:??????' and a wp-address class
        s_mailto = r'<\w+(?!>)[ ]class[ ]?\=[ ]?[\'"]wp-address[\'"][ ]href[ ]?\=[ ]?["\']((mailto:)?' + re_email_address + ')'
        re_pattern = re.compile(s_mailto)
        raw_matches = re.findall(re_pattern, self.content)
        mailtos_ = []
        for groups_ in raw_matches:
            # first item is the mailto: line we want.
            mailtos_.append(groups_[0])
        return mailtos_
    
    def find_email_addresses(self):
        """ finds all instances of email@addresses.com inside a wp-address classed tag. for hide_email() """
        
        # regex pattern for locating an email address.
        s_addr = r"(<\w+(?!>)[ ]class[ ]?\=[ ]?['\"]wp-address['\"])(.+)?[ >](" + re_email_address + ")"
        re_pattern = re.compile(s_addr)
        raw_matches = re.findall(re_pattern, self.content)
        addresses_ = []
        for groups_ in raw_matches:
            # the last item is the address we want
            addresses_.append(groups_[-1])
        return addresses_


# Module Variables (for accessing from anywhere)
auto_link_list = (("Windows", "http://www.windows.com"),
                  ("Mint", "http://linuxmint.com"),
                  ("Linux", "http://linux.org"),
                  ("Python", "http://www.python.org"),
                  ("Django", "http://djangoproject.com"),
                  ("Visual Basic .Net", "http://msdn.microsoft.com/en-us/vstudio/"),
                  ("VB", "http://msdn.microsoft.com/en-us/vstudio/"),
                  ("Ubuntu", "http://ubuntu.com"),
                  ("Arduino", "http://arduino.cc"),
                  ("RaspberryPi", "http://raspberrypi.org"),
                  ("Raspberry Pi", "http://raspberrypi.org"),
                  ("HTML", "http://en.wikipedia.org/wiki/HTML"),
                  ("JavaScript", "http://en.wikipedia.org/wiki/JavaScript"),
                  ("PostgreSQL", "http://www.postgresql.org"),
                  ("Puppy", "http://puppylinux.org"),
                  ("BASIC", "http://en.wikipedia.org/wiki/BASIC"),
                  ("ATTiny", "http://www.atmel.com/products/microcontrollers/avr/tinyavr.aspx"),
                  ("(?P<CGROUP>C language)", "http://en.wikipedia.org/wiki/C_(programming_language)"),
                  )
    
# Module Functions (not everything can be an html_content(), or should be.)


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


def auto_link(str_, link_list, **kwargs):
    """ Grabs words from HTML content and makes them links.
        see: auto_link_line()
        Only replaces lines inside certain tags.
        
        Keyword Arguments:
            All keyword arguments are added as attributes to the link.
            For python keywords like 'class', just put a _ in front or behind it.
            So _class="my-link-class" becomes <a href="" class="my-link-class">
            You can also just pass a dict as keyword args like this:
                my_attrs = {"target": "_blank", "class": "my-class"}
                auto_link(mycontent, my_link_list, **my_attrs)s
    """
    
    if hasattr(str_, 'encode'):
        lines = str_.split('\n')
        joiner = '\n'
    else:
        joiner = None
        lines = str_
    inside_p = False
    inside_span = False
    new_lines = []
    for line in iter(lines):
        linetrim = line.replace(' ', '').replace('\t', '')
        # start of tags
        if "<p" in linetrim:
            inside_p = True
        if "<span" in linetrim:
            inside_span = True
        
        # deal with good tags
        if inside_p or inside_span:
            line = auto_link_line(line, link_list, **kwargs)
        new_lines.append(line)
        
        # end of tags
        if "</p>" in linetrim:
            inside_p = False
        if "</span>" in linetrim:
            inside_span = False
    # end of content
    if joiner is None:
        return new_lines
    else:
        return joiner.join(new_lines)


def auto_link_line(str_, link_list, **kwargs):
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
            new_html = auto_link(old_html, link_list, target="_blank", _class="link-class")
        * Notice the _ in front of 'class', because class is a python keyword.
        * All _'s are stripped from the keys before using them, so '_class' becomes
        * a 'class' attribute.
    """
    
    try:
        if len(link_list) == 0:
            return str_
        if len(link_list[0]) < 2:
            return str_
    except:
        _log.error("Invalid input to auto_link()!, expecting a list/tuple of 2-tuple/lists")
        return str_
    # build attributes

    def parse_key(k):
        # for passing keys like "class", you can do "_class"
        return k.strip('_')
    attr_strings = [' ' + parse_key(k) + '="' + v + '"' for k, v in kwargs.items()]
    attr_string = ''.join(attr_strings) if len(attr_strings) > 0 else ''
    # replace text with links
    for link_pat, link_href in link_list:
        try:
            link_pat = r'[^\>]' + link_pat + r'[^\<]'
            re_pat = re.compile(link_pat)
            re_match = re_pat.search(str_)
            if re_match:
                if len(re_match.groups()) == 0:
                    # use only 1 group
                    link_text = strip_all(re_match.group(), ' .,\'";:?/\\`~!@#$%^&*()_+-={}[]|')
                else:
                    # use first group dict key if found
                    if len(re_match.groupdict().keys()) > 0:
                        first_key = list(re_match.groupdict().keys())[0]
                        link_text = re_match.groupdict()[first_key]
                    else:
                        # use first non-named group
                        link_text = re_match.groups()[0]
                # Replace the text with a link
                new_link = '<a href="' + link_href + '" title="' + link_text + '"' + attr_string + '>' + link_text + '</a>'
                str_ = str_.replace(link_text, new_link)
        except Exception as ex:
            _log.error("Error in auto_link_line(): (" + link_pat + ")" + repr(ex))
            return str_
    return str_


def readmore_box(link_href):
    """ returns Html string for the readmore box. """
    
    return "<br/><a href='" + link_href + "'><div class='readmore-box'><span class='readmore-text'>more...</span></div></a>"


def comments_button(link_href):
    """ returns Html string for the comments box (button) """

    return "<a href='" + link_href + "#comments-box'><div class='comments-button'><span class='comments-button-text'>comments...</span></div></a>"
 

def get_html_file(wpobj):
    """ finds html file to use for t content, if any.
        returns empty string on failure.
    """
    
    if hasattr(wpobj, 'html_url'):
        htmlattr = 'html_url'
    elif hasattr(wpobj, 'contentfile'):
        htmlattr = 'contentfile'
    else:
        _log.error('Object doesn\'t have a html file attribute!: {}'.format(wpobj.__name__))
        return ''
    if not hasattr(wpobj, 'alias'):
        _log.error('Object doesn\'t have an \'alias\' attribute!: {}'.format(wpobj.__name__))
        return ''
    # Get objects html_url/contentfile
    obj_file = getattr(wpobj, htmlattr)
    if not obj_file:
        # use default location if no manual override is set.
        html_file = utilities.get_absolute_path("static/html/" + wpobj.alias + ".html")
    elif obj_file.lower() == "none":
        # html files can be disabled by putting None in the html_url/contentfile field.
        return ''
    else:
        if os.path.isfile(obj_file):
            # already absolute
            html_file = obj_file
        else:
            # try absolute path
            html_file = utilities.get_absolute_path(obj_file)
    return html_file

    
def load_html_file(sfile):
    """ loads html content from file.
        returns string with html content.
    """
    
    if not os.path.isfile(sfile):
        # try getting absolute path
        spath = utilities.get_absolute_path(sfile)
        if os.path.isfile(spath):
            sfile = spath
        else:
            # no file found.
            _log.debug("no file found at: " + sfile)
            return ""
        
    try:
        with open(sfile) as fhtml:
            return fhtml.read()
    except IOError as exIO:
        _log.error("Cannot open file: " + sfile + '\n' + str(exIO))
        return ""
    except OSError as exOS:
        _log.error("Possible bad permissions opening file: " + sfile + '\n' + str(exOS))
        return ""
    except Exception as ex:
        _log.error("General error opening file: " + sfile + '\n' + str(ex))
        return ""
        

def check_replacement(source_string, target_replacement):
    """ fixes target replacement string in inject functions.
        if {{ }} was ommitted, it adds it.
        if "{{target}}" is in source_string instead of "{{ target }}",
        it fixes the target to match.
        if nothing is needed, it returns the original target_replacement string.
        if the target_replacement isn't in the source_string, it returns false,
        so use [if check_replacement()], not [if check_replacement() in source_string].
    """
    
    # fix replacement if {{}} was omitted.
    if not target_replacement.startswith("{{"):
        target_replacement = "{{ " + target_replacement
    if not target_replacement.endswith("}}"):
        target_replacement = target_replacement + " }}"
        
    # this will look for '{{ target }}' and '{{target}}'...
    if target_replacement.replace(' ', '') in source_string:
        target_replacement = target_replacement.replace(' ', '')
    
    return target_replacement if (target_replacement in source_string) else False
    

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
    formats = [".png", ".jpg", ".gif", ".bmp", "jpeg"]
    
    # Make sure we are using the right dir.
    # get absolute path for images dir, if none exists then delete the target_replacement.
    images_dir = utilities.get_absolute_path(images_dir)
    if not images_dir:
        return None
    
    # Get useable relative dir (user-passed may be wrong format)
    relative_dir = utilities.get_relative_path(images_dir)
        
    # find acceptable pics
    try:
        all_files = os.listdir(images_dir)
    except Exception as ex:
        _log.debug("Can't list dir: " + images_dir + '\n' + str(ex))
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
    screenshots = render_clean("home/screenshots.html",
                               context_dict={'images': good_pics,
                                             'noscript_image': noscript_image,
                                             })
    return screenshots


def inject_article_ad(source_string, target_replacement="{{ article_ad }}"):
    """ basically does a text replacement, 
        replaces 'target_replacement' with the code for article ads.
        returns finished html string.
    """
    
    # fail check.
    target = check_replacement(source_string, target_replacement)
    if target:
        # at this moment article ad needs no Context.
        article_ad = render_clean("home/articlead.html")
        return source_string.replace(target, article_ad)
    
    # target not found.
    return source_string


def inject_screenshots(source_string, images_dir, **kwargs):
    """ inject code for screenshots box.
        walks image directory, grabbing images for the image rotator box.
        uses screenshots.html template to display them.
        Arguments:
            source_string       : Original string containing the replacement
                                  target.
                                  like: '<body>{{ screenshots_code }}</body>'
            images_dir          : Relative dir containing all the images.
        Keyword Arguments:
            target_replacement  : string to replace screenshot html with.
                                  default: '{{ screenshots_code }}'
            noscript_image      : Path to image to show for <noscript> tag.
        examples:
            s = inject_screenshots(s, "static/images/myapp")
            s = inject_screenshots(s, 
                                   "images/myapp/", 
                                   noscript_image="sorry_no_javascript.png")
            s = inject_screenshots(s, 
                                   "images/myapp",
                                   "{{ screenshots }}",
                                   "noscript.png")
    """
    # Grab kw args, set defaults.
    target_replacement = kwargs.get('target_replacement',
                                    '{{ screenshots_code }}')
    noscript_image = kwargs.get('noscript_image', None)

    # fail checks, make sure target exists in source_string
    target = check_replacement(source_string, target_replacement)
    if not target:
        return source_string
    
    screenshots = get_screenshots(images_dir, noscript_image=noscript_image)
    if screenshots:
        # Return fixed source_string with screenshots.
        return source_string.replace(target, screenshots)
    else:
        # No screenshots found.
        return source_string


def inject_sourceview(project, source_string, request=None, link_text=None, desc_text=None, target_replacement="{{ source_view }}"):
    """ injects code for source viewing.
        needs wp_project (project) passed to gather info.
        if target_replacement is not found, returns source_string.
        
        uses sourceview.html template to display. the template handles
        missing information.
        returns rendered source_string.
    """

    # fail check.
    target = check_replacement(source_string, target_replacement)
    if not target:
        return source_string
    
    # has project info?
    if project is None:
        return source_string.replace(target, "")
    
    # use source_file if no source_dir was set.
    relativefile = utilities.get_relative_path(project.source_file)
    relativedir = utilities.get_relative_path(project.source_dir)
    relativepath = relativedir if relativedir else relativefile
    # has good link?
    if relativepath == "":
        _log.debug("missing source file/dir for: " + project.name)

    # get default filename to display in link.
    file_name = utilities.get_filename(project.source_file) if project.source_file else project.name
    
    # get link text
    if link_text is None:
        link_text = file_name + " (local)"

    sourceview = render_clean("home/sourceview.html",
                              context_dict={'project': project,
                                            'file_path': relativepath,
                                            'link_text': link_text,
                                            'desc_text': desc_text,
                                            },
                              with_request=request,
                              )
    return source_string.replace(target, sourceview)
    
        
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


def remove_newlines(source_string):
    """ remove all newlines from a string 
        skips some tags, leaving them alone. like 'pre', so
        formatting doesn't get messed up.
    """
        
    # removes newlines, except for in pre blocks.
    if '\n' in source_string:
        in_skipped = False
        final_output = []
        for sline in source_string.split('\n'):
            sline_lower = sline.lower()
            # start of pre tag
            if (("<pre" in sline_lower) or
                ("<script" in sline_lower)):
                in_skipped = True
            # process line.
            if in_skipped:
                # add original line.
                final_output.append(sline + '\n')
            else:
                # add trimmed line.
                final_output.append(sline.replace('\n', ''))
            # end of tag
            if (("</pre>" in sline_lower) or
                ("</script>" in sline_lower)):
                in_skipped = False
    else:
        final_output = [source_string]
    return "".join(final_output)


def remove_whitespace(source_string):
    """ removes leading and trailing whitespace from lines,
        and removes blank lines.

    """
    
    # removes newlines, except for in pre blocks.
    if '\n' in source_string:
        slines = source_string.split('\n')
    else:
        slines = [source_string]
    # start processing
    in_skipped = False
    final_output = []
    for sline in slines:
        sline_lower = sline.lower()
        # start of skipped tag
        if "<pre" in sline_lower:
            in_skipped = True
        # process line.
        if in_skipped:
            # add original line.
            final_output.append(sline)
        else:
            trimmed = trim_whitespace_line(sline)
            # no blanks.
            if trimmed != '\n' and trimmed != '':
                final_output.append(trimmed)
        # end of tag
        if "</pre>" in sline_lower:
            in_skipped = False

    return '\n'.join(final_output)


def fix_p_spaces(source_string):
    """ adds a &nbsp; to the end of lines inside all <p> tags.
        removing newlines breaks the <p> functionality of adding spaces on linebreaks.
        this function will add a &nbsp; where needed but must be called before any
        remove_newlines() type function.
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
        if strim.startswith('<p>') or strim.startswith("<pid") or strim.startswith("<pclass"):
            inside_p = True
        
        # append line to list, modified or not.
        modified_lines.append(sline)
    
    # finished
    return '\n'.join(modified_lines)


def trim_whitespace_line(sline):
    """ trims whitespace from a single line """
    
    scopy = sline
    while scopy.startswith(' ') or scopy.startswith('\t'):
        scopy = scopy[1:]
    while scopy.endswith(' ') or scopy.endswith('\t'):
        scopy = scopy[:-1]
    return scopy


def hide_email(source_string):
    """ base64 encodes all email addresses for use with wptool.js reveal functions.
        for spam protection.
    """
    
    if '\n' in source_string:
        slines = source_string.split('\n')
    else:
        # single line
        slines = [source_string]
    
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
            sline = sline.replace(mailto_, b64_mailto.decode('utf-8').replace('\n', ''))
            #_log.debug("mailto: replaced " + mailto_ +'\n    with: ' + b64_mailto)
        emails_ = find_email_addresses(sline)
        for email_ in emails_:
            b64_addr = encode(email_.encode('utf-8'))
            sline = sline.replace(email_, b64_addr.decode('utf-8').replace('\n', ''))
            #_log.debug("email: replaced " + email_ +'\n    with: ' + b64_addr)
        # add line (encoded or not)
        final_output.append(sline)
    return '\n'.join(final_output)


def find_mailtos(source_string):
    """ finds all instances of <a class='wp-address' href='mailto:email@adress.com'></a> for hide_email().
        returns a list of href targets ['mailto:name@test.com', 'mailto:name2@test2.com'],
        returns empty list on failure.
    
    """
    
    # regex pattern for finding href tag with 'mailto:??????' and a wp-address class
    s_mailto = r'<\w+(?!>)[ ]class[ ]?\=[ ]?[\'"]wp-address[\'"][ ]href[ ]?\=[ ]?["\']((mailto:)?' + re_email_address + ')'
    re_pattern = re.compile(s_mailto)
    raw_matches = re.findall(re_pattern, source_string)
    mailtos_ = []
    for groups_ in raw_matches:
        # first item is the mailto: line we want.
        mailtos_.append(groups_[0])
    return mailtos_


def find_email_addresses(source_string):
    """ finds all instances of email@addresses.com inside a wp-address classed tag. for hide_email() """
    
    # regex pattern for locating an email address.
    s_addr = r"(<\w+(?!>)[ ]class[ ]?\=[ ]?['\"]wp-address['\"])(.+)?[ >](" + re_email_address + ")"
    re_pattern = re.compile(s_addr)
    raw_matches = re.findall(re_pattern, source_string)
    addresses_ = []
    for groups_ in raw_matches:
        # the last item is the address we want
        addresses_.append(groups_[-1])
    return addresses_


def strip_all(s, strip_chars):
    """ runs s.strip() for every char in strip_chars.
        if strip_chars is a list/tuple, then it strips
        every character of every item in the list.
    """
    
    if s is None:
        return s
    if isinstance(strip_chars, (list, tuple)):
        strip_chars = ''.join(strip_chars)
    
    if isinstance(s, str):
        strip_ = str.strip
    elif isinstance(s, unicode):
        strip_ = unicode.strip
    
    for c in strip_chars:
        s = strip_(s, c)
    return s


def fix_open_tags(source):
    """ scans string, or list of strings for 
        open <tags> without their </closing> tag.
        adds the closing tags to the end (in order)
        (ignores certain tags like <br> and <img>) 
        
        if you put a list in, you get a list back.
        if you put a string in, you get a string back.
    
    """
    # TODO: Fix new wp highlight codes open tags. [python] some stuff... oops.
    try:
        if hasattr(source, 'encode'):
            if '\n' in source:
                source = source.split('\n')
                joiner = '\n'
            elif '<br>' in source:
                source = source.split('<br>')
                joiner = '<br>'
            else:
                # single line of text to scan.
                source = [source]
                joiner = ''
                
        elif isinstance(source, (list, tuple)):
            joiner = None
        else:
            _log.debug("Unknown type passed: " + str(type(source)))
            joiner = None
    except Exception as ex:
        # error splitting text?
        _log.error("Error splitting text:\n" + str(ex))
        return source
      
    # keeps track of tags opened so far,
    opening_tags = []
    #incomplete_tags = []
    # list to hold good and 'fixed' lines.
    fixed_lines = []

    def find_opening(closing):
        if '/' in closing:
            closing = closing.replace('/', '')
        if closing.endswith('>'):
            closing = closing[:-1]

        for starts in opening_tags:
            if closing in starts:
                return starts
        return False
        
    for line in source:
        opening = re_opening_complete.search(line)
        incomplete = re_opening_incomplete.search(line)
        closing = re_closing_complete.search(line)
        closing_inc = re_closing_incomplete.search(line)

        # Incomplete start tag (no '>')
        if incomplete and not opening:
            # try fixing the opening tag.
            line = line.replace(incomplete.group(), incomplete.group() + '>')
            opening_tags.append(incomplete.group())
        # Good tag
        elif incomplete and opening:
            # add to the list of known good tags.
            opening_tagmatch = re_start_tag.search(opening.group())
            if opening_tagmatch:
                opening_tag = opening_tagmatch.group()
                opening_tags.append(opening_tag)

        # Incomplete closing tag (no '>')
        if closing_inc and not closing:
            # find it's start tag, and use it to build a 'fixed' end tag.
            expecting = opening_tags[len(opening_tags) - 1].replace('<', '</') + '>'
            line = line.replace(closing_inc.group(), expecting)
            tag_opening = find_opening(expecting)
            if tag_opening:
                opening_tags.remove(tag_opening)
        # Good closing tag...
        elif closing_inc and closing:
            # remove it's start tag from the list.
            has_start = find_opening(closing.group())
            if has_start:
                opening_tags.remove(has_start)

        fixed_lines.append(line)

    # Add left over tags (last open tag gets first closing tag.)...
    ignore_tags = ('<img', '<br')

    if len(opening_tags) > 0:
        for i in range(len(opening_tags), 0, -1):
            left_over = opening_tags[i - 1]
            if not left_over in ignore_tags:
                fixed_lines.append(left_over.replace('<', '</') + '>')

    if joiner is None:
        return fixed_lines
    else:
        return joiner.join(fixed_lines)
    

def clean_html(source_string):
    """ runs the proper remove_ functions. on the source string """

    # these things have to be done in a certain order to work correctly.
    # hide_email, fix p spaces, remove_comments, remove_whitespace, remove_newlines
    if source_string is None:
        _log.debug("None object passed as source_string!")
        return ""
    
    return remove_whitespace(
        remove_comments(
            hide_email(source_string)))
    
    
def render_html(template_name, **kwargs):
    """ renders template by name and context dict,
        returns the resulting html.
        Keyword arguments are:
            context_dict : Context or RequestContext dict to be used
                           RequestContext is used if a request is passed into 'with_request'
                           Default: {}
            with_request : HttpRequest object to pass on to RequestContext
                           Default: False (causes Context to be used)
               link_list : A link list in auto_link() format to be used
                           with auto_link() before returning content.
                           see: htmltools.auto_link()
                           Default: False (disables auto_link())
          auto_link_args : dict containing arguments for auto_link()
                           ex: render_html("mytemplate", 
                                           link_list = my_link_list, 
                                           auto_link_args = {"target":"_blank", "class":"my-link-class"})
                           Default: {}
    """
    context_dict = kwargs.get('context_dict', {})
    with_request = kwargs.get('with_request', False)
    link_list = kwargs.get('link_list', False)
    auto_link_args = kwargs.get('auto_link_args', {})
    
    try:
        tmplate = loader.get_template(template_name)
        if isinstance(context_dict, dict):
            context_ = RequestContext(with_request, context_dict) if with_request else Context(context_dict)
        else:
            # whole Context was passed
            context_ = context_dict
            
        rendered = tmplate.render(context_)
        if link_list:
            rendered = auto_link(rendered, link_list, **auto_link_args)
        return rendered
    except Exception as ex:
        errstr = "Unable to render html template"
        if with_request:
            errstr += " with request context"

        _log.error(errstr + ': ' + template_name + '\n' + str(ex))
        return None


def render_clean(template_name, **kwargs):
    """ runs render_html() through clean_html().
        renders template by name and context dict,
        RequestContext is used if with_request is True.
        Keyword Arguments:
              context_dict : dict to be used by Context() or RequestContext()
              with_request : HttpRequest() object to pass on to RequestContext()
                 link_list : link_list to be used with htmltools.auto_link()
                             Default: False
            auto_link_args : A dict containing keyword arguments for auto_link()
                             Default: {}
            For these arguments, see: htmltools.render_html()
        passes resulting html through clean_html(),
        returns resulting html string.
        
    """

    return clean_html(render_html(template_name, **kwargs))
