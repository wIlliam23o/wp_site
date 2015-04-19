# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='wp_misc',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(help_text='Name for this misc object (must be unique)', max_length=250)),
                ('alias', models.CharField(help_text='Alias for this misc object (used for building urls)', max_length=250)),
                ('description', models.CharField(help_text='Short description for the misc object.', default='', blank=True, max_length=1024)),
                ('version', models.CharField(help_text='Version string in the form of X.X.X', default='1.0.0', blank=True, max_length=120)),
                ('filename', models.CharField(help_text='Main source file for the misc object for viewing/downloading.', default='', blank=True, max_length=512)),
                ('contentfile', models.CharField(help_text='Html file for this misc object, used for long description.', default='', blank=True, max_length=512)),
                ('content', models.TextField(help_text='Content for this misc object (long desc) if contentfile is not used.', default='', blank=True)),
                ('usage_string', models.TextField(help_text='Usage string if this is a full script with cmdline options. (no html allowed)', default='', blank=True, max_length=5000)),
                ('filetype', models.CharField(help_text='Type of misc object (snippet, code, archive, text, etc.)', default='None', choices=[('Archive', 'Archive File'), ('Code', 'Code File'), ('Snippet', 'Code Snippet'), ('Executable', 'Executable File'), ('None', 'None'), ('Script', 'Script File'), ('Text', 'Text File'), ('XChat', 'XChat Script')], max_length=100)),
                ('language', models.CharField(help_text='Code language for this misc object (None, Python, C, Bash, etc.)', default='None', choices=[('Bash', 'Bash'), ('C', 'C'), ('C++', 'C++'), ('None', 'None'), ('Perl', 'Perl'), ('PyPy', 'PyPy'), ('Python', 'Python (any)'), ('Python 2', 'Python 2+'), ('Python 3', 'Python 3+'), ('Stackless Python', 'Stackless Python'), ('Visual Basic', 'Visual Basic')], max_length=100)),
                ('disabled', models.BooleanField(default=False)),
                ('view_count', models.IntegerField(help_text='How many times this misc object has been viewed. (Integer)', default=0)),
                ('download_count', models.IntegerField(help_text='How many times this misc object has been downloaded. (Integer)', default=0)),
                ('publish_date', models.DateField(help_text='Date the misc object was published. (Automatically set to today.)', default=datetime.date(2014, 9, 18))),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'Misc. Object',
                'verbose_name_plural': 'Misc. Objects',
            },
            bases=(models.Model,),
        ),
    ]
