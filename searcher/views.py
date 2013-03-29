# Local tools
from wp_main.utilities import responses
from wp_main.utilities import utilities

# Search tools
from searcher import searchtools



def view_index(request):
    """ displays search form for welbornprod search queries """
    
    return responses.clean_response("searcher/searchform.html",
                                    {'extra_style_link': utilities.get_browser_style(request),
                                     
                                     })


def view_results(request, _query):
    """ searches welbornprod content and returns the findings. """
    
    results_list = searchtools.search_all(_query, projects_first=True)
    results_list = utilities.slice_list(results_list, starting_index=0, max_items=25)
    
    return responses.clean_response("searcher/results.html",
                                    {'results_list': results_list,
                                     'results_count': str(len(results_list)),
                                     'extra_style_link': utilities.get_browser_style(request),
                                     })
