# Mark generated Html as safe to view.
# from django.utils.safestring import mark_safe # don't escape html with strings marked safe.

# Project Info
from projects.models import wp_project

# Local tools
from wp_main.utilities import utilities
from wp_main.utilities import responses
#from wp_main.utilities import htmltools
#from projects import tools

# logging
from wp_main.utilities.wp_logging import logger
_log = logger('projects').log


def view_index(request):
    """ Main Project Page (index/listing) [using template instead of hard-coded html] """
    
    # If i can fix the template properly this will be much shorter
    # and probably faster. The old way was my very first Django view ever.
    # Hince the complication and mess.
    
    # get all projects if project is not disabled
    all_projects = [p for p in wp_project.objects.order_by('name') if not p.disabled]
    
    if len(all_projects) == 0:
        response = responses.alert_message(alert_msg="Sorry, no projects found!")
    else:
        response = responses.clean_response("projects/index.html",
                                            {'request': request,
                                             'extra_style_link_list': [utilities.get_browser_style(request),
                                                                       "/static/css/projects.min.css"],
                                             'projects': all_projects,
                                             })
    return response


def view_project(request, project, requested_page, source=None):
    """ Returns project page for individual project. Project object
        must be passed (usually from request_any() which retrieves projects by name,alias,id)
        If a list/tuple of projects is passed as 'project' then it will
        be used as 'possible matches' for bad project name.
    """
    
    # default flags
    use_screenshots = False
    extra_style_link_list = [utilities.get_browser_style(request),
                             "/static/css/projects.min.css",
                             "/static/css/highlighter.min.css"]
    
    # no project, no matches found (or error retrieving).
    if project is None:
        notfound_msg = "<a href='/projects'>Click here to visit a listing of my projects.</a><br/>\n" + \
                       "<span>Or you could try <a href='/search?q={{PAGE}}'>searching</a>...</span>"
        return responses.alert_message(alert_msg="Sorry, I can't find that project.",
                                       body_message=notfound_msg.replace('{{PAGE}}', str(requested_page)))
    
    # possible matches passed?
    matches = project if isinstance(project, (list, tuple)) else None
    if matches:
        project = None
    
    # Grab project info
    if project:
        # this will tell the template to add screenshots javascript.
        use_screenshots = project.screenshot_dir != ''
        # keep track of how many times this has been viewed.
        project.view_count += 1
        project.save()
    
    # Grab projects list for vertical menu
    all_projects = [p for p in wp_project.objects.order_by('name') if not p.disabled]

    return responses.clean_response_req("projects/project.html",
                                        {'request': request,
                                         'requested_page': requested_page,
                                         'extra_style_link_list': extra_style_link_list,
                                         'projects': all_projects,
                                         'project': project,
                                         'matches': matches,
                                         'use_screenshots': use_screenshots,
                                         },
                                        with_request=request)


def request_any(request, identifier):
    """ returns project by name, alias, or id 
        returns list of possible matches on failure.
        returns project on success
    """
    
    proj = get_withmatches(utilities.safe_arg(identifier))
    return view_project(request, proj, identifier, source="by_any")
   
   
def request_id(request, _id):
    """ returns project by id """
    
    proj = get_byid(utilities.safe_arg(_id))
    return view_project(request, proj, str(_id), source="by_id")


def request_alias(request, _alias):
    """ returns project by alias """
    
    proj = get_byalias(utilities.safe_arg(_alias))
    return view_project(request, proj, _alias, source="by_alias")


def request_name(request, _name):
    """ returns project by name """
    
    proj = get_byname(utilities.safe_arg(_name))
    return view_project(request, proj, _name, source="by_name")


def get_byname(_name):
    """ safely retrieve project
        returns None on failure. """
        
    try:
        proj = wp_project.objects.get(name=_name)
        return proj if not proj.disabled else None
    except wp_project.DoesNotExist:
        for proj in wp_project.objects.all():
            if proj.name.lower().replace(' ', '') == _name.lower().replace(' ', ''):
                return proj
        return None
    except:
        return None
    
    
def get_byalias(_alias):
    """ safely retrieve project
        returns None on failure. """
        
    try:
        proj = wp_project.objects.get(alias=_alias)
        return proj if not proj.disabled else None
    except wp_project.DoesNotExist:
        return None
    except:
        return None
    
        
def get_byid(_id):
    """ safely retrieve project
        returns None on failure. """
        
    try:
        proj = wp_project.objects.get(id=_id)
        return proj if not proj.disabled else None
    except:
        return None


def get_withmatches(_identifier):
    """ safely retrieve project by name, alias, or id.
        returns project on success,
        return list of possible close matches on failure 
    """
    identifiers = str(_identifier).split(' ')
    
    try:
        _id = int(identifiers[0])
        proj = get_byid(_id)
    except:
        # not an id, try alias.
        proj = get_byalias(identifiers[0])
        if proj is None:
            # Try name
            proj = get_byname(' '.join(identifiers))
    
    # Search for matches
    if proj is None:
        lst_matches = []
        # Try all words in identifier seperately
        for _word in identifiers:
            _search = str(_word).lower()
            _strim = _search.replace(' ', '')
            # still no project, look for close matches...
            for project in [p for p in wp_project.objects.order_by('name') if not p.disabled]:
                _name = project.name.lower()
                _nametrim = _name.replace(' ', '')
                _alias = project.alias.lower()
                _desc = project.description.lower()
                _desctrim = _desc.replace(' ', '')
                _id = str(project.id)
                # try matching in various ways
                if ((_strim in _nametrim) or
                   (_nametrim in _strim) or
                   (_strim in _desctrim) or
                   (_strim in _alias) or
                   (_alias in _strim) or
                   (_strim in _id)):
                    if not project in lst_matches:
                        lst_matches.append(project)
        # return list of matching projects
        return lst_matches
    else:
        # project was found (only show if its not disabled)
        return proj if not proj.disabled else None
