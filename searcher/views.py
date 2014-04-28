# Global settings
#from django.conf import settings
from django.utils.safestring import mark_for_escaping

# Local tools
from wp_main.utilities import responses
from wp_main.utilities import utilities
from wp_main.utilities.wp_logging import logger
_log = logger("search").log

# Search tools
from searcher import searchtools


def view_index(request):
    """ displays search form for welbornprod search queries """
    
    # get search query, if any.
    query = responses.get_request_arg(request, ['q', 'query', 'search'], default="")

    # no query, show search form.
    if not query:
        return responses.clean_response("searcher/searchform.html",
                                        {'request': request,
                                         'extra_style_link_list': [utilities.get_browser_style(request),
                                                                   '/static/css/searcher.min.css'],
                                         })
    else:
        # pass it to view_results
        return view_results(request, query)


def view_results(request, query):
    """ searches welbornprod content and returns the findings. """
    
    # search is okay until it's ran through our little 'gotcha' checker below.
    results_list, results_slice = ([], [])
    search_warning = searchtools.valid_query(query)
        
    if not search_warning:
        # search terms are okay, let's do it.
        results_list = searchtools.search_all(query, projects_first=True)
        results_slice = utilities.slice_list(results_list, starting_index=0, max_items=25)
    
    return responses.clean_response("searcher/results.html",
                                    {'request': request,
                                     'search_warning': search_warning,
                                     'results_list': results_slice,
                                     'query_text': query,
                                     'query_safe': mark_for_escaping(query),
                                     'results_count': len(results_list),
                                     'extra_style_link_list': [utilities.get_browser_style(request),
                                                               "/static/css/searcher.min.css",
                                                               "/static/css/highlighter.min.css"],
                                     })


def view_paged(request):
    """ views page slice of results using GET args. """
    
    # intialize results in case of failure...
    results_list, results_slice = ([], [])
    
    # get query
    query = responses.get_request_arg(request, ['q', 'query', 'search'], default="")
    query_safe = mark_for_escaping(query)
    
    # check query
    search_warning = searchtools.valid_query(query)
    page_args = None
    # search okay?
    if search_warning == '':
        # get initial results
        results_list = searchtools.search_all(query, projects_first=True)
            
        # get overall total count
        results_count = len(results_list)
        
        # get args
        page_args = responses.get_paged_args(request, results_count)
        # results slice
        if results_count > 0:
            results_slice = utilities.slice_list(results_list,
                                                 starting_index=page_args['start_id'],
                                                 max_items=page_args['max_items'])
        else:
            results_slice = []
    # No args provided?
    if not page_args:
        errmsgs = ['No arguments provided.']
        friendly = 'That page needs more info to work correctly.'
        return responses.error500(request, msgs=errmsgs, user_error=friendly)
    
    # get last index.
    end_id = str(page_args['start_id'] + len(results_slice))
    hasnxt = (page_args['start_id'] < (results_count - page_args['max_items']))
    hasprv = (page_args['start_id'] > 0)
    context = {
        "request": request,
        "search_warning": search_warning,
        "results_list": results_slice,
        "query_text": query,
        "query_safe": query_safe,
        "start_id": (page_args['start_id'] + 1),
        "end_id": end_id,
        "results_count": results_count,
        "prev_page": page_args['prev_page'],
        "next_page": page_args['next_page'],
        "has_prev": hasprv,
        "has_next": hasnxt,
        "extra_style_link_list": [utilities.get_browser_style(request),
                                  "/static/css/searcher.min.css",
                                  "/static/css/highlighter.min.css"],
    }
    return responses.clean_response("searcher/results_paged.html", context)
