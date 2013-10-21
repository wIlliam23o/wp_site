# File/Path
import os.path
# Mark generated html as safe to view.
from django.utils.safestring import mark_safe # don't escape html with strings marked safe.
from django.utils.html import escape

# Standard Errors
from django.http import Http404

# DEBUG?
from django.conf import settings


# Django decorators
from django.views.decorators.csrf import csrf_protect

# Filetracker info
from downloads import dltools

# Misc object info
from misc import tools as misctools

# Local tools
from wp_main.utilities import utilities
from wp_main.utilities import responses
# For source highlighting
from wp_main.utilities.highlighter import wp_highlighter, get_lexer_name_fromfile, get_lexer_name_fromcontent
# Logging
from wp_main.utilities.wp_logging import logger
_log = logger('viewer').log

# For retrieving project information (source viewing)
from projects import tools as ptools

def logdebug(s):
    """ Write log message only if settings.DEBUG. """
    if settings.DEBUG:
        _log.debug(s)
         
@csrf_protect
def ajax_contents(request):
    """ retrieves file contents per an ajax request. """
    
    if not request.is_ajax():
        raise Http404("File not found, sorry.")
    
    get_data = responses.json_get_request(request)
    
    file_info = {}
    if get_data.get('file', False):
        logdebug('Loading info for file: {}'.format(get_data['file']))
        
        file_info = get_file_info(get_data['file'])
        # Grab DEBUG and send it.
        file_info['debug'] = settings.DEBUG
        
        # highlight file
        file_info['file_content'] = highlight_file(file_info['static_path'], file_info['file_content'])
        
        # override non-serializable project
        project = file_info['project']
        file_info.pop('project')
        # override non-serializable miscobj
        miscobj = file_info['miscobj']
        file_info.pop('miscobj')
        
        # Fill in info for project/miscobj so it can be serialized
        for infoattr in ('name', 'alias', 'version'):
            # Key name for attributes (misc_name, project_version, etc.)
            projkey = 'project_' + infoattr
            misckey = 'misc_' + infoattr
            # Set info if its there, otherwise set None
            file_info[projkey] = getattr(project, infoattr) if project else None
            file_info[misckey] = getattr(miscobj, infoattr) if miscobj else None

        # get a short file name that we can use without shortening it in javascript.
        file_info['file_short'] = utilities.get_filename(file_info['static_path'])
        # get all project related files (if any, otherwise an empty list)
        if project:
            file_info['menu_items'] = [(n, utilities.get_filename(n)) for n in get_source_files(project)]
        else:
            # Misc objects need no menu (False is sent to wpviewer.js:load_file_content())
            file_info['menu_items'] = False
        # send json encoded data.
        return responses.json_response(file_info)
    else:
        raise Http404("No file name provided!")

    
@csrf_protect
def view_loader(request):
    """ accepts GET/POST request containing a filename 'file'.
        uses ajax in loader.html to pass that filename to ajax_contents().
        everything after that is handled in loader.html's javascript
        with the help of wpviewer.js.
        raises 404 on error or file not found..
    """
    
    if request.REQUEST.get('file', False):
        file_path = request.REQUEST['file'].strip("'").strip('"')
        return responses.clean_response_req("viewer/loader.html",
                                            context_dict = {'file': file_path,
                                                            'extra_style_link_list': [utilities.get_browser_style(request),
                                                                                      '/static/css/projects.css',
                                                                                      '/static/css/highlighter.css'],
                                                            },
                                            with_request = request)
    else:
        raise Http404("No file passed to request.")

    
def get_source_files(project):
    """ returns list of all source files for a project, if any.
        uses relative static path. (/static/files/project/source/file.py)
        returns None on  failure.
    """
    
    if project.source_dir == "":
        source_files = []
    else:
        sabsolute = utilities.get_absolute_path(project.source_dir)
        if sabsolute == "":
            source_files = []
        else:
            # retrieve all source filenames
            file_names = os.listdir(sabsolute)
            print str(file_names)
            if len(file_names) == 0:
                source_files = []
            else:
                source_files = []
                for sfilename in file_names:
                    srelativepath = utilities.get_relative_path(os.path.join(project.source_dir, sfilename))
                    source_files.append(srelativepath)
    return source_files
    

