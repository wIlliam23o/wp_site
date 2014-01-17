#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: welborn productions - sitemaps - main
     @summary: provides main sitemap for sitemaps framework
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Apr 3, 2013
'''
# django cache stuff
from django.views.decorators.cache import never_cache
# local logging.
from wp_main.utilities.wp_logging import logger
_log = logger("sitemaps").log
# xml_response.
from wp_main.utilities import responses
# Blog/Project info
from blogger.models import wp_blog
from projects.models import wp_project
# Today's date
from datetime import date


@never_cache
def view_sitemap(request):
    """ delivers sitemap for current domain using sitemap.xml template """
    
    # return xml sitemap response
    return responses.xml_response("sitemaps/sitemap.xml",
                                  {"url_list": get_urls(request),
                                   })


@never_cache
def view_blank_sitemap(request):
    """ delivers a blank sitemap (for servers that don't need a sitemap like the test-server). """
    
    return responses.text_response("", content_type='application/xml')


@never_cache
def view_byserver(request):
    """ decides which sitemap to deliver according to server.
        sends blank sitemap to server with names starting with 'test.'
    """
    
    server_name = request.META['SERVER_NAME']
    if server_name.startswith('test.'):
        return view_blank_sitemap(request)
    else:
        # normal sitemap.
        return view_sitemap(request)
    
  
def get_urls(request):
    """ builds a list of sitemap_url() containing:
        Full URL, Change Frequency, Last Modified Date
        for main site, projects, and blog sections/items.
        
        request is a WSGIRequest or HttpRequest object that was
        passed to the view. It is used to determine the protocol (http/https),
        and the domain name.
        (for building location urls like: http://mysite.com/projects/myproject)
        
        returns list of sitemap_url()
    """
    
    try:
        # get protocol
        protocol_ = 'https' if request.is_secure() else 'http'
    except Exception as ex:
        _log.error('get_urls: unable to determine request.is_secure():\n'
                   '{}'.format(ex))
        return []

    # Find server name (.com or .info)
    serverattrs = ('HTTP_X_FORWARDED_HOST',
                   'HTTP_X_FORWARDED_SERVER',
                   'HTTP_HOST')
    domain_ = None
    for serverattr in serverattrs:
        if serverattr in request.META.keys():
            # get domain
            domain_ = request.META[serverattr]
            if domain_:
                break

    # Unable to retrieve server name from request.
    if not domain_:
        _log.error('get_urls: unable to retrieve domain name!')
        return []
    
    # url list, consists of sitemap_url() items containing:
    # (URL, Change Frequency, Last Modified Date)
    urls_ = []
    # string form of today's date.
    today_ = str(date.today())
    # default change frequencies for main sections.
    default_freqs = {'/': 'daily',
                     '/about': 'monthly',
                     '/projects': 'weekly',
                     '/blog': 'daily',
                     '/misc': 'weekly',
                     }
    # build basic urls for main site nav.
    for main_url in ['/', '/about', '/projects', '/blog', '/misc']:
        _url = sitemap_url(rel_location=main_url,
                           protocol=protocol_,
                           domain=domain_,
                           changefreq=default_freqs[main_url],
                           lastmod=today_,
                           priority='0.8')
        urls_.append(_url)
    
    # build projects urls
    for proj in wp_project.objects.order_by('name'):
        _url = sitemap_url(rel_location='/projects/' + proj.alias,
                           protocol=protocol_,
                           domain=domain_,
                           changefreq='monthly',
                           lastmod=str(proj.publish_date),
                           priority='0.9')
        urls_.append(_url)
    
    # build blog urls
    for post_ in wp_blog.objects.order_by('-posted'):
        _url = sitemap_url(rel_location='/blog/view/' + post_.slug,
                           protocol=protocol_,
                           domain=domain_,
                           changefreq='never',
                           lastmod=str(post_.posted),
                           priority='0.5')
        urls_.append(_url)

    # return complete list.
    return urls_
    
 
class sitemap_url(object):

    """ provides info for individual sitemap urls """
     
    def __init__(self, location='', rel_location='',
                 changefreq='', lastmod='',
                 protocol='http', domain='',
                 priority='0.5'):
        # changes info
        self.changefreq = changefreq
        self.lastmod = lastmod
        # priority
        self.priority = priority
        # location info
        self.rel_location = rel_location
        self.protocol = protocol
        self.domain = domain
        # build complete location if needed.
        if location == '':
            self.location = self.complete_url()
        else:
            self.location = location

    def get_by_name(self, attribute_name):
        """ retrieves url info by name string.
            uses getattr().
            returns value of attribute on success.
            returns empty string on failure.
        """
        
        try:
            if hasattr(self, attribute_name):
                return getattr(self, attribute_name)
            else:
                return ''
        except:
            _log.error("sitemap_url: get_by_name: error getting attribute: " + attribute_name)
            return ''
        
    def get_info_dict(self):
        """ retrieves url info as a dict. """
        
        info_dict = {}
        for attr_name in dir(self):
            # filter builtins and private attributes
            if not attr_name.startswith('_'):
                attr_ = getattr(self, attr_name)
                # filter functions, we only want info not functions.
                if not callable(attr_):
                    info_dict[attr_name] = attr_
                    
        return info_dict
    
    def get_info_list(self):
        """ retrieves url info as a list of [attribute, value].
            list item[0][0] = attribute 1, item[0][1] = value 1.
        """
        info_list = []
        info_dict = self.get_info_dict()
        for skey in info_dict.keys():
            info_list.append([skey, info_dict[skey]])
        return info_list

    def complete_url(self):
        """ builds complete url for this item if all info is present.
             ex:
                url = sitemap_url(location_="/projects", protocol_="http", domain_="mysite.com")
                loc = url.complete_url()
                # will return:
                #     http://mysite.com/projects
        """
        
        if self.domain == "" or self.protocol == "":
            surl = self.rel_location
        else:
            surl = self.protocol + "://" + self.domain + self.rel_location

        return surl
