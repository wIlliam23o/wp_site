""" Welborn Productions - Apps - TimeKeeper - Tools
    Provides functions to work with TimeKeeper objects.
    -Christopher Welborn 1-12-16
"""

from datetime import datetime, timedelta

from apps.timekeeper.models import (
    WEEKDAYS,
    TKConfig,
    TKJob,
    TKSession
)

# TKConfig is a SingletonModel. This will only be created once, when
# migrating for the first time, or when the db has been wiped during testing.
config = TKConfig.objects.get_or_create()[0]


def get_week_start(date=None):
    """ Get the starting and ending datetimes for a work week. """
    if date is None:
        date = datetime.now()

    thisweekday = date.isoweekday()
    past_days = get_week_indexes().index(thisweekday)
    start_date = date - timedelta(days=past_days)

    return start_date


def get_week_indexes():
    """ Build a list of WEEKDAYS indexes, starting with start_work_day. """
    start_work_index = WEEKDAYS.index(config.start_work_day)
    weekindexes = list(range(start_work_index, len(WEEKDAYS)))
    if start_work_index > 0:
        # The start day is in the middle of the week, so append the "end"
        # of the week (beginning of an iso week).
        weekindexes.extend(range(start_work_index))
    return weekindexes


def get_week_jobs(date=None):
    """ Return a dict of {TKJob: [TKSessions]} for all
        jobs with sessions in the given work week (determined from `date`).
        Arguments:
            date  : Datetime to get week from.
                    `TKConfig.start_work_day` determines the layout
                    of the sessions, and whether the job/session falls into
                    the week.
    """
    # The starting work week day, based on the `date` given.
    date_min = get_week_start(date).date()
    # The maximum date for this week. It's possible that there are no sessions
    # up to this date (we may be in the middle of a work week).
    # date_max is date_min + 7 days, plus 1 more because __range uses 00:00:00
    # and the end date wouldn't be included.
    date_max = date_min + timedelta(days=8)
    jobsessions = {}
    for job in TKJob.objects.filter(disabled=False):
        sessions = job.sessions.filter(
            disabled=False,
            start_time__range=(date_min, date_max)
        )
        if sessions:
            jobsessions[job] = sessions

    return jobsessions
