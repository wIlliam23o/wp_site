import logging
import os.path
# Standard Errors
from django.http import Http404

# DEBUG?
from django.conf import settings

# Django decorators
from django.views.decorators.csrf import csrf_protect

# Local tools
from wp_main.utilities import utilities, responses
# Filetracker info
from downloads import dltools
# For retrieving project information (source viewing)
from projects import tools as ptools
# Misc object info
from misc import tools as misctools


log = logging.getLogger('wp.viewer')


@csrf_protect
def ajax_contents(request):
    """ retrieves file contents per an ajax request. """

    if not request.is_ajax():
        return responses.json_response_err(Http404("File not found, sorry."))

    get_data = responses.json_get_request(request)

    file_info = {}
    if get_data.get('file', False):
        log.debug('Loading info for file: {}'.format(get_data['file']))

        try:
            file_info = get_file_info(get_data['file'])
        except Exception as ex:
            return responses.json_response_err(ex)

        if not file_info:
            badfile = get_data.get('file', '<No Filename>')
            log.error('ajax_contents(): File not found: {}'.format(badfile))
            exc = Http404('File not found, sorry.')
            return responses.json_response_err(exc)

        # Grab DEBUG and send it.
        file_info['debug'] = settings.DEBUG

        # override non-serializable project
        project = file_info['project']
        file_info.pop('project')
        # override non-serializable miscobj
        miscobj = file_info['miscobj']
        file_info.pop('miscobj')

        # Fill in info for project/miscobj so it can be serialized
        for infoattr in ('name', 'alias', 'version'):
            # Key name for attributes (misc_name, project_version, etc.)
            projkey = 'project_' + infoattr
            misckey = 'misc_' + infoattr
            # Set info if its there, otherwise set None
            file_info[projkey] = getattr(project, infoattr) if project else None  # noqa
            file_info[misckey] = getattr(miscobj, infoattr) if miscobj else None  # noqa

        # get a short file name that we can use for display.
        file_info['file_short'] = utilities.get_filename(file_info['static_path'])  # noqa
        # get all project related files (if any, otherwise an empty list)
        if project:
            file_info['menu_items'] = sorted([(n, utilities.get_filename(n))
                                              for n in
                                              get_source_files(project)])  # noqa
        else:
            # Misc objects need no menu
            # (False is sent to wpviewer.js:load_file_content())
            file_info['menu_items'] = False
        # send json encoded data.
        return responses.json_response(file_info)
    else:
        log.error('ajax_contents(): No file name provided.')
        return responses.json_response_err(Http404("No file name provided!"))


@csrf_protect
def view_loader(request):
    """ accepts GET/POST request containing a filename 'file'.
        uses ajax in loader.html to pass that filename to ajax_contents().
        everything after that is handled in loader.html's javascript
        with the help of wpviewer.js.
        raises 404 on error or file not found..
    """
    rawpath = request.POST.get('file', request.GET.get('file', ''))
    if rawpath:
        file_path = utilities.strip_chars(rawpath, ('"', "'"))
        context = {
            'file': file_path,
        }

        return responses.clean_response(
            'viewer/loader.html',
            context=context,
            request=request)

    log.error('Empty file name given: {}'.format(
        utilities.get_remote_ip(request))
    )
    raise Http404('No file name given.')


def get_source_files(project):
    """ returns list of all source files for a project, if any.
        uses relative static path. (/static/files/project/source/file.py)
        returns None on  failure.
    """

    if project.source_dir == "":
        source_files = []
    else:
        sabsolute = utilities.get_absolute_path(project.source_dir)
        if sabsolute == "":
            source_files = []
        else:
            # retrieve all source filenames
            file_names = os.listdir(sabsolute)

            if len(file_names) == 0:
                source_files = []
            else:
                source_files = []
                for sfilename in file_names:
                    srelativepath = utilities.get_relative_path(os.path.join(project.source_dir, sfilename))  # noqa
                    source_files.append(srelativepath)
    return source_files


def get_using_paths(dir_path, absolute_path=None, proj=None):
    """ When given a dir as a path,
       find out which file is preferred to use first.
    """

    if absolute_path is None:
        absolute_path = utilities.get_absolute_path(dir_path)

    if not os.path.isdir(absolute_path):
        return (None, None)

    try:
        files = os.listdir(absolute_path)
    except Exception as ex:
        files = []
        log.debug("unable to listdir: " + absolute_path + '\n' + str(ex))

    # no files in this directory, or bad dir.
    if len(files) == 0:
        return (None, None)

    # dir has files, get most important to show.
    if proj is None:
        # no project, try first file.
        static_path = utilities.append_path(dir_path, files[0])
        absolute_path = utilities.get_absolute_path(static_path)

    else:
        # has project, see if source_file is good. if so, use it.
        if proj.source_file:
            static_path = proj.source_file
            absolute_path = utilities.get_absolute_path(static_path)
            # log.debug("dir passed: using source_file: " + absolute_path)
        else:
            # just use first file found.
            static_path = utilities.append_path(dir_path, files[0])
            absolute_path = utilities.get_absolute_path(static_path)

    return (static_path, absolute_path)


def get_file_info(file_path):
    """ retrieves actual file content for viewer. """
    absolute_path = utilities.get_absolute_path(file_path)
    static_path = utilities.get_relative_path(file_path)
    # no file to load.
    if not absolute_path:
        log.error(
            'Invalid file path for viewer.get_file_content(): {}'.format(
                file_path))
        raise Http404('Sorry, that file doesn\'t exist.')

    project = ptools.get_project_from_path(absolute_path)

    # Directory was passed, get files to use. (based on project, dir listing)
    if os.path.isdir(absolute_path):
        if project:
            static_path, absolute_path = get_using_paths(
                static_path,
                absolute_path,
                project)
            if static_path is None or absolute_path is None:
                # Raise error which will display a 404.
                raise Http404('Sorry, there was an error viewing that file.')
        else:
            raise Http404('Sorry, that file doesn\'t exist.')

    # Update project view count tracker
    miscobj = None
    if project:
        project.view_count += 1
        project.save()
    else:
        # Not a project, may be a Misc Object.
        miscobj = misctools.get_by_filename(file_path)
        log.debug('Found Misc Object: {}'.format(repr(miscobj)))

        # Update misc view count tracker
        if miscobj:
            miscobj.view_count += 1
            miscobj.save()
        else:
            log.debug(
                'get_file_content: not a project or misc object: {}'.format(
                    file_path))

    # Update file tracker
    if os.path.isfile(absolute_path):
        filetracker = dltools.get_file_tracker(absolute_path)
        if filetracker is not None:
            if project is not None:
                dltools.update_tracker_projects(filetracker,
                                                project,
                                                dosave=False)
            filetracker.view_count += 1
            filetracker.save()

    # Get file content
    try:
        with open(absolute_path) as fread:
            file_content = fread.read()
    except Exception as ex:
        log.error('Error loading file: {}\n{}'.format(absolute_path, ex))
        raise Http404('Sorry, I can\'t load that file right now.')

    fileinfo = {
        'project': project,
        'miscobj': miscobj,
        'static_path': static_path,
        'absolute_path': absolute_path,
        'file_content': file_content,
    }
    return fileinfo
