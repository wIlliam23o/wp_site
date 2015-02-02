#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
      project: Welborn Productions - Downloads - Tools
     @summary: Various tools for the downloads app, such as file tracking.

      @author: Christopher Welborn <cj@welbornprod.com>
@organization: welborn productions <welbornprod.com>

   start date: May 25, 2013
'''

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from downloads.models import file_tracker
from projects import tools as ptools
from projects.models import wp_project
from misc import tools as misctools

from wp_main.utilities.wp_logging import logger
_log = logger("downloads.tools").log


def get_file_tracker(absolute_path, createtracker=True, dosave=False):
    """ gets an existing file_tracker, or creates a new one from a filename """
    try:
        filetracker = file_tracker.objects.get(filename=absolute_path)
    except MultipleObjectsReturned:
        _log.error('File tracker has multiple objects!: '
                   '{}'.format(absolute_path))
        return None
    except ObjectDoesNotExist:
        if createtracker:
            try:
                # create new tracker
                filetracker = file_tracker()
                filetracker.set_filename(absolute_path, dosave=False)
            except Exception as ex:
                _log.error('Unable to create new file tracker for: '
                           '{}\n{}'.format(absolute_path, ex))
                filetracker = None
        else:
            filetracker = None
    except Exception as ex:
        _log.error('Error retrieving file tracker: {}'.format(absolute_path))
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
    trackables = {
        n: o for n, o in (
            ('project', ptools.get_project_from_path(absolute_path)),
            ('filetracker', get_file_tracker(absolute_path)),
            ('misc', misctools.get_by_filename(file_path))
        ) if o
    }

    if trackables.get('project', None) and trackables.get('filetracker', None):
        #
        update_tracker_projects(
            trackables['filetracker'],
            trackables['project'])

    for obj in trackables.values():
        obj.download_count += 1
        obj.save()


def update_tracker_views(absolute_path, createtracker=True, dosave=True):
    """ update a file tracker's view_count,
        will create the file_tracker if wanted.
    """

    filetracker = get_file_tracker(absolute_path, createtracker)
    if filetracker is None:
        return None

    filetracker.view_count += 1
    if dosave:
        filetracker.save()

    return filetracker


def update_tracker_projects(tracker, project, dosave=True):
    """ Adds a project to this tracker's project field safely. """

    if not isinstance(project, wp_project):
        return None

    trackerid = getattr(tracker, 'id', None)
    if trackerid is None:
        return None

    # Tracker must be saved at least once before adding a project relation.
    if trackerid < 0:
        tracker.save()

    projectid = getattr(project, 'id', None)
    if tracker.project.objects.get(id=projectid):
        # Project already added to this tracker.
        return None

    tracker.project.add(project)
    if dosave:
        tracker.save()
