from django.http import HttpResponse
from django.template import Context, loader
from django.utils.safestring import mark_safe # don't escape html with strings marked safe.

from projects.models import wp_project


def index(request):
    """ Main Project Page (index/listing) """
    
    tmp_main = loader.get_template('projects/index.html')
    
    if wp_project.objects.count() == 0:
        projects_content = "<span>Sorry, no projects available yet.</span>"
    else:
        # load all projects...
        projects_content = ""
        all_projects = wp_project.objects.all()
        for proj in all_projects:
            proj_content = "<div class='project_container'>" + \
                "<div class='project_header'>" + \
                "<span class='project_name'>" + proj.name + "</span><br/>" + \
                "<span class='project_version'>version " + proj.version + "</span><br/>" + \
                "</div>" + \
                "<span class='project_desc'>" + proj.description + "</span>" + \
                "</div>"
            projects_content += wrap_link(proj_content, proj.name.lower().replace(' ', ''))
            
    # build context (mark content as safe so we can build our page using html)
    context_main = Context({'projects_content': mark_safe(projects_content)})
    return HttpResponse(tmp_main.render(context_main))

def project_page(request, project, source=""):
    """ Project Page (for individual project) """
    
    # Get project page template
    tmp_project = loader.get_template("projects/index.html")
    
    ######## TEST ##########
    s = "<span>Requested project: " + project.name + "</span><br/>"
    s += "<span>ID = " + str(project.id) + "</span>"
    
    if s != "":
        s += "<br/><span>Came from " + source + "</span>"
    
    projects_content = s
    #########################
    
    # Build Context for project...
    cont_project = Context({'projects_content': mark_safe(projects_content)})
    return HttpResponse(tmp_project.render(cont_project))


def by_id(request, _id):
    """ returns project by id """
    
    proj = wp_project.objects.get(id = safe_arg(_id))
    return project_page(request, proj, source="by_id")


def by_alias(request, _alias):
    """ returns project by alias """
    
    proj = wp_project.objects.get(alias = safe_arg(_alias))
    return project_page(request, proj, source="by_alias")


def by_name(request, _name):
    """ returns project by name """
    
    proj = wp_project.objects.get(name = safe_arg(_name))
    return project_page(request, proj, source="by_name")


def safe_arg(_url):
    """ basically just trims the / from the end of urls right now """
    
    s = _url
    if s.endswith('/'):
        s = s[:-1]
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

    
        