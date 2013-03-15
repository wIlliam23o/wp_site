# basic Response/Template/Context stuff...
from django.http import HttpResponse
from django.template import Context, loader

# User-Agent helper...
from django_user_agents.utils import get_user_agent #@UnresolvedImport

# various welbornprod tools
from wp_main import utilities
# logging
import logging

def index(request):
    """ serve up main site """
    
    # setup logging
    wp_log = logging.getLogger("welbornprod.index")
    wp_log.debug("Requested page: " + request.path)

    
    # get user agent
    user_agent = get_user_agent(request)
    browser_name = user_agent.browser.family.lower()
    # log browser name
    wp_log.debug("Browser: " + user_agent.browser.family)
    # get browser css to use...
    if browser_name.startswith("ie"):
        extra_style_link = "/static/css/main-ie.css"
    elif "firefox" in browser_name:
        extra_style_link = "/static/css/main-gecko.css"
    elif "chrome" in browser_name:
        extra_style_link = "/static/css/main-webkit.css"
    else:
        extra_style_link = False
    
        
    
    # initialize main template
    tmp_main = loader.get_template('home/index.html')
    default_content = browser_name
    # load variables into template
    c_main = Context({'extra_style_link': extra_style_link,
                      'default_content': default_content})

    # render final page
    return HttpResponse(utilities.clean_template(tmp_main, c_main))
