""" Welborn Productions - Apps - PhoneWords - Models
    Holds information for the phonewords app.
"""

from django.db import models

import json


class pw_result(models.Model):

    """ Holds a prefetched result from PhoneWords. """

    # Original query for this result (phone number)
    query = models.CharField(
        blank=False,
        max_length=256,
        help_text='Original query for this result.'
    )
    # Length of results from this query
    result_length = models.IntegerField(
        blank=False,
        help_text='Length of results for the query.'
    )
    # Holds all the result items [{combo : wordfound}, ...]
    json = models.TextField(
        blank=False,
        help_text='JSON to hold results list.'
    )

    # Number of attempts needed for this result originally.
    attempts = models.IntegerField(
        blank=False,
        help_text='Number of attempts to get these results.'
    )

    # Disable this result (force re-calculating)
    disabled = models.BooleanField(default=False)

    def __str__(self):
        return '{} : ({} results)'.format(
            self.query,
            self.result_length
        )

    def get_results(self):
        """ Try to parse results_json and return an object.
            Raises InvalidJsonData on failure.
        """

        if self.json:
            try:
                results = json.loads(self.json)
            except ValueError as ex:
                raise InvalidJsonData(ex)
            return results
        # No results to get.
        return None

    def set_results(self, obj, dosave=True):
        """ Set result_json from an object.
            raises InvalidJsonObject on failure.
        """

        try:
            jsonstr = json.dumps(obj)
        except (TypeError, ValueError) as ex:
            raise InvalidJsonObject(ex)

        self.json = jsonstr
        if dosave:
            try:
                self.save()
            except Exception as ex:
                raise InvalidJsonObject(ex)
        return True

    # Meta info for the admin site
    class Meta:
        ordering = ['query']
        verbose_name = "PhoneWords Result"
        verbose_name_plural = "PhoneWords Results"


class InvalidJsonData(ValueError):
    pass


class InvalidJsonObject(ValueError):
    pass
