# basic Response/Template/Context stuff...
from django.http import HttpResponse
from django.template import Context, loader

# User-Agent helper...
from django_user_agents.utils import get_user_agent #@UnresolvedImport

def index(request):
    """ serve up main site """
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
    
        
    
    # initialize main template
    tmp_main = loader.get_template('home/index.html')
    default_content = browser_name
    # load variables into template
    c_main = Context({'extra_style_link': extra_style_link,
                      'default_content': default_content})
    #    'latest_poll_list': latest_poll_list,
    #})
    return HttpResponse(tmp_main.render(c_main))
