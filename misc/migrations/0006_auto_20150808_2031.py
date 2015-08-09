# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('misc', '0005_auto_20150205_2000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wp_misc',
            name='filetype',
            field=models.CharField(choices=[('Archive', 'Archive File'), ('Code', 'Code File'), ('Snippet', 'Code Snippet'), ('Executable', 'Executable File'), ('HexChat', 'HexChat Script'), ('None', 'None'), ('Script', 'Script File'), ('Text', 'Text File'), ('XChat', 'XChat Script')], help_text='Type of misc object (snippet, code, archive, text, etc.)', default='None', max_length=100),
        ),
        migrations.AlterField(
            model_name='wp_misc',
            name='language',
            field=models.CharField(choices=[('Bash', 'Bash'), ('C', 'C'), ('C++', 'C++'), ('None', 'None'), ('Perl', 'Perl'), ('PyPy', 'PyPy'), ('Python', 'Python (any)'), ('Python 2', 'Python 2+'), ('Python 3', 'Python 3+'), ('Stackless Python', 'Stackless Python'), ('Visual Basic', 'Visual Basic')], help_text='Programming language for this misc object (None, Python, C, Bash, etc.)', default='None', max_length=100),
        ),
    ]
