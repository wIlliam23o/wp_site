#!/usr/bin/env python
'''
    EasySettings Setup
Created on Jan 22, 2013

@author: Christopher Welborn
'''

from distutils.core import setup

setup(
    name='EasySettings',
    version='1.7.5',
    author='Christopher Welborn',
    author_email='cj@welbornproductions.net',
    packages=['easysettings'],
    url='http://pypi.python.org/pypi/EasySettings/',
    license='LICENSE.txt',
    description='Easily save & retrieve your applications settings.',
    long_description=open('README.txt').read(),
)
