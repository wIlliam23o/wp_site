#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: wrapper for logging module
     @summary: provides easy setup/access to correct log files.
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 21, 2013
'''

import logging
from django.conf import settings
from os.path import join as pathjoin

class logger(object):
    def __init__(self, log_name, use_file_in_debug = True):
        # initialize logger with name (from module)
        self.log = logging.getLogger(log_name)
        # file will always be used in production site.
        use_file = True
        
        # use file during debug mode?
        if (bool(settings.DEBUG) and (not use_file_in_debug)):
            use_file = False

        # prepare file handler.
        if use_file:
            # short filename
            file_name = "welbornprod.log"
            # add base dir
            file_name = pathjoin(settings.BASE_DIR, file_name)
            # build handler
            self.filehandler = logging.FileHandler(file_name)
            # format for logging messages
            log_format = '%(asctime)s - [%(levelname)s] %(name)s.%(funcName)s (%(lineno)d):\n %(message)s\n'
            self.formatter = logging.Formatter(log_format)
            self.filehandler.setFormatter(self.formatter)
            self.log.addHandler(self.filehandler)

    # not using these from now on, we will use logger().log.debug(),
    # to keep better track of funcName and lineno (hopefully),    
    def debug(self, message):
        self.log.debug(message)
    
    def Print(self, message):
        self.debug(message)
           
    def error(self, message):
        self.log.error(message)
        
    def info(self, message):
        self.log.info(message)
        
    def warn(self, message):
        self.log.warn(message)