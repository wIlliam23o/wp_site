#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: welborn productions - sitemaps - main
     @summary: provides main sitemap for sitemaps framework

      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>

   start date: Apr 3, 2013
'''
import logging
# django cache stuff
from django.views.decorators.cache import never_cache

log = logging.getLogger('wp.sitemaps')
# xml_response.
from wp_main.utilities import responses
# Blog/Project info
from apps.models import wp_app
from blogger.models import wp_blog
from img.models import wp_image
from misc.models import wp_misc
from projects.models import wp_project

# Today's date
from datetime import date


@never_cache
def view_sitemap(request):
    """ Delivers sitemap for current domain using sitemap.xml template """

    # return xml sitemap response
    return responses.xml_response(
        'sitemaps/sitemap.xml',
        context={
            'url_list': [sm_url for sm_url in build_urls(request)]
        }
    )


@never_cache
def view_blank_sitemap(request):
    """ Delivers a blank sitemap
        (for servers that don't need a sitemap like the test-server).
    """

    return responses.text_response('', content_type='application/xml')


@never_cache
def view_byserver(request):
    """ Decides which sitemap to deliver according to server.
        sends blank sitemap to server with names starting with 'test.'
    """

    server_name = request.META['SERVER_NAME']
    if server_name.startswith('test.'):
        return view_blank_sitemap(request)

    # normal sitemap.
    return view_sitemap(request)


def build_app_urls(protocol, domain):
    """ Yields SitemapUrl()s for all web apps. """
    # build apps urls.
    for app in wp_app.objects.filter(disabled=False).order_by('name'):
        yield SitemapUrl(
            rel_location='/apps/{}'.format(app.alias),
            protocol=protocol,
            domain=domain,
            changefreq='monthly',
            lastmod=str(app.publish_date),
            priority='0.9'
        )


def build_blog_urls(protocol, domain):
    """ Yields SitemapUrl()s for all blog posts. """
    for post in wp_blog.objects.filter(disabled=False).order_by('-posted'):
        yield SitemapUrl(
            rel_location='/blog/view/{}'.format(post.slug),
            protocol=protocol,
            domain=domain,
            changefreq='never',
            lastmod=str(post.posted),
            priority='0.5'
        )


def build_img_urls(protocol, domain):
    """ Yields SitemapUrl()s for all img posts. """
    imgs = wp_image.objects.filter(disabled=False, private=False)
    for img in imgs.order_by('-publish_date'):
        yield SitemapUrl(
            rel_location='/img?id={}'.format(img.image_id),
            protocol=protocol,
            domain=domain,
            changefreq='never',
            lastmod=str(img.publish_date.date()),
            priority='0.5'
        )


def build_main_urls(protocol, domain):
    """ Yields SitemapUrl()s for the main pages.  """
    # Main urls and default change frequencies for them.
    url_freq = {
        '/': 'daily',
        '/about': 'monthly',
        '/apps': 'monthly',
        '/projects': 'weekly',
        '/blog': 'daily',
        '/misc': 'weekly',
        '/paste': 'daily',
    }
    today = str(date.today())
    # build basic urls for main site nav.
    for url in url_freq:
        yield SitemapUrl(
            rel_location=url,
            protocol=protocol,
            domain=domain,
            changefreq=url_freq[url],
            lastmod=today,
            priority='0.8'
        )


def build_misc_urls(protocol, domain):
    """ Yields SitemapUrl()s for all misc objects. """
    # build misc urls.
    for misc in wp_misc.objects.filter(disabled=False).order_by('name'):
        yield SitemapUrl(
            rel_location='/misc/{}'.format(misc.alias),
            protocol=protocol,
            domain=domain,
            changefreq='monthly',
            lastmod=str(misc.publish_date),
            priority='0.8'
        )


def build_project_urls(protocol, domain):
    """ Yields SitemapUrl()s for all project pages. """
    for proj in wp_project.objects.filter(disabled=False).order_by('name'):
        yield SitemapUrl(
            rel_location='/projects/{}'.format(proj.alias),
            protocol=protocol,
            domain=domain,
            changefreq='monthly',
            lastmod=str(proj.publish_date),
            priority='0.9'
        )


def build_urls(request):
    """ builds a list of SitemapUrl() containing:
        Full URL, Change Frequency, Last Modified Date
        for main site, projects, and blog sections/items.

        request is a WSGIRequest or HttpRequest object that was
        passed to the view. It is used to determine the protocol (http/https),
        and the domain name.
        (for building location urls like: http://mysite.com/projects/myproject)

        returns list of SitemapUrl()
    """

    try:
        # get protocol
        protocol = 'https' if request.is_secure() else 'http'
    except Exception as ex:
        errmsg = 'build_urls: unable to determine request.is_secure():'
        log.error('{}\n  {}'.format(errmsg, ex))
    else:
        # Find server name (.com or .info)
        serverattrs = (
            'HTTP_X_FORWARDED_HOST',
            'HTTP_X_FORWARDED_SERVER',
            'HTTP_HOST'
        )
        domain = None
        for serverattr in serverattrs:
            if serverattr in request.META.keys():
                # get domain
                domain = request.META[serverattr]
                if domain:
                    break

        # Unable to retrieve server name from request.
        if not domain:
            log.error('build_urls: unable to retrieve domain name!')
        else:
            # url list, consists of SitemapUrl() items containing:
            # (URL, Change Frequency, Last Modified Date)
            yield from build_main_urls(protocol, domain)
            yield from build_project_urls(protocol, domain)
            yield from build_blog_urls(protocol, domain)
            yield from build_misc_urls(protocol, domain)
            yield from build_app_urls(protocol, domain)
            yield from build_img_urls(protocol, domain)


class SitemapUrl(object):  # noqa

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
            log.error('SitemapUrl: get_by_name: error getting attribute: '
                      '{}'.format(attribute_name))
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
                url = SitemapUrl(location_="/projects",
                                  protocol_="http",
                                  domain_="mysite.com")
                loc = url.complete_url()
                # will return:
                #     http://mysite.com/projects
        """

        if (not self.domain) or (not self.protocol):
            surl = self.rel_location
        else:
            surl = ''.join((
                self.protocol,
                '://',
                self.domain,
                self.rel_location
            ))
        return surl
