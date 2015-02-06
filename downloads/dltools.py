#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
      project: Welborn Productions - Downloads - Tools
     @summary: Various tools for the downloads app, such as file tracking.

      @author: Christopher Welborn <cj@welbornprod.com>
@organization: welborn productions <welbornprod.com>

   start date: May 25, 2013
'''
import logging

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from downloads.models import file_tracker

from img import tools as imgtools
from misc import tools as misctools
from projects import tools as ptools
from projects.models import wp_project

log = logging.getLogger('wp.downloads.tools')


def get_file_tracker(absolute_path, createtracker=True, dosave=False):
    """ gets an existing file_tracker, or creates a new one from a filename """
    try:
        filetracker = file_tracker.objects.get(filename=absolute_path)
    except MultipleObjectsReturned:
        log.error('File tracker has multiple objects!: '
                  '{}'.format(absolute_path))
        return None
    except ObjectDoesNotExist:
        if createtracker:
            try:
                # create new tracker
                filetracker = file_tracker()
                filetracker.set_filename(absolute_path, dosave=False)
            except Exception as ex:
                log.error('Unable to create new file tracker for: '
                          '{}\n{}'.format(absolute_path, ex))
                filetracker = None
            else:
                log.debug('Created a new file tracker: {}'.format(
                    absolute_path))
        else:
            filetracker = None
    except Exception as ex:
        log.error('Error retrieving file tracker: {}'.format(absolute_path))
        return None

    if (filetracker is not None) and (dosave):
        filetracker.save()
    return filetracker


def increment_dl_count(file_path, absolute_path):
    """ Reverse lookup of a model instance by it's related file name.
        Arguments:
            file_path      : Relative file path.
            absolute_path  : Absolute file path.
        Returns an instance on success, or None on failure.
    """
    try:
        trackables = {
            n: o for n, o in (
                ('project', ptools.get_project_from_path(absolute_path)),
                ('filetracker', get_file_tracker(absolute_path)),
                ('misc', misctools.get_by_filename(file_path)),
                ('image', imgtools.get_by_filename(absolute_path))
            ) if o
        }
    except Exception as ex:
        log.error('Trackables failed!: {}'.format(ex))
        return None

    log.debug('Found {} trackables.'.format(len(trackables)))

    if trackables.get('project', None) and trackables.get('filetracker', None):
        update_tracker_projects(
            trackables['filetracker'],
            trackables['project'])

    for objtype, obj in trackables.items():
        if hasattr(obj, 'download_count'):
            obj.download_count += 1
            obj.save()
            log.debug('Incremented {} download_count to {}: {}'.format(
                objtype,
                obj.download_count,
                obj))
        else:
            log.error('Trackable object has no download_count: {}'.format(obj))


def update_tracker_views(absolute_path, createtracker=True, dosave=True):
    """ update a file tracker's view_count,
        will create the file_tracker if wanted.
    """

    filetracker = get_file_tracker(absolute_path, createtracker)
    if filetracker is None:
        return None

    filetracker.view_count += 1
    log.debug('Updated file_tracker.view_count: {} = {}'.format(
        filetracker,
        filetracker.view_count))
    if dosave:
        filetracker.save()

    return filetracker


def update_tracker_projects(tracker, project, dosave=True):
    """ Adds a project to this tracker's project field safely. """

    if not isinstance(project, wp_project):
        log.debug('Not a project: {}'.format(wp_project))
        return None

    trackerid = getattr(tracker, 'id', None)
    if trackerid is None:
        log.debug('No tracker.id: {}'.format(tracker))
        return None

    # Tracker must be saved at least once before adding a project relation.
    if trackerid < 0:
        tracker.save()

    projectid = getattr(project, 'id', None)
    if tracker.project.get(id=projectid):
        # Project already added to this tracker.
        log.debug('Tracker already added: {}, Project: {}'.format(
            tracker,
            project))
        return None

    tracker.project.add(project)
    log.debug('Added new tracker to project: {} -> {}'.format(
        tracker,
        project))
    if dosave:
        tracker.save()
