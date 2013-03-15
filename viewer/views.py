from django.http import HttpResponse
from django.template import Context, loader
from django.utils.safestring import mark_safe # don't escape html with strings marked safe.

from django.conf import settings

from wp_main import utilities
from downloads.views import get_project
from viewer.highlighter import wp_highlighter

import os.path
import logging
hl_log = logging.getLogger("welbornprod.viewer.highlighter")

def index(request):
    """ default download page, when no file is specified """
    
    return viewer(request, "")


def viewer(request, file_path):
    """ provides download of files, 
        tracks download count of projects and possibly others
        by checking file's project owner, incrementing the count,
        and then redirecting to the actual file.
    """
    
    static_path = file_path if (file_path.startswith("/")) else ('/' + file_path)
    absolute_path = utilities.get_absolute_path(file_path)
    if absolute_path == "":
        # File doesn't exist. Return a 404
        alert_message = "Sorry, that file doesn't exist."
        main_content = "<div class='wp-block'><a href='/'><span>Click here to go home.</span></a></div>"
        tmp_notfound = loader.get_template('home/main.html')
        cont_notfound = Context({'main_content': mark_safe(main_content),
                                 'alert_message': mark_safe(alert_message),
                                 })
        rendered = utilities.clean_template(tmp_notfound, cont_notfound, (not settings.DEBUG))
        response = HttpResponse(rendered)
    else:
        # load actual file.
        # see if its a project file.
        proj = get_project(absolute_path)
        if proj is None:
            project_title = ""
        else:
            project_title = proj.name
            # increment downloads for this project.
            proj.view_count += 1
            proj.save()
        # get lexer
        lexer_ = get_lexer_fromfile(static_path)
        # get file content
        try:
            with open(absolute_path) as fread:
                scontent = fread.read()
            alert_message = ""
        except:
            hl_log.error("unable to open file: " + absolute_path)
            alert_message = "There was an error opening the file."
            lexer_ = ""
            scontent = "<a href='/'><span>Sorry, click here to go home.</span></a>"
 
        if lexer_ == "":
            hl_log.debug("no suitable lexer found for: " + absolute_path)
            # no suitable lexer found.
            shtml = scontent
        else:
            # Build top of page
            if project_title == "":
                shtml = ""
            else:
                shtml = "<div class='title-box'><h3 class='title'>Source View</h3></div>"
                shtml += "<a href='/projects/" + proj.alias + "'>" + \
                            "<div class='project_title'><h1 class='project-header'>" + project_title + "</h1>" +\
                            "</div></a>"
            # Add short filename...
            sshortname = os.path.split(static_path)[1]
            shtml += "<a href='" + static_path + "'><div><span class='viewer-filename'>" + sshortname + "</span></div></a>"
            # highlight file content
            highlighter = wp_highlighter(lexer_, "default", False)
            highlighter.code = scontent
            try:
                shtml += highlighter.highlight()
                hl_log.debug("Highlighted file: " + absolute_path)
            except:
                alert_message = "There was an error highlighting this file."
                shtml = "<a href='/'><span>Sorry, click here to go home.</span></a>"
        
        # build template
        tmp_view = loader.get_template("home/main.html")
        cont_view = Context({'extra_style_link': "/static/css/highlighter.css",
                             'extra_style_link2': "/static/css/projects.css",
                             'main_content': mark_safe(shtml),
                             'alert_message': mark_safe(alert_message),
                             })
        rendered = utilities.clean_template(tmp_view, cont_view, (not settings.DEBUG))
        response = HttpResponse(rendered)
    return response


def get_lexer_fromfile(sfilename):
    """ determine which lexer to use by file extension """
    
    lexers = [["python", ".py"],
              ["c", ".c", ".h", ".cpp"]
              ]
    slexer = ""
    for lex_ in lexers:
        sname = lex_[0]
        exts = lex_[1:]
        for ext_ in exts:
            if sfilename.lower().endswith(ext_):
                slexer = sname
                
    return slexer
    