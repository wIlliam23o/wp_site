from django.http import HttpResponse
from django.template import Context, loader
from django.utils.safestring import mark_safe # don't escape html with strings marked safe.

from django.conf import settings
from projects.models import wp_project
from wp_main import utilities

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
        # redirect to actual file.
        response = HttpResponse(static_path, status=302)
        response['Location'] = static_path
        # see if its a project file.
        proj = get_project(absolute_path)
        if proj is not None:
            # increment downloads for this project.
            proj.download_count += 1
            proj.save()
        
    return response


def get_project(file_path):
    """ determines if this file is from a project. 
        returns project object if it is.
        returns None on failure.
    """
    
    # check all project names
    for proj in wp_project.objects.all():
        if proj.alias in str(file_path):
            return proj
    return None
           
    