# disable cache for ip/useragent pages.
from django.views.decorators.cache import never_cache
from django.db.models import Q
# various welbornprod tools
from wp_main.utilities import (
    utilities,
    responses,
    htmltools,
    tweets
)
from apps.timekeeper import tools
from apps.timekeeper.models import (
    TKJob,
)


@never_cache
def view_index(request):
    """ Default api response. """
    return responses.json_response_err(NotImplementedError('Still working..'))


@never_cache
def view_job(request):
    """ View JSON for a specific job. """
    if not request.user.is_authenticated():
        return responses.json_response_err(Exception('You must login first.'))

    args = (
        responses.json_get_request(request) or
        responses.get_request_args(request)
    )

    jobid = args.get('id', None)
    if not jobid:
        return responses.json_response_err(ValueError('No job id given.'))

    jobs = TKJob.objects.filter(disabled=False)
    try:
        jobintid = int(jobid)
        job = jobs.get(id=jobintid)
    except (ValueError, TypeError, TKJob.DoesNotExist):
        try:
            job = jobs.get(name=jobid)
        except TKJob.DoesNotExist:
            return responses.json_response_err(
                ValueError('No job with that id: {}'.format(jobid)),
                logit=True)

    return responses.json_response({
        'job': job.to_json(include_sessions=True),
        'status': 'ok',
        'message': 'Successfully retrieved job #{}.'.format(job.id)
    })
