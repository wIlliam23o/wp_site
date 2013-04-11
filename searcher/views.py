# Global settings
from django.conf import settings
from django.utils.safestring import mark_for_escaping

# Local tools
from wp_main.utilities import responses
from wp_main.utilities import utilities
from wp_main.utilities.wp_logging import logger
_log = logger("welbornprod.search", use_file=(not settings.DEBUG))

# Search tools
from searcher import searchtools



def view_index(request):
    """ displays search form for welbornprod search queries """
    
    # get search query, if any.
    query = responses.get_request_arg(request, ['q', 'query', 'search'])

    # no query, show search form.
    if query == "":
        return responses.clean_response("searcher/searchform.html",
                                        {'request': request,
                                         'extra_style_link_list': [utilities.get_browser_style(request),
                                                                   "/static/css/searcher.css"],
                                         })
    else:
        # pass it to view_results
        return view_results(request, query)


def view_results(request, _query):
    """ searches welbornprod content and returns the findings. """
    
    # 3 character minimum
    if len(_query.replace(' ', '')) < 3:
        search_warning = "3 character minimum, try again."
        results_list = []
        results_slice = []
    else:
        search_warning = ""
        results_list = searchtools.search_all(_query, projects_first=True)
        results_slice = utilities.slice_list(results_list, starting_index=0, max_items=25)
    
    return responses.clean_response("searcher/results.html",
                                    {'request': request,
                                     'search_warning': search_warning,
                                     'results_list': results_slice,
                                     'query_text': _query,
                                     'query_safe': mark_for_escaping(_query),
                                     'results_count': len(results_list),
                                     'extra_style_link_list': [utilities.get_browser_style(request),
                                                               "/static/css/searcher.css",
                                                               "/static/css/highlighter.css"],
                                     })

def view_paged(request):
    """ views page slice of results using GET args. """
    
    # get query
    _query = responses.get_request_arg(request, ['q', 'query', 'search'])
    query_safe = mark_for_escaping(_query)
    
    # 3 character minimum
    if len(_query.replace(' ', '')) < 3:
        search_warning = "3 character minimum, try again."
        results_list = []
    else:
        search_warning = ""
        # get initial results
        results_list = searchtools.search_all(_query, projects_first=True)
        
    # get overall total count
    results_count = len(results_list)
    
    # get args
    page_args = responses.get_paged_args(request, results_count)
    # results slice
    if results_count > 0:
        results_slice = utilities.slice_list(results_list,
                                             starting_index = page_args['start_id'],
                                             max_items = page_args['max_items'])
    else:
        results_slice = []
        
    # get last index.     
    end_id = str(page_args['start_id'] + len(results_slice))
    return responses.clean_response("searcher/results_paged.html",
                                    {"request": request,
                                     "search_warning": search_warning,
                                     "results_list": results_slice,
                                     "query_text": _query,
                                     "query_safe": query_safe,
                                     "start_id": (page_args['start_id'] + 1),
                                     "end_id": end_id,
                                     "results_count": results_count,
                                     "prev_page": page_args['prev_page'],
                                     "next_page": page_args['next_page'],
                                     "has_prev": (page_args['start_id'] > 0),
                                     "has_next": (page_args['start_id'] < (results_count - page_args['max_items'])),
                                     "extra_style_link_list": [utilities.get_browser_style(request),
                                                               "/static/css/searcher.css",
                                                               "/static/css/highlighter.css"],
                                     })