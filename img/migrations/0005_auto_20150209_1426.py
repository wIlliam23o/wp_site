# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('img', '0004_wp_image_filename'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wp_image',
            name='description',
            field=models.TextField(default='', verbose_name='description', help_text='Description for this image.', blank=True),
        ),
    ]
