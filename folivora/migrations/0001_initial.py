# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Package'
        db.create_table('folivora_package', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('provider', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('initial_sync_done', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('folivora', ['Package'])

        # Adding model 'PackageVersion'
        db.create_table('folivora_packageversion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(related_name='versions', to=orm['folivora.Package'])),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('release_date', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('folivora', ['PackageVersion'])

        # Adding model 'ProjectMember'
        db.create_table('folivora_projectmember', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['folivora.Project'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('state', self.gf('django.db.models.fields.IntegerField')()),
            ('mail', self.gf('django.db.models.fields.EmailField')(max_length=255, blank=True)),
            ('jabber', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('folivora', ['ProjectMember'])

        # Adding model 'Project'
        db.create_table('folivora_project', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
        ))
        db.send_create_signal('folivora', ['Project'])

        # Adding model 'ProjectDependency'
        db.create_table('folivora_projectdependency', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='dependencies', to=orm['folivora.Project'])),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['folivora.Package'])),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('update', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['folivora.PackageVersion'], null=True, blank=True)),
        ))
        db.send_create_signal('folivora', ['ProjectDependency'])

        # Adding model 'Log'
        db.create_table('folivora_log', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['folivora.Project'])),
            ('package', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['folivora.Package'], null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('when', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('action', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('data', self.gf('django_orm.postgresql.hstore.fields.DictionaryField')()),
        ))
        db.send_create_signal('folivora', ['Log'])

        # Adding model 'SyncState'
        db.create_table('folivora_syncstate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('last_sync', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('folivora', ['SyncState'])

        # Adding model 'UserProfile'
        db.create_table('folivora_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('timezone', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('jabber', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('folivora', ['UserProfile'])


    def backwards(self, orm):
        # Deleting model 'Package'
        db.delete_table('folivora_package')

        # Deleting model 'PackageVersion'
        db.delete_table('folivora_packageversion')

        # Deleting model 'ProjectMember'
        db.delete_table('folivora_projectmember')

        # Deleting model 'Project'
        db.delete_table('folivora_project')

        # Deleting model 'ProjectDependency'
        db.delete_table('folivora_projectdependency')

        # Deleting model 'Log'
        db.delete_table('folivora_log')

        # Deleting model 'SyncState'
        db.delete_table('folivora_syncstate')

        # Deleting model 'UserProfile'
        db.delete_table('folivora_userprofile')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'folivora.log': {
            'Meta': {'object_name': 'Log'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'data': ('django_orm.postgresql.hstore.fields.DictionaryField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['folivora.Package']", 'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['folivora.Project']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'when': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        },
        'folivora.package': {
            'Meta': {'object_name': 'Package'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial_sync_done': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'folivora.packageversion': {
            'Meta': {'object_name': 'PackageVersion'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'versions'", 'to': "orm['folivora.Package']"}),
            'release_date': ('django.db.models.fields.DateTimeField', [], {}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'folivora.project': {
            'Meta': {'object_name': 'Project'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'through': "orm['folivora.ProjectMember']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'folivora.projectdependency': {
            'Meta': {'object_name': 'ProjectDependency'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'package': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['folivora.Package']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'dependencies'", 'to': "orm['folivora.Project']"}),
            'update': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['folivora.PackageVersion']", 'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'folivora.projectmember': {
            'Meta': {'object_name': 'ProjectMember'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jabber': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'mail': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['folivora.Project']"}),
            'state': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'folivora.syncstate': {
            'Meta': {'object_name': 'SyncState'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_sync': ('django.db.models.fields.DateTimeField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'folivora.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jabber': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'timezone': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        }
    }

    complete_apps = ['folivora']