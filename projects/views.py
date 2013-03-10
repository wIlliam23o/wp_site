from django.http import HttpResponse
from django.template import Context, loader
from django.utils.safestring import mark_safe # don't escape html with strings marked safe.

#from projects import models
from projects.models import wp_project
# User-Agent helper...
from django_user_agents.utils import get_user_agent #@UnresolvedImport
# Global settings (for getting absolute path)
from django.conf import settings



import os.path


def index(request):
    """ Main Project Page (index/listing) """
    # get user agent
    user_agent = get_user_agent(request)
    browser_name = user_agent.browser.family.lower()
    
    # get css to use (non-IE, it's handled in the template)...
    if "opera" in browser_name:
        extra_style_link = "/static/css/template-opera.css"
    elif "firefox" in browser_name:
        extra_style_link = "/static/css/template-gecko.css"
    elif "chrome" in browser_name:
        extra_style_link = "/static/css/template-webkit.css"
    else:
        extra_style_link = False    
    tmp_main = loader.get_template('projects/index.html')
    
    if wp_project.objects.count() == 0:
        projects_content = "<span>Sorry, no projects available yet.</span>"
    else:
        # list all projects...
        projects_content = "<div class='project_listing'>\n"
        for proj in wp_project.objects.all().order_by('name'):
            projects_content += project_listing(request, proj)
        projects_content += "</div>\n"     
    # build context (mark content as safe so we can build our page using html)
    context_main = Context({'projects_content': mark_safe(projects_content),
                            'extra_style_link': extra_style_link
                            })
    return HttpResponse(tmp_main.render(context_main))


def project_listing(request, project):
    """ Returns a single project listing when for when building the projects index """
    
    # Build project name/link
    p_namelink = wrap_link("<span class='header project_name'>" + project.name + "</span>", 
                       "/projects/" + project.alias)
    
    # Build project listing module
    _content = "<div class='wp-block project_container'>\n" + \
                "<div class='project_header'>\n" + \
                p_namelink + \
                "<br/>\n" + \
                "<span class='version'>version " + project.version + "</span>\n" + \
                "<br/>\n" + \
                "</div>\n" + \
                "<div class='project_desc'>\n" + \
                "<span class='desc'>" + project.description + "</span>\n" + \
                "</div></div>\n"   
    return _content


def project_page(request, project, requested_page, source=""):
    """ Project Page (for individual project) """
    
    # Get project page template
    tmp_project = loader.get_template("projects/index.html")
    
    
    if isinstance(project, list):
        # no project found, build possible matches..
        if len(project) == 0:
            shtml = "<span>Sorry, no matching projects found for: " + requested_page + "</span>" 
        else:
            # build possible matches..
            shtml = "<div class='surround_matches'>" + \
                "<span>Sorry, I can't find a project at '" + requested_page + "'. Were you " + \
                "looking for one of these?</span><br/>" + \
                "<div class='project_matches'>"
            for proj in project:
                shtml += "<div class='project_match'>"
                p_name = "<span class='match_result'>" + \
                         proj.name + "</span>"
                p_link = "/projects/" + proj.alias
                shtml += wrap_link(p_name, p_link) + \
                     "</div>"
            shtml += "</div></div>"
    else:
        # Found Project, build page.
        salias = project.alias
        shtmlfile = os.path.join(settings.BASE_DIR, "projects/static/html/" + salias + ".html")
        print "HTML File: " + shtmlfile
        
        shtml = "<span>No information found for: " + salias + "</span>"
        if os.path.isfile(shtmlfile):
            with open(shtmlfile) as fhtml:
                shtml = fhtml.read()
                
    
    # Build Context for project...
    cont_project = Context({'projects_content': mark_safe(shtml)})
    return HttpResponse(tmp_project.render(cont_project))


def request_any(request, _identifier):
    """ returns project by name, alias, or id 
        returns list of possible matches on failure.
        returns project on success
    """
    
    proj = get_withmatches(safe_arg(_identifier))
    return project_page(request, proj, _identifier, source="by_any")
   
   
def request_id(request, _id):
    """ returns project by id """
    
    proj = get_byid(safe_arg(_id))
    return project_page(request, proj, str(_id), source="by_id")


def request_alias(request, _alias):
    """ returns project by alias """
    
    proj = get_byalias(safe_arg(_alias))
    return project_page(request, proj, _alias, source="by_alias")


def request_name(request, _name):
    """ returns project by name """
    
    proj = get_byname(safe_arg(_name))
    return project_page(request, proj, _name, source="by_name")


def get_byname(_name):
    """ safely retrieve project
        returns None on failure. """
        
    try:
        proj = wp_project.objects.get(name=_name)
        return proj
    except wp_project.DoesNotExist:
        return None
    except:
        return None
    
    
def get_byalias(_alias):
    """ safely retrieve project
        returns None on failure. """
        
    try:
        proj = wp_project.objects.get(alias=_alias)
        return proj
    except wp_project.DoesNotExist:
        return None
    except:
        return None
    
        
def get_byid(_id):
    """ safely retrieve project
        returns None on failure. """
        
    try:
        proj = wp_project.objects.get(id=_id)
        return proj
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
            for project in wp_project.objects.all():
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
        # project was found
        return proj
    
    
def sorted_projects(sort_method = "date"):
    """ return sorted list of projects.
        sort methods: date, name, id
    """
    
    if sort_method == "date":
        sort_method = "publish_date"
        
    return wp_project.objects.all().order_by(sort_method)

     
def safe_arg(_url):
    """ basically just trims the / from the args right now """
    
    s = _url
    if s.endswith('/'):
        s = s[:-1]
    if s.startswith('/'):
        s = s[1:]
    return s


def wrap_link(content_, link_url, alt_text = ""):
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

    
        