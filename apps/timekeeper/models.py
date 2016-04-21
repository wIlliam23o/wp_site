""" Welborn Productions - Apps - TimeKeeper - Models
    Holds information for the timekeeper app.
    -Christopher Welborn 1-11-16
"""
from datetime import datetime, timedelta
import logging
import json

from decimal import Decimal
from moneyed import USD

from django.db import models
from django.conf import settings
from djmoney.models.fields import MoneyField, MoneyPatched
from solo.models import SingletonModel

log = logging.getLogger('wp.apps.timekeeper.models')

# Weekdays, where indexes match what datetime.isoweekday() says.
# isoweekday() is used instead of weekday() for better compatibility with JS's
# getDay().
WEEKDAYS = (
    'sunday',
    'monday',
    'tuesday',
    'wednesday',
    'thursday',
    'friday',
    'saturday',
)

WEEKDAY_CHOICES = tuple((wday, wday.title()) for wday in WEEKDAYS)


def now_plus():
    """ Returns datetime.now() + work_day_hours """
    tkconfig = TKConfig.objects.get()
    return datetime.now() + timedelta(hours=tkconfig.work_day_hours)


def hours_from_secs(seconds):
    """ Return hours from seconds in a float. """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    # Do some rounding.
    if seconds > 30:
        minutes += 1
        seconds = 0
    if minutes > 50:
        hours += 1
        minutes = 0
    return hours + (minutes / 60)


class TKConfig(SingletonModel):
    """ Configuration for TimeKeeper. """
    start_work_day = models.CharField(
        verbose_name='work week start day',
        blank=False,
        max_length=9,
        default='friday',
        choices=WEEKDAY_CHOICES,
        help_text='Starting day for the work week.'
    )

    # For automatic session stop_times.
    work_day_hours = models.FloatField(
        verbose_name='work day hours',
        blank=False,
        default=8.0,
        help_text='Number of hours in a work day.'
    )

    def to_dict(self):
        return {
            'start_work_day': self.start_work_day,
            'work_day_hours': self.work_day_hours,
        }

    def to_json(self, sort_keys=False, indent=0):
        return json.dumps(self.to_dict(), sort_keys=sort_keys, indent=indent)

    class Meta:
        verbose_name = 'timekeeper config'


class TKAddress(models.Model):
    """ A job address, one per job. """
    disabled = models.BooleanField(
        blank=False,
        default=False,
        help_text='Whether this address is disabled (not viewable/included).'
    )
    number = models.IntegerField(
        blank=True,
        default=0,
        help_text='House number for the address.')

    street = models.CharField(
        blank=True,
        max_length=150,
        default='',
        help_text='Street name for the address.')

    city = models.CharField(
        blank=True,
        max_length=150,
        default='jasper',
        help_text='City name for the address.')

    state = models.CharField(
        blank=True,
        max_length=2,
        default='al',
        help_text='State abbreviation for the address.'
    )

    zipcode = models.ForeignKey(
        'TKZipCode',
        verbose_name='zipcode',
        blank=True,
        default=1,
        related_name='addresses',
        related_query_name='address',
        on_delete=models.SET_DEFAULT,
        help_text='ZipCode for the address.')

    def __repr__(self):
        return 'TKAddress({})'.format(
            ', '.join((
                'number={s.number!r}',
                'street={s.street!r}',
                'city={s.city!r}',
                'state={s.state!r}',
                'zipcode={s.zipcode!r}'
            )).format(s=self))

    def __str__(self):
        return self.str_format(joiner=' ')

    def save(self, *args, **kwargs):
        """ Make sure all city, street, and state fields are lower case. """
        self.city = self.city and self.city.lower()
        self.street = self.street and self.street.lower()
        self.state = self.state and self.state.lower()
        return super().save(*args, **kwargs)

    def str_format(self, joiner='\n'):
        return joiner.join((
            '{s.number} {s.street}',
            '{s.city}, {s.state} {s.zipcode}'
        )).format(s=self)

    def to_dict(self):
        return {
            'disabled': self.disabled,
            'number': self.number,
            'street': self.street,
            'city': self.city,
            'state': self.state,
            'zipcode': self.zipcode.to_dict()
        }

    def to_json(self, sort_keys=False, indent=0):
        return json.dumps(self.to_dict(), sort_keys=sort_keys, indent=indent)

    class Meta:
        verbose_name = 'address'
        verbose_name_plural = 'addresses'
        db_table = 'timekeeper_address'