def get_using_paths(dir_path, absolute_path=None, proj=None):
    """ When given a dir as a path, find out which file is preferred to use first. """
    
    if absolute_path is None: absolute_path = utilities.get_absolute_path(dir_path)

    if not os.path.isdir(absolute_path): return (None, None)
    
    try:
        files = os.listdir(absolute_path)
    except Exception as ex:
        files = []
        _log.debug("unable to listdir: " + absolute_path + '\n' + str(ex))
        
    # no files in this directory, or bad dir.
    if len(files) == 0: return (None, None)

    # dir has files, get most important to show.
    if proj is None:
        # no project, try first file.
        static_path = utilities.append_path(dir_path, files[0])
        absolute_path = utilities.get_absolute_path(static_path)
        #_log.debug("dir passed: no project for file, using first file: " + absolute_path)
    else:
        # has project, see if source_file is good. if so, use it.
        if proj.source_file:
            static_path = proj.source_file
            absolute_path = utilities.get_absolute_path(static_path)
            #_log.debug("dir passed: using source_file: " + absolute_path)
        else:
            # just use first file found.
            static_path = utilities.append_path(dir_path, files[0])
            absolute_path = utilities.get_absolute_path(static_path)
            #_log.debug("dir passed: no source_file for project, using first file: " + absolute_path)
    
    return (static_path, absolute_path)

def get_file_info(file_path):
    """ retrieves actual file content for viewer. """
    absolute_path = utilities.get_absolute_path(file_path)
    static_path = utilities.get_relative_path(file_path)
    # no file to load.
    if not absolute_path: 
        _log.error('Invalid file path for viewer.get_file_content(): {}'.format(file_path))
        raise Http404("Sorry, that file doesn't exist.")
        
    project = ptools.get_project_from_path(absolute_path)
    
    # Directory was passed, get files to use. (based on project, dir listing)
    if os.path.isdir(absolute_path):
        static_path, absolute_path = get_using_paths(static_path, absolute_path, project)
        if static_path is None or absolute_path is None:
            #return responses.alert_message("Sorry, there was an error viewing that file.", body_message=alertmsg)
            raise Http404("Sorry, there was an error viewing that file.")
        
    # Update project view count tracker
    miscobj = None
    if project:
        project.view_count +=1
        project.save()
    else:
        # Not a project, may be a Misc Object.
        miscobj = misctools.get_by_filename(file_path)
        logdebug('Found Misc Object: {}'.format(repr(miscobj)))
        
        # Update misc view count tracker
        if miscobj:
            miscobj.view_count += 1
            miscobj.save()
        else:
            _log.debug('get_file_content: not a project or misc object: {}'.format(file_path))
            
    # Update file tracker
    if os.path.isfile(absolute_path):
        filetracker = dltools.get_file_tracker(absolute_path)
        if filetracker is not None:
            if project is not None: 
                dltools.update_tracker_projects(filetracker, project, dosave=False)
            filetracker.view_count +=1
            filetracker.save()
    
    # Get file content
    file_content = ""
    try:
        with open(absolute_path) as fread:
            file_content = fread.read()
    except Exception as ex:
        _log.error("Error loading file: " + absolute_path + '\n' + str(ex))
        raise Http404("Sorry, I can't load that file right now.")
    
    fileinfo = {'project': project,
                'miscobj': miscobj,
                'static_path': static_path,
                'absolute_path': absolute_path,
                'file_content': file_content,}
    return fileinfo
    

def highlight_file(static_path, file_content):
    """ highlight file content for viewing """
    
    # Get pygments lexer
    lexername = get_lexer_name_fromfile(static_path)
    if not lexername:
        # Try getting lexer from first line in file.
        lexername = get_lexer_name_fromcontent(file_content)
    
    # Highlight the file (if needed)
    if lexername:
        try:
            highlighter = wp_highlighter(lexername, 'default', line_nums_=False)
            highlighter.code = file_content
            file_content = highlighter.highlight()
        except Exception as ex:
            _log.error("Error highlighting file: " + static_path + '\n' + str(ex))
    else:
        # No lexer, so no highlighting, still need to format it a bit.
        file_content = escape(file_content).replace('\n', '<br>')
        
    return mark_safe(file_content)

    