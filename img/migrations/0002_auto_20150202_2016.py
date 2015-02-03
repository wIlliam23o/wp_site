# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('img', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wp_image',
            name='image',
            field=models.FileField(verbose_name='image', help_text='The file for the image.', upload_to='img'),
        ),
    ]
