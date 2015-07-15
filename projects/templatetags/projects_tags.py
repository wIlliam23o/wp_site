#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: Welborn Productions - Projects - Template Tags
     @summary: Provides extra functionality to templates in the projects app.

      @author: Christopher Welborn <cj@welbornprod.com>
@organization: welborn productions <welbornprod.com>

   start date: May 31, 2013
'''
import logging
from django import template
from django.utils.safestring import mark_safe  # , mark_for_escaping
from projects import tools as ptools
from wp_main.utilities import utilities, htmltools
import os.path

log = logging.getLogger('wp.projects.tags')

register = template.Library()


@register.tag
def downloads(parser, token):
    """ Renders download links for a project. """
    try:
        tag_name, proj, desc = token.split_contents()
    except ValueError:
        try:
            tag_name, proj = token.split_contents()
        except ValueError:
            tagname = token.contents.split()[0]
            errmsg = '{} expects a wp_project and an optional description.'
            raise template.TemplateSyntaxError(errmsg.format(tagname))
        else:
            desc = None
    if desc is not None:
        if not ((desc[0] == desc[-1]) and (desc[0] in ('"', "'"))):
            errmsg = '{}\'s description argument must be quoted.'
            raise template.TemplateSyntaxError(errmsg.format(tag_name))
    return DownloadLink(proj, desc=desc)


@register.filter
def has_project_html(project):
    """ test to see if project has a valid html file to load. """

    return os.path.isfile(ptools.get_html_file(project))


@register.filter
def process_project_html(project, request=None):
    """ runs the project through some html processing
        for screenshots, article ads, download code, sourceview code, etc.
        works on project.get_html_content() through
        projects.tools.process_injections()
    """
    if project is None:
        log.debug('received None project!')
        return ""

    try:
        projfile = '{}.html'.format(project.alias)
        proj_html = htmltools.load_html_file(
            projfile,
            request=request,
            context={
                'project': project
            })
    except Exception as ex:
        log.debug("Error processing injections:\n" + str(ex))
        return ""
    else:
        return mark_safe(proj_html)


@register.tag
def source_view(parser, token):
    """ Renders source view links for a project. """
    try:
        tag_name, proj, request = token.split_contents()
    except ValueError:
        tagname = token.contents.split()[0]
        errmsg = '{} expects 2 arguments, a wp_project, and a Request.'
        raise template.TemplateSyntaxError(errmsg.format(tagname))
    return SourceView(proj, request)


class DownloadLink(template.Node):

    """ Renders download links for a project if download_url is valid. """

    def __init__(self, project, desc=None):
        self.project = project or None
        self.desc = desc or None

    def render(self, context):
        if self.project is None:
            return ''
        try:
            self.project = template.Variable(self.project).resolve(context)
        except template.VariableDoesNotExist:
            log.error('Bad variable passed: {}'.format(self.project))
            return ''
        if self.desc is not None:
            try:
                desc = template.Variable(self.desc).resolve(context)
            except template.VariableDoesNotExist:
                desc = self.desc
        else:
            desc = None
        self.desc = desc

        content = self.get_download_link()
        return content if content else ''

    def get_download_file_abs(self):
        """ Determines location of download file,
            or returns empty string if we can't find it anywhere.
        """
        if not self.project.download_url:
            log.debug('Project has no download_url: {!r} -> {!r}'.format(
                self.project,
                self.project.download_url
            ))
            return ''
        if utilities.is_file_or_dir(self.project.download_url):
            # already absolute
            return self.project.download_url

        # try absolute_path
        return utilities.get_absolute_path(self.project.download_url)

    def get_download_file(self):
        """ Return relative download path, only if it's valid.
            Returns empty string on invalid or missing paths.
        """
        absolute = self.get_download_file_abs()
        if absolute:
            return utilities.get_relative_path(absolute)
        log.debug('Bad file name passed: {}'.format(absolute))
        return ''

    def get_download_link(self):
        """ Renders the projects/download.html template if download_url is
            valid.
            Returns None on failure.
        """
        filename = self.get_download_file()
        if not (filename and self.project):
            return None

        context = {
            'project': self.project,
            'filename': filename,
            'desc': self.desc
        }

        return htmltools.render_clean(
            'projects/download.html',
            context=context)


class SourceView(template.Node):

    """ Renders the links for viewing source locally for a project. """

    def __init__(self, project, request):
        self.project = project or None
        self.request = request or None

    def render(self, context):
        """ Renders the source view code if available. """
        if (self.project is None) or (self.request is None):
            return ''

        try:
            self.project = template.Variable(self.project).resolve(context)
        except template.VariableDoesNotExist:
            log.error('Bad project variable passed: {}'.format(self.project))
            return ''
        try:
            self.request = template.Variable(self.request).resolve(context)
        except template.VariableDoesNotExist:
            log.error('Bad request variable passed: {}'.format(self.request))
            return ''

        content = self.get_sourceview()
        return content if content else ''

    def get_sourceview(self):
        """ Retrieves code for source viewing.
            Uses sourceview.html template to display.
            The template handles missing information.
            Returns rendered string (html code).
        """
        # has project and request info?
        if (self.project is None) or (self.request is None):
            return None

        # use source_file if no source_dir was set.
        relativefile = utilities.get_relative_path(self.project.source_file)
        relativedir = utilities.get_relative_path(self.project.source_dir)
        relativepath = relativedir if relativedir else relativefile
        # has good link?
        if not relativepath:
            logfmt = 'Missing source file/dir for: {}'
            log.debug(logfmt.format(self.project.name))

        # get default filename to display in link.
        if self.project.source_file:
            file_name = utilities.get_filename(self.project.source_file)
        else:
            file_name = self.project.name

        # get link text
        link_text = '{} (local)'.format(file_name)

        return htmltools.render_clean(
            'projects/sourceview.html',
            context={
                'project': self.project,
                'file_path': relativepath,
                'link_text': link_text,
                'desc_text': None,
            },
            request=self.request)
