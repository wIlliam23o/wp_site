# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='wp_image',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('image', models.FileField(upload_to='/img', help_text='The file for the image.', verbose_name='image')),
                ('image_id', models.CharField(blank=True, db_index=True, max_length=255, help_text='Image ID for building urls.', verbose_name='image id')),
                ('publish_date', models.DateTimeField(default=datetime.datetime.now, help_text='When the image was uploaded.', verbose_name='publish date')),
                ('height', models.IntegerField(blank=True, default=0, help_text='The height for the image.', verbose_name='height')),
                ('width', models.IntegerField(blank=True, default=0, help_text='The width for the image.', verbose_name='width')),
                ('album', models.CharField(blank=True, default='', max_length=255, help_text='Album name for this image.', verbose_name='album')),
                ('title', models.CharField(blank=True, default='', max_length=255, help_text='Title for the image.', verbose_name='title')),
                ('description', models.TextField(help_text='Description for this image.', verbose_name='description')),
                ('disabled', models.BooleanField(default=False, help_text='Whether or not this image is listable.', verbose_name='disabled')),
                ('private', models.BooleanField(default=False, help_text='Whether or not this image is private (not listable).', verbose_name='private')),
                ('view_count', models.IntegerField(default=0, help_text='How many times this image has been viewed.', verbose_name='view count')),
            ],
            options={
                'get_latest_by': 'publish_date',
                'verbose_name': 'Image',
                'db_table': 'wp_images',
                'ordering': ['-publish_date'],
                'verbose_name_plural': 'Images',
            },
            bases=(models.Model,),
        ),
    ]
