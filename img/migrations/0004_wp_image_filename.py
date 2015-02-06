# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('img', '0003_wp_image_download_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='wp_image',
            name='filename',
            field=models.CharField(default='', max_length=1024, db_index=True, verbose_name='file name', blank=True, help_text='File name for this image, read only.'),
            preserve_default=True,
        ),
    ]
