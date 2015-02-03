# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('misc', '0002_auto_20150112_1614'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wp_misc',
            name='publish_date',
            field=models.DateField(default=datetime.date(2015, 2, 2), help_text='Date the misc object was published. (Automatically set to today.)'),
        ),
    ]
