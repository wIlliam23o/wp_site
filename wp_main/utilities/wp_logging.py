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
from os import getcwd

class logger(object):
    def __init__(self, log_name, use_file = False):
        self.log = logging.getLogger(log_name)
        # override default behaviour.
        # force use of file when DEBUG = False.
        if (not use_file) and (not settings.DEBUG):
            use_file = True
        # prepare file handler.
        if use_file:
            # short filename
            file_name = log_name + ".log"
            # trim unwanted info
            if "welbornprod." in file_name:
                file_name = file_name.replace('welbornprod.', '')
            # add base dir
            file_name = pathjoin(settings.BASE_DIR, file_name)
            self.filehandler = logging.FileHandler(file_name)
            self.formatter = logging.Formatter('%(asctime)s - [%(levelname)s] %(message)s')
            self.filehandler.setFormatter(self.formatter)
            self.log.addHandler(self.filehandler)

            
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