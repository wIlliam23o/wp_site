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

# For today's date
from datetime import date

# django cache stuff
from django.views.decorators.cache import never_cache

# xml_response.
from wp_main.utilities import responses
# Local models to build urls.
from apps.models import wp_app
from blogger.models import wp_blog
from img.models import wp_image
from misc.models import wp_misc
from projects.models import wp_project

log = logging.getLogger('wp.sitemaps')

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
    apps = wp_app.objects.filter(
        disabled=False,
        admin_only=False)
    for app in apps.order_by('name'):
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
        (for building location urls: http://mysite.com/projects/myproject)

        returns list of SitemapUrl()
    """

    try:
        # get protocol
        protocol = 'https' if request.is_secure() else 'http'
    except Exception as ex:
        errfmt = 'build_urls: unable to determine request.is_secure():\n  {}'
        log.error(errfmt.format(ex))
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

    """ Provides info for individual sitemap urls. """

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
        # build complete location on demand if needed.
        self.location = location or self.complete_url()

    def complete_url(self):
        """ builds complete url for this item if all info is present.
             ex:
                url = SitemapUrl(
                    rel_location_='/projects',
                    protocol='http',
                    domain='mysite.com')
                loc = url.complete_url()
                # will return:
                #     http://mysite.com/projects
            This is used to build .location when it isn't set, so
                loc = url.location
            ..will do the same thing.
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
