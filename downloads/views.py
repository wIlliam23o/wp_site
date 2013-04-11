# Mark generated Html as safe to view.
from django.utils.safestring import mark_safe # don't escape html with strings marked safe.
# Project Info
from projects import tools
# Local Tools
from wp_main.utilities import utilities
from wp_main.utilities import responses
from wp_main.utilities.wp_logging import logger
_log = logger('welbornprod.downloads', use_file=True)

def index(request):
    """ default download page, when no file is specified """
    
    return download(request, "")


def download(request, file_path):
    """ provides download of files, 
        tracks download count of projects and possibly others
        by checking file's project owner, incrementing the count,
        and then redirecting to the actual file.
    """
    
    static_path = file_path if (file_path.startswith("/")) else ('/' + file_path)
    absolute_path = utilities.get_absolute_path(file_path)
    if absolute_path == "":
        # File doesn't exist. Return an error.
        _log.debug("file doesn't exist: " + file_path)
        alert_message = "Sorry, that file doesn't exist."
        main_content = "<div class='wp-block'><a href='/'><span>Click here to go home.</span></a></div>"
        response = responses.clean_response("home/main.html",
                                            {'request': request,
                                             'main_content': mark_safe(main_content),
                                             'alert_message': mark_safe(alert_message),
                                             'extra_style_link_list': [utilities.get_browser_style(request)],
                                             })
    else:
        # redirect to actual file.
        response = responses.redirect_response(static_path)
        # see if its a project file.
        proj = tools.get_project_from_path(absolute_path)
        if proj is not None:
            # increment downloads for this project.
            proj.download_count += 1
            proj.save()
        
    return response



           
    