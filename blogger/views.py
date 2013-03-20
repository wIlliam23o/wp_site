from django.http import HttpResponse
from django.template import Context, loader
from django.utils.safestring import mark_safe # don't escape html with strings marked safe.

#from projects import models
from blogger.models import wp_blog
# Global settings (for getting absolute path)
from django.conf import settings

# welborn productions utilities
from wp_main import utilities

def index(request):
    """ index list of all blog posts """
    return HttpResponse("This is the index page for the Blog.")


def view_post(request, _identifier):
    """ view a post by identifier.
        identifier can be:
            pk (id)
            slug
            title
    """
    
    # get post.
    post_ = get_post_byany(_identifier)
    if post_ is None:
        s = "No post found: " + _identifier
    else:
        
        s = "Found post:</br>\n" + \
            post_.title + '<br/>\n' + \
            post_.body + '<br/>\n' #+ \
            #post_.project.objects.all()
        projects = post_.project.all()
        s += "Projects:<br/>\n"
        for proj in projects:
            s += proj.name + " v." +  proj.version + "<br/>\n" 
    return HttpResponse(s)


def view_tags(request):
    """ list all posts by tags (categories) """
    
    return HttpResponse("You are looking for all tags.")


def no_identifier(request):
    """ returns a message when user forgets to add an identifier """
    
    return HttpResponse("You forgot to add an identifier, maybe you meant to visit /blog/?")


def get_post_byany(_identifier):
    """ retrieve blog post by any identifier, returns None on failure """
    
    try:
        id_ = int(_identifier)
        post_ = wp_blog.objects.get(id=id_)
    except:
        post_ = None
    
    if post_ is None:
        try:
            post_ = wp_blog.objects.get(title=_identifier)
        except:
            post_ = None
    if post_ is None:
        # id and title failed, try slug.
        # remove html ending
        if (_identifier.lower().endswith(".html") or
            _identifier.lower().endswith(".htm")):
            _identifier = _identifier[:_identifier.index(".")]
        try:
            post_ = wp_blog.objects.get(slug=_identifier)
        except:
            post_ = None
    return post_
   