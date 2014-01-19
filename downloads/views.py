# Mark generated Html as safe to view.
from django.utils.safestring import mark_safe
# Gloval settings
from django.conf import settings

# File tools
import os.path

# Download tools
from downloads import dltools

# Project/Misc Info
from projects import tools as ptools
from misc import tools as misctools
# Local Tools
from wp_main.utilities import utilities
from wp_main.utilities import responses
from wp_main.utilities.wp_logging import logger
_log = logger('downloads').log


def index(request):
    """ default download page, when no file is specified """
    
    return download(request, "")


def download(request, file_path):
    """ provides download of files, 
        tracks download count of projects and possibly others
        by checking file's project owner, incrementing the count,
        and then redirecting to the actual file.
    """

    # File path may be an incomplete path to the actual location.
    # /cedit/source is just as good as /static/files/cedit/source
    # so we must grab the real (absolute) path, and then convert
    # it to a valid static path.
    
    # location on disk
    absolute_path = utilities.get_absolute_path(file_path)
    # location relative to site
    if settings.SERVER_LOCATION == 'local':
        static_path = absolute_path.replace(settings.STATIC_PARENT, '')
    else:
        # remote, file is actually located at the static_server dir.
        # but we will need to forward the user to the /static url.
        static_path = absolute_path.replace(settings.STATIC_ROOT, '')
        if static_path.startswith('/'):
            static_path = '/static{}'.format(static_path)
        else:
            static_path = '/static/{}'.format(static_path)

    # used for local only.
    if (not static_path.startswith('/')):
        static_path = '/{}'.format(static_path)
    
    if not absolute_path:
        # File doesn't exist. Return an error.
        _log.debug("file doesn't exist: " + file_path)
        alert_message = "Sorry, that file doesn't exist."
        main_content = ("<div class='wp-block'>"
                        "<a href='/'><span>Click here to go home.</span></a>"
                        "</div>")
        context = {'request': request,
                   'main_content': mark_safe(main_content),
                   'alert_message': mark_safe(alert_message),
                   'extra_style_link_list':
                   [utilities.get_browser_style(request)],
                   }
        response = responses.clean_response("home/main.html", context)
    else:
        # redirect to actual file.
        #_log.debug("redirecting to: " + static_path)
        response = responses.redirect_response(static_path)
        # File to track? (not a directory)
        if os.path.isfile(absolute_path):
            # see if its a project file.
            proj = ptools.get_project_from_path(absolute_path)
            # update project's download count
            if proj is not None:
                # increment downloads for this project.
                proj.download_count += 1
                proj.save()
            # see if it's a misc file
            misc = misctools.get_by_filename(file_path)
            # update misc files count
            if misc:
                misc.download_count += 1
                misc.save()
                
            # update file tracker info
            filetracker = dltools.get_file_tracker(absolute_path)
            if filetracker is not None:
                if proj is not None:
                    dltools.update_tracker_projects(filetracker, proj)
                
                filetracker.download_count += 1
                filetracker.save()
                 
    return response
