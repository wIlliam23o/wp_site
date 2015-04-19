# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('img', '0002_auto_20150202_2016'),
    ]

    operations = [
        migrations.AddField(
            model_name='wp_image',
            name='download_count',
            field=models.IntegerField(help_text='How many times this image has been downloaded.', default=0, verbose_name='download count'),
            preserve_default=True,
        ),
    ]
