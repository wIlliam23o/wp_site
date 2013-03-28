#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: welborn productions utilities - responses
     @summary: provides easy access to HttpResponse/Request objects/functions.
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 27, 2013
'''

# Global settings
from django.conf import settings
# Local tools
from wp_main.utilities import htmltools
# Log
from wp_main.utilities.wp_logging import logger
_log = logger("welbornprod.utilities.responses", use_file=(not settings.DEBUG))
# Template loading, and Contexts
from django.http import HttpResponse
from django.template import Context, loader
# Mark Html generated by these functions as safe to view.
from django.utils.safestring import mark_safe

def clean_template(template_, context_, force_ = False):
    """ renders a template with context and 
        applies the cleaning functions.
        
        Email addresses are hidden with hide_email(),
        then fixed on document load with wptools.js.
        
        Blank Lines, Whitespace, Comments are removed if DEBUG = True.
        if DEBUG = False then New Lines are removed also (to minify)
    """
    
    # these things have to be done in a certain order to work correctly.
    # hide_email, remove_comments, remove_whitespace, remove_newlines
    clean_output = htmltools.remove_whitespace(
                        htmltools.remove_comments(
                        htmltools.hide_email(template_.render(context_))))

    if ((not settings.DEBUG) or (force_)):
        # minify (kinda)
        clean_output = htmltools.remove_newlines(clean_output)
    return clean_output


def alert_message(alert_msg, body_message="<a href='/'><span>Click here to go home</span></a>", noblock=False):
    """ Builds an alert message, and returns the HttpResponse object. 
        alert_message: What to show in the alert box.
        body_message: Body content wrapped in a wp-block div.
                      Default is "Click here to go home."
        noblock: Don't wrap in wp-block div if True.
    
    """
    
    if noblock:
        main_content = body_message
    else:
        main_content = "<div class='wp-block'>" + body_message + "</div>"
    tmp_notfound = loader.get_template('home/main.html')
    cont_notfound = Context({'main_content': mark_safe(main_content),
                             'alert_message': mark_safe(alert_msg),
                             })
    rendered = clean_template(tmp_notfound, cont_notfound, (not settings.DEBUG))
    return HttpResponse(rendered)


def basic_response(scontent='', *args, **kwargs):
    """ just a wrapper for the basic HttpResponse object. """
    return HttpResponse(scontent, args, kwargs)


def render_response(template_name, context_dict):
    """ same as render_to_response, 
        loads template, renders with context,
        returns HttpResponse.
    """
    
    try:
        tmp_ = loader.get_template(template_name)
        cont_ = Context(context_dict)
        rendered = tmp_.render(cont_)
    except:
        rendered = alert_message("Sorry, there was an error loading this page.")
    return HttpResponse(rendered)

def clean_response(template_name, context_dict):
    """ same as render_response, except does code minifying/compression 
        (compresses only if settings.DEBUG=False)
        returns cleaned HttpResponse.
    """
    
    try:
        tmp_ = loader.get_template(template_name)
    except Exception as ex:
        _log.error("clean_response: could not load template: " + template_name + '<br/>\n' + \
                   str(ex))
        rendered = None
    else:
        try:
            cont_ = Context(context_dict)
        except Exception as ex:
            _log.error("clean_response: could not load context: " + str(context_dict) + "<br/>\n" + \
                       str(ex))
            rendered = None
        else:
            try:
                rendered = clean_template(tmp_, cont_, (not settings.DEBUG))
            except Exception as ex:
                _log.error("clean_response: could not clean_template!<br/>\n" + str(ex))
                rendered = None
    if rendered is None:
        return alert_message("Sorry, there was an error loading this page.")
    else:
        return HttpResponse(rendered)


def redirect_response(redirect_to):
    """ returns redirect response.
        redirects user to redirect_to.
    """
    
    response = HttpResponse(redirect_to, status=302)
    response['Location'] = redirect_to
    return response


def get_request_arg(request, arg_name, default_value=None, min_val=0, max_val=9999):
    """ return argument from request (GET or POST),
        default value can be set.
        automatically returns int/float values instead of string where needed.
        min/max can be set for integer/float values.
    """
    
    try:
        val = request.REQUEST[arg_name]
    except:
        # no arg passed.
        val = ""
    
    if val.isalnum():
        # check min/max for int values
        try:
            int_val = int(val)
            if (int_val < min_val):
                int_val = min_val
            if (int_val > max_val):
                int_val = max_val
            # return float instead of string
            val = int_val
        except:
            pass
    else:
        # try float, check min/max if needed.
        try:
            float_val = float(val)
            if (float_val < min_val):
                float_val = min_val
            if (float_val > max_val):
                float_val = max_val
            # return float instead of string
            val = float_val
        except:
            pass
    
    # default value is empty string if none was passed.
    if default_value is None:
        default_value = ""    
    # final return after processing,
    # will goto default value if val is empty.
    if val == "":
        val = default_value
    return val
        
    
def wsgi_error(request, smessage):
    """ print message to requests wsgi errors """
    
    request.META['wsgi_errors'] = smessage
   
