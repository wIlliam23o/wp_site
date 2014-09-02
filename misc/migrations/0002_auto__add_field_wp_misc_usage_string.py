# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'wp_misc.usage_string'
        db.add_column('misc_wp_misc', 'usage_string',
                      self.gf('django.db.models.fields.TextField')(default='', max_length=5000, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'wp_misc.usage_string'
        db.delete_column('misc_wp_misc', 'usage_string')


    models = {
        'misc.wp_misc': {
            'Meta': {'object_name': 'wp_misc', 'ordering': "['name']"},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'content': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'contentfile': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '512', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1024', 'blank': 'True'}),
            'disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'download_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'filename': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '512', 'blank': 'True'}),
            'filetype': ('django.db.models.fields.CharField', [], {'default': "'None'", 'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'None'", 'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'publish_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2014, 9, 1, 0, 0)'}),
            'usage_string': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '5000', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'default': "'1.0.0'", 'max_length': '120', 'blank': 'True'}),
            'view_count': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['misc']