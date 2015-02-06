# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('misc', '0004_auto_20150205_1553'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wp_misc',
            name='publish_date',
            field=models.DateField(help_text='Date the misc object was published. (Automatically set to today.)', default=datetime.date.today),
        ),
    ]