class TKEmployee(models.Model):
    """ A single employee, with a name/wage/etc. """
    disabled = models.BooleanField(
        blank=False,
        default=False,
        help_text='Whether this employee is disabled (not viewable/included).'
    )

    first_name = models.CharField(
        blank=False,
        max_length=25,
        help_text='First name for the employee.'
    )

    last_name = models.CharField(
        blank=False,
        max_length=25,
        help_text='Last name for the employee.'
    )

    wage = MoneyField(
        blank=False,
        max_digits=4,
        decimal_places=2,
        default_currency='USD',
        help_text='Hourly wage for the employee.'
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_DEFAULT,
        blank=True,
        null=True,
        default=None,
        related_name='employee',
        related_query_name='employees',
        help_text='Welborn Prod. user for this employee.'
    )

    def __repr__(self):
        return 'TKEmployee({})'.format(
            ', '.join((
                'first_name={s.first_name!r}',
                'last_name={s.last_name!r}',
                'wage={s.wage}'
            )).format(s=self)
        )

    def __str__(self):
        return self.name()

    def name(self):
        """ Return the full name for this employee. """
        return ' '.join((self.first_name, self.last_name))

    def to_dict(self):
        return {
            'disabled': self.disabled,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'name': self.name(),
            'wage': float(self.wage.amount),
            'user': self.user.get_username() if self.user else None
        }

    def to_json(self, sort_keys=False, indent=0):
        return json.dumps(self.to_dict(), sort_keys=sort_keys, indent=indent)

    class Meta:
        verbose_name = 'employee'
        verbose_name_plural = 'employees'
        db_table = 'timekeeper_employee'


class TKJob(models.Model):
    """ A single job id/name/address. """
    disabled = models.BooleanField(
        blank=False,
        default=False,
        help_text='Whether this job is disabled (not viewable/included).'
    )

    name = models.CharField(
        blank=False,
        max_length=255,
        help_text='A unique name for the job.'
    )

    address = models.ForeignKey(
        'TKAddress',
        verbose_name='address',
        blank=True,
        default=1,
        related_name='jobs',
        related_query_name='job',
        on_delete=models.SET_DEFAULT,
        help_text='Address for the job.')

    paid = models.BooleanField(
        blank=False,
        default=False,
        help_text='Whether this job has been paid for.'
    )

    notes = models.TextField(
        blank=True,
        max_length=1024,
        default='',
        help_text='Notes pertaining to this job (html is okay).'
    )

    def __repr__(self):
        return 'TKJob({})'.format(
            ', '.join((
                'name={s.name!r}',
                'address={s.address!r}'  # ,
                #  'sessions={s.sessions!r}'
            )).format(s=self)
        )

    def __str__(self):
        return '{s.name}: {s.address}'.format(s=self)

    def save(self, *args, **kwargs):
        """ Handle any payment processing automatically when saving. """
        if self.paid:
            # Job is paid, set all sessions as paid.
            self.sessions.update(paid=True)
        else:
            # All sessions are paid, set self as paid.
            for ses in self.sessions.all():
                if not ses.paid:
                    break
            else:
                # All sessions are paid.
                self.paid = True

        return super().save(*args, **kwargs)

    def to_dict(self, include_sessions=True):
        data = {
            'disabled': self.disabled,
            'name': self.name,
            'address': self.address.to_dict(),
            'paid': self.paid,
            'notes': self.notes,
        }
        if include_sessions:
            data['sessions'] = [
                ses.to_dict(include_job=False)
                for ses in self.sessions.all()
            ]
        return data

    def to_json(self, sort_keys=False, indent=0, include_sessions=False):
        return json.dumps(
            self.to_dict(include_sessions=include_sessions),
            sort_keys=sort_keys,
            indent=indent)

    class Meta:
        verbose_name = 'job'
        verbose_name_plural = 'jobs'
        db_table = 'timekeeper_job'


