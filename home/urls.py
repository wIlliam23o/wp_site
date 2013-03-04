#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
      project: 
     @summary: 
    
      @author: Christopher Welborn <cj@welbornproductions.net>
@organization: welborn productions <welbornproductions.net>
 
   start date: Mar 3, 2013
'''

from django.conf.urls import patterns, include, url
from home import views

urlpatterns = patterns('',
                      
                      url(r'^$', views.index, name='home')

                      )


