# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'wp_misc'
        db.create_table('misc_wp_misc', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('alias', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('description', self.gf('django.db.models.fields.CharField')(default='', blank=True, max_length=1024)),
            ('version', self.gf('django.db.models.fields.CharField')(default='1.0.0', blank=True, max_length=120)),
            ('filename', self.gf('django.db.models.fields.CharField')(default='', blank=True, max_length=512)),
            ('contentfile', self.gf('django.db.models.fields.CharField')(default='', blank=True, max_length=512)),
            ('content', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('filetype', self.gf('django.db.models.fields.CharField')(default='None', max_length=100)),
            ('language', self.gf('django.db.models.fields.CharField')(default='None', max_length=100)),
            ('disabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('view_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('download_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('publish_date', self.gf('django.db.models.fields.DateField')(default=datetime.datetime(2014, 9, 1, 0, 0))),
        ))
        db.send_create_signal('misc', ['wp_misc'])


    def backwards(self, orm):
        # Deleting model 'wp_misc'
        db.delete_table('misc_wp_misc')


    models = {
        'misc.wp_misc': {
            'Meta': {'object_name': 'wp_misc', 'ordering': "['name']"},
            'alias': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'content': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'contentfile': ('django.db.models.fields.CharField', [], {'default': "''", 'blank': 'True', 'max_length': '512'}),
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'blank': 'True', 'max_length': '1024'}),
            'disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'download_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'filename': ('django.db.models.fields.CharField', [], {'default': "''", 'blank': 'True', 'max_length': '512'}),
            'filetype': ('django.db.models.fields.CharField', [], {'default': "'None'", 'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'None'", 'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'publish_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2014, 9, 1, 0, 0)'}),
            'version': ('django.db.models.fields.CharField', [], {'default': "'1.0.0'", 'blank': 'True', 'max_length': '120'}),
            'view_count': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['misc']