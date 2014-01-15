#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
      project: wrapper for logging module
     @summary: provides easy setup/access to correct log files.
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 21, 2013
'''

import logging
from logging.handlers import RotatingFileHandler
from django.conf import settings
from os.path import join as pathjoin


class logger(object):

    def __init__(self, logname, use_file_in_debug=True):
        # initialize logger with name (from module)
        self.log = logging.getLogger(logname)
        # file will always be used in production site.
        usefile = True
        
        # use file during debug mode?
        if (bool(settings.DEBUG) and (not use_file_in_debug)):
            usefile = False

        # prepare file handler.
        if usefile:
            # put log file in base dir.
            filename = pathjoin(settings.BASE_DIR, 'welbornprod.log')
            # build rotating file handler
            # max size is about 2MB, no backups will be made.
            self.filehandler = RotatingFileHandler(filename,
                                                   maxBytes=2097152,
                                                   backupCount=0)
            # format for logging messages
            logformat = ('%(asctime)s - [%(levelname)s] '
                         '%(name)s.%(funcName)s (%(lineno)d):\n %(message)s\n')
            self.formatter = logging.Formatter(logformat)
            self.filehandler.setFormatter(self.formatter)
            self.log.addHandler(self.filehandler)

    def setlevel(self, lvl):
        """ Sets the underlying logging.log level. """
        self.level = lvl
        self.log.setLevel(self.level)
