import logging

from django.views.decorators.cache import cache_page

from projects.models import wp_project

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

    if not all_projects:
        alertmsg = 'Sorry, no projects yet.'
        response = responses.alert_message(request, alert_msg=alertmsg)
    else:
        context = {
            'projects': all_projects,
        }
        response = responses.clean_response(
            'projects/index.html',
            context=context,
            request=request)

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
        return responses.error404(
            request,
            'Project not found: {}'.format(requested_page)
        )

    # possible matches passed?
    matches = project if isinstance(project, set) else None
    if matches:
        project = None

    # Grab project info
    if project:
        # this will tell the template to add the screenshots javascript.
        use_screenshots = project.screenshot_dir != ''
        # keep track of how many times this has been viewed.
        project.view_count += 1
        project.save()

    # Grab projects list for vertical menu
    all_projects = wp_project.objects.filter(disabled=False).order_by('name')
    context = {
        'requested_page': requested_page,
        'projects': all_projects,
        'project': project,
        'matches': matches,
        'use_screenshots': use_screenshots,
    }
    return responses.clean_response(
        'projects/project.html',
        context=context,
        request=request)


def request_any(request, identifier):
    """ returns project by name, alias, or id
        returns list of possible matches on failure.
        returns project on success
    """

    proj = get_withmatches(identifier)
    return view_project(request, proj, identifier, source='by_any')


def request_id(request, _id):
    """ returns project by id """

    proj = get_byid(_id)
    return view_project(request, proj, str(_id), source='by_id')


def request_alias(request, alias):
    """ returns project by alias """

    proj = get_byalias(alias)
    return view_project(request, proj, alias, source='by_alias')


def request_name(request, name):
    """ returns project by name """

    proj = get_byname(name)
    return view_project(request, proj, name, source='by_name')


def get_byname(name):
    """ safely retrieve project by name
        returns None on failure. """

    try:
        proj = wp_project.objects.get(name=name, disabled=False)
        return proj
    except wp_project.DoesNotExist:
        # long search..
        name = name.lower().replace(' ', '')
        for proj in wp_project.objects.filter(disabled=False):
            projname = proj.name.lower().replace(' ', '')
            if projname == name:
                return proj
        return None
    except Exception:
        return None


def get_byalias(alias):
    """ safely retrieve project by alias
        returns None on failure. """

    try:
        proj = wp_project.objects.get(alias=alias, disabled=False)
        return proj
    except (wp_project.DoesNotExist, Exception):
        return None


def get_byid(_id):
    """ safely retrieve project by id
        returns None on failure. """

    try:
        proj = wp_project.objects.get(id=_id, disabled=False)
        return proj
    except (wp_project.DoesNotExist, Exception):
        return None


def get_withmatches(identifier):
    """ safely retrieve project by name, alias, or id.
        returns project on success,
        return list of possible close matches on failure
    """
    identifiers = str(identifier).split(' ')

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
