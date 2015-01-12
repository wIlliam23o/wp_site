# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('misc', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='wp_misc',
            options={'get_latest_by': 'publish_date', 'verbose_name_plural': 'Misc. Objects', 'verbose_name': 'Misc. Object', 'ordering': ['name']},
        ),
        migrations.AlterField(
            model_name='wp_misc',
            name='publish_date',
            field=models.DateField(default=datetime.date(2015, 1, 12), help_text='Date the misc object was published. (Automatically set to today.)'),
        ),
    ]
