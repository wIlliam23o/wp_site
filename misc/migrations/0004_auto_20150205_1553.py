# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('misc', '0003_auto_20150202_1832'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wp_misc',
            name='publish_date',
            field=models.DateField(default=datetime.date(2015, 2, 5), help_text='Date the misc object was published. (Automatically set to today.)'),
        ),
    ]
