import logging
# Django page caching.
from django.views.decorators.cache import cache_page

# Project Info
from projects.models import wp_project

# Local tools
from wp_main.utilities import utilities
from wp_main.utilities import responses


log = logging.getLogger('wp.projects')


@cache_page(15 * 60)
def view_index(request):
    """ Main Project Page (index/listing)
        [using template instead of hard-coded html]
    """

    # If i can fix the template properly this will be much shorter
    # and probably faster. The old way was my very first Django view ever.
    # Hince the complication and mess.

    # get all projects if project is not disabled
    all_projects = wp_project.objects.filter(disabled=False).order_by('name')

    if len(all_projects) == 0:
        alertmsg = 'Sorry, no projects yet.'
        response = responses.alert_message(request, alert_msg=alertmsg)
    else:
        context = {
            'request': request,
            'projects': all_projects,
        }
        response = responses.clean_response('projects/index.html', context)

    return response


@cache_page(15 * 60)
def view_project(request, project, requested_page, source=None):
    """ Returns project page for individual project.
        Project object must be passed
        (usually from request_any() which retrieves projects by name,alias,id)
        If a list/tuple of projects is passed as 'project' then it will
        be used as 'possible matches' for bad project name.
    """

    # default flags
    use_screenshots = False

    # no project, no matches found (or error retrieving).
    if not project:
        alertmsg = 'Sorry, I can\'t find that project.'
        notfound_msg = (
            '<a href=\'/projects\'>'
            'Click here to visit a listing of my projects.'
            '</a><br/>\n'
            '<span>Or you could try '
            '<a href=\'/search?q={page}\'>searching</a>'
            '...</span>').format(page=str(requested_page))
        return responses.alert_message(
            request,
            alert_msg=alertmsg,
            body_message=notfound_msg)

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
    all_projects = wp_project.objects.filter(disabled=False).order_by('name')
    context = {
        'request': request,
        'requested_page': requested_page,
        'projects': all_projects,
        'project': project,
        'matches': matches,
        'use_screenshots': use_screenshots,
    }
    return responses.clean_response_req(
        'projects/project.html',
        context,
        request=request)


def request_any(request, identifier):
    """ returns project by name, alias, or id
        returns list of possible matches on failure.
        returns project on success
    """

    proj = get_withmatches(utilities.safe_arg(identifier))
    return view_project(request, proj, identifier, source='by_any')


def request_id(request, _id):
    """ returns project by id """

    proj = get_byid(utilities.safe_arg(_id))
    return view_project(request, proj, str(_id), source='by_id')


def request_alias(request, _alias):
    """ returns project by alias """

    proj = get_byalias(utilities.safe_arg(_alias))
    return view_project(request, proj, _alias, source='by_alias')


def request_name(request, _name):
    """ returns project by name """

    proj = get_byname(utilities.safe_arg(_name))
    return view_project(request, proj, _name, source='by_name')


def get_byname(_name):
    """ safely retrieve project by name
        returns None on failure. """

    try:
        proj = wp_project.objects.get(name=_name)
        return proj if not proj.disabled else None
    except wp_project.DoesNotExist:
        # long search..
        _name = _name.lower().replace(' ', '')
        for proj in wp_project.objects.all():
            projname = proj.name.lower().replace(' ', '')
            if projname == _name:
                return proj
        return None
    except:
        return None


def get_byalias(_alias):
    """ safely retrieve project by alias
        returns None on failure. """

    try:
        proj = wp_project.objects.get(alias=_alias)
        return proj if not proj.disabled else None
    except wp_project.DoesNotExist:
        return None
    except:
        return None


def get_byid(_id):
    """ safely retrieve project by id
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

    # Try alias.
    proj = get_byalias(identifiers[0])
    if proj and not proj.disabled:
        return proj

    # Try name
    proj = get_byname(' '.join(identifiers))
    if proj and not proj.disabled:
        return proj

    # Try id.
    try:
        _id = int(identifiers[0])
    except (TypeError, ValueError):
        pass
    else:
        proj = get_byid(_id)
        if proj and not proj.disabled:
            return proj

    # Search for matches
    return search_projects(identifiers)


def match_items(query, items):
    """ Does 'if query in item or item in query' for each
        item in items.
        Ex:
            matched = match_items('test', ('testing', 'es', 'blah'))
            # Returns True on 'testing', but would also return true on 'es'
            # because 'test' is in 'testing', and 'es' is in 'test'.
    """
    for item in items:
        if (query in item) or (item in query):
            return True
    return False


def search_projects(identifiers):
    """ Searches all project attributes, trys to match identifiers string.
        Looks at name, alias, description, and id.
        All .lower() and trimmed of spaces.

        Returns set of project matches, or empty set when nothing matches.
    """
    matches = set()
    # Try all words in identifier seperately
    projects = wp_project.objects.filter(disabled=False).order_by('name')
    # A map of project -> searchable strings
    searchable = {
        p: (
            p.name.lower().replace(' ', ''),
            p.alias.lower(),
            p.description.lower().replace(' ', ''),
            str(p.id)
        )
        for p in projects
    }

    for project in searchable:
        for word in identifiers:
            searchword = str(word).lower()
            # Attributes to search, lowered and trimmed when applicable.
            # try matching in various ways
            if match_items(searchword, searchable[project]):
                matches.add(project)
    return matches