class TKSession(models.Model):
    """ A single work session, with a start/stop time, job id, employees,
        etc.
        There will always be at least one employee per session.
    """
    date_format = '%m-%d-%Y'
    time_format = '%I:%M%p'
    datetime_format = ' '.join((date_format, time_format))

    disabled = models.BooleanField(
        blank=False,
        default=False,
        help_text='Whether this session is disabled (not viewable/included).'
    )

    employees = models.ManyToManyField(
        'TKEmployee',
        verbose_name='employees',
        blank=False,
        related_name='employees',
        related_query_name='employee',
        help_text='Employees for this session.'
    )

    job = models.ForeignKey(
        'TKJob',
        verbose_name='job',
        blank=False,
        on_delete=models.CASCADE,
        related_name='sessions',
        related_query_name='session',
        help_text='Job for this session.'
    )

    start_time = models.DateTimeField(
        blank=False,
        default=datetime.now,
        help_text='Start time for the session.'
    )

    stop_time = models.DateTimeField(
        blank=False,
        default=now_plus,
        help_text='Stop time for the session.'
    )

    paid = models.BooleanField(
        blank=False,
        default=False,
        help_text='Whether this session has been paid for.'
    )

    def __repr__(self):
        return 'TKSession({})'.format(
            ', '.join((
                'job={s.job!r}',
                'employees={s.employees!r}',
                'start_time={s.start_time!r}',
                'stop_time={s.stop_time!r}'
            )).format(s=self)
        )

    def __str__(self):
        return (
            '{jobname} ({hours:0.2f}hrs) {sessiontime}'.format(
                jobname=self.job.name,
                hours=self.hours(),
                sessiontime=self.session_format()
            )
        )

    def day(self, abbreviated=False):
        """ Return the weekday for this session. """
        return self.start_time.strftime('%a' if abbreviated else '%A')

    def duration(self):
        """ Return a timedelta of the duration of this session. """
        return self.stop_time - self.start_time

    def employee_pay(self):
        """ Return each employee's pay for this session in a dict of:
            {TKEmployee: MoneyPatched(USD)}
        """
        return {
            emp: MoneyPatched(
                emp.wage.amount * Decimal(self.hours()),
                USD)
            for emp in self.employees.all()
        }

    def hours(self):
        """ Return the number of hours in a float for this session. """
        return hours_from_secs(self.duration().seconds)

    def in_range(self, date_min, date_max):
        """ Returns True if this session fell between `date_min` and
            `date_max`.
            Times are not included in this comparison, this is a date
            comparison only.

            Arguments:
                date_min  : A datetime() or date(). The session must have
                            started on or after this date.
                date_max  : A datetime() or date(). The session must have
                            ended on or before this date.
        """
        if hasattr(date_min, 'date'):
            date_min = date_min.date()
        if hasattr(date_max, 'date'):
            date_max = date_max.date()
        start_date = self.start_time.date()
        return (start_date >= date_min) and (start_date <= date_max)

    def pay(self, from_emp_pay=None):
        """ Return the total pay for this session in MoneyPatched(USD). """
        return sum((from_emp_pay or self.employee_pay()).values())

    def session_format(self):
        """ Return the start and stop time in a human readable string. """
        return '-'.join((self.start_format(), self.stop_format()))

    def start_format(self):
        """ Return the start time in a human readable string. """
        return self.start_time.strftime(self.time_format)

    def stop_format(self):
        """ Return the stop time in a human readable string. """
        return self.stop_time.strftime(self.time_format)

    def to_dict(self, include_job=True):
        emp_pay = self.employee_pay()
        data = {
            'disabled': self.disabled,
            'employees': [emp.to_dict() for emp in self.employees.all()],
            'start_time': self.start_time.strftime(self.datetime_format),
            'stop_time': self.stop_time.strftime(self.datetime_format),
            'paid': self.paid,
            'day': self.day(),
            'employee_pay': {
                emp.name(): float(money.amount)
                for emp, money in emp_pay.items()
            },
            'pay': float(self.pay(from_emp_pay=emp_pay).amount),
            'hours': self.hours(),
        }
        if include_job:
            data['job'] = self.job.to_dict(include_sessions=False)
        return data

    def to_json(self, sort_keys=False, indent=0, include_job=False):
        return json.dumps(
            self.to_dict(include_job=include_job),
            sort_keys=sort_keys,
            indent=indent)

    class Meta:
        verbose_name = 'session'
        verbose_name_plural = 'sessions'
        ordering = ['-start_time']
        db_table = 'timekeeper_session'


class TKZipCode(models.Model):
    """ A single zip-code. Many Addresses may have the same ZipCode. """
    disabled = models.BooleanField(
        blank=False,
        default=False,
        help_text='Whether this zipcode is disabled (not viewable/included).'
    )
    code = models.CharField(blank=True, max_length=5, default='35501')
    code2 = models.CharField(blank=True, max_length=5, default='')

    def __repr__(self):
        return 'TKZipCode(code={s.code!r}, code2={s.code2!r})'.format(
            s=self
        )

    def __str__(self):
        return self.full_code()

    def full_code(self):
        """ Return the full 10 digit zipcode if set.
            Otherwise return the 5 digit zipcode.
        """
        if self.code2:
            return '-'.join((self.code, self.code2))
        return self.code or ''

    def to_dict(self):
        return {
            'code': self.code,
            'code2': self.code2,
            'full_code': self.full_code()
        }

    def to_json(self, sort_keys=False, indent=0):
        return json.dumps(self.to_dict(), sort_keys=sort_keys, indent=indent)

    class Meta:
        verbose_name = 'zipcode'
        verbose_name_plural = 'zipcodes'
        db_table = 'timekeeper_zipcode'
