# File/Path
import os.path
# Mark generated html as safe to view.
from django.utils.safestring import mark_safe # don't escape html with strings marked safe.

# Filetracker info
from downloads import dltools

# Local tools
from wp_main.utilities import utilities
from wp_main.utilities import responses
# For source highlighting
from wp_main.utilities.highlighter import wp_highlighter, get_lexer_name_fromfile
# Logging
from wp_main.utilities.wp_logging import logger
_log = logger('viewer').log

# For retrieving project information (source viewing)
from projects import tools



def index(request):
    """ default download page, when no file is specified """
    
    return viewer(request, "")


def viewer(request, file_path):
    """ provides view of files, 
        tracks view count of projects and possibly others
        by checking file's project owner, incrementing the count,
        and then highlights the file where applicable..
    """
    
    static_path = file_path if (file_path.startswith("/")) else ('/' + file_path)
    absolute_path = utilities.get_absolute_path(file_path)
    #_log.debug("using absolute_path: " + absolute_path)
    if absolute_path == "":
        # File doesn't exist. Return an alert.
        return responses.alert_message("Sorry, that file doesn't exist.")

    # see if its a project file.
    proj = tools.get_project_from_path(absolute_path)
   
    # directory was passed?
    if os.path.isdir(absolute_path):
        paths = get_using_paths(file_path, absolute_path, proj)
        if (paths is None):
            # can't determine a good file to view from this dir, return an alert.
            return responses.alert_message("Sorry, there was an error viewing that directory.")
        else:
            static_path, absolute_path = paths
    # if a dir was passed, the absolute_path has changed, we need to update the file_tracker.
    if os.path.isfile(absolute_path):
        # update file_tracker info...
        filetracker = dltools.get_file_tracker(absolute_path)
        if filetracker is not None:
            if proj is not None: dltools.update_tracker_projects(filetracker, proj)
            filetracker.view_count += 1
            filetracker.save()            
    # load actual file.
    if proj is None:
        project_title = ""
        # we're not letting you browse the /js dir that easily.
        # not that I care, it's just code that is not needed.
        # this site is about my projects, not my external libs.
        vertical_menu = ""
    else:
        project_title = proj.name
        # increment views for this project.
        proj.view_count += 1
        proj.save()
        # check for source files.
        source_files = get_source_files(proj)
        vertical_menu = get_source_files_menu(source_files)
       
    # get lexer name
    lexer_ = get_lexer_name_fromfile(static_path)
   
    # get file content
    alert_msg = ""
    try:
        with open(absolute_path) as fread:
            scontent = fread.read()
    except:
        _log.error("unable to open file: " + absolute_path)
        alert_msg = "There was an error opening the file."
        lexer_ = ""
        scontent = "<a href='/'><span>Sorry, click here to go home.</span></a>"

    if lexer_ == "":
        _log.debug("no suitable lexer found for: " + absolute_path)
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
        file_name = utilities.get_filename(static_path)
        shtml += "<a href='" + utilities.append_path("/dl", static_path) + "'>" + \
                 "<div class='viewer-filename-box'><span class='viewer-filename'>" + file_name + "</span></div>" + \
                 "<div class='viewer-download-box'><span class='viewer-download-text'>download</span></div></a>"
                
        # highlight file content
        highlighter = wp_highlighter(lexer_, "default", False)
        highlighter.code = scontent
        try:
            shtml += highlighter.highlight()
            #_log.debug("Highlighted file: " + absolute_path)
        except:
            alert_msg = "There was an error highlighting this file."
            shtml = "<a href='/'><span>Sorry, click here to go home.</span></a>"
    
    # build template (if an alert response wasn't returned already.)
    response = responses.clean_response("home/main.html",
                                        {'request': request,
                                         'extra_style_link_list': ["/static/css/highlighter.css",
                                                                   "/static/css/projects.css"],
                                         'vertical_menu': mark_safe(vertical_menu),
                                         'main_content': mark_safe(shtml),
                                         'alert_message': mark_safe(alert_msg),
                                         })
    return response


def get_source_files(project):
    """ returns list of all source files for a project, if any.
        uses relative static path. (/static/files/project/source/file.py)
        returns None on  failure.
    """
    
    if project.source_dir == "":
        source_files = None
    else:
        sabsolute = utilities.get_absolute_path(project.source_dir)
        if sabsolute == "":
            source_files = None
        else:
            # retrieve all source filenames
            file_names = os.listdir(sabsolute)
            print str(file_names)
            if len(file_names) == 0:
                source_files = None
            else:
                source_files = []
                for sfilename in file_names:
                    srelativepath = utilities.get_relative_path(os.path.join(project.source_dir, sfilename))
                    source_files.append(srelativepath)
    return source_files
    
    
def get_source_files_menu(source_files, max_length = 25, max_text_length = 18):
    """ build a vertical menu from all source files.
        source_files should be a list of relative paths to files.
        returns Html string.
    """
    
    if source_files is None:
        return ""
    if len(source_files) == 0:
        return ""
    
    shead = "<div class='vertical-menu'>\n" + \
            "<ul class='vertical-menu-main'>\n"
    stail = "</ul>\n</div>\n"
    stemplate = """
                    <li class='vertical-menu-item'>
                        <a class='vertical-menu-link' href='{{ view_path }}'>
                            <span class='vertical-menu-text' style='font-size: .8em;'>{{ file_name }}</span>
                        </a>
                    </li>
    """
    smenu = ""
    icount = 0
    for srelativepath in source_files:
        sviewpath = utilities.append_path("/view", srelativepath)
        sfilename = utilities.get_filename(srelativepath)
        # trim filename if needed
        if len(sfilename) > max_text_length:
            sfilename = ".." + sfilename[len(sfilename) - max_text_length:]

        
        smenu += stemplate.replace("{{ view_path }}", sviewpath).replace("{{ file_name }}", sfilename)
        icount += 1
        if icount > max_length:
            break
        
    return shead + smenu + stail

def get_using_paths(file_path, absolute_path=None, proj=None):
    """ When given a dir as a path, find out which file is preferred to use first. """
    
    if absolute_path is None:
        absolute_path = utilities.get_absolute_path(file_path)
    if absolute_path == "":
        return None
    
    try:
        files = os.listdir(absolute_path)
    except:
        files = []
        _log.debug("unable to listdir: " + absolute_path)
        
    # no files in this directory, or bad dir.
    if len(files) == 0:
        return None

    # dir has files, get most important to show.
    if proj is None:
        # no project, try first file.
        static_path = utilities.append_path(file_path, files[0])
        absolute_path = utilities.get_absolute_path(static_path)
        #_log.debug("dir passed: no project for file, using first file: " + absolute_path)
    else:
        # has project, see if source_file is good. if so, use it.
        if proj.source_file == "":
            # just use first file found.
            static_path = utilities.append_path(file_path, files[0])
            absolute_path = utilities.get_absolute_path(static_path)
            #_log.debug("dir passed: no source_file for project, using first file: " + absolute_path)
        else:
            static_path = proj.source_file
            absolute_path = utilities.get_absolute_path(static_path)
            #_log.debug("dir passed: using source_file: " + absolute_path)
    
    return (static_path, absolute_path)
