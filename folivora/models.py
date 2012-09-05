# -*- coding: utf-8 -*-
import time
import urlparse
import datetime

import pytz

from django.conf import settings
from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import make_aware, now

from django.contrib.auth.models import User

from django_orm.postgresql import hstore

from .utils.pypi import DEFAULT_SERVER, CheeseShop


PROVIDES = ('pypi',)


class Package(models.Model):
    PYPI = 'pypi'
    PROVIDER_CHOICES = (
        (PYPI, 'PyPi'),
    )

    name = models.CharField(_('name'), max_length=255, unique=True)
    url = models.URLField(_('url'))
    provider = models.CharField(_('provider'), max_length=255,
        choices=PROVIDER_CHOICES, default=PYPI)
    initial_sync_done = models.BooleanField(default=False)

    @classmethod
    def create_with_provider_url(cls, name, provider='pypi', url=None):
        if url is None:
            url = urlparse.urljoin(DEFAULT_SERVER, name)
        pkg = cls(name=name, url=url, provider=provider)
        pkg.save()
        return pkg

    def sync_versions(self):
        if self.initial_sync_done:
            return
        client = CheeseShop()
        versions = client.get_package_versions(self.name)
        for version in versions:
            urls = client.get_release_urls(self.name, version)
            if urls:
                url = urls[0]
                utime = time.mktime(url['upload_time'].timetuple())
                release_date = make_aware(
                    datetime.datetime.fromtimestamp(utime),
                    pytz.UTC)
                PackageVersion.objects.get_or_create(
                    package=self,
                    version=version,
                    release_date=release_date)
        self.initial_sync_done = True
        self.save()

    class Meta:
        verbose_name = _('package')
        verbose_name_plural = _('packages')
        unique_together = ('name', 'provider')

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)


class PackageVersion(models.Model):
    package = models.ForeignKey(Package, verbose_name=_('package'),
                                related_name='versions')
    version = models.CharField(_('version'), max_length=255)
    release_date = models.DateTimeField(_('release date'))

    class Meta:
        verbose_name = _('package version')
        verbose_name_plural = _('package versions')
        unique_together = ('package', 'version')

    def __unicode__(self):
        return '{}{}'.format(self.package.name, self.version)


class ProjectMember(models.Model):
    OWNER = 0
    MEMBER = 1
    STATE_CHOICES = (
        (OWNER, _('Owner')),
        (MEMBER, _('Member'))
    )

    project = models.ForeignKey('Project', verbose_name=_('project'))
    user = models.ForeignKey(User, verbose_name=_('user'))
    state = models.IntegerField(_('state'), choices=STATE_CHOICES)
    mail = models.EmailField(_('Email'), max_length=255, blank=True)
    jabber = models.CharField(_('Jabber'), max_length=255, blank=True)

    class Meta:
        verbose_name = _('project member')
        verbose_name_plural = _('project members')
        unique_together = ('project', 'user')


class Project(models.Model):
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), unique=True)
    members = models.ManyToManyField(User, through=ProjectMember,
          verbose_name=_('members'))

    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')

    @models.permalink
    def get_absolute_url(self):
        return 'folivora_project_detail', (), {'slug': self.slug}

    def create_logentry(self, type, action, user=None, **kwargs):
        Log.objects.create(project=self, type=type,
                           action=action, data=kwargs, user=user)

    @property
    def requirements(self):
        query = ProjectDependency.objects.filter(project=self) \
                                         .select_related('package') \
                                         .order_by('package__name')
        return "\n".join([d.dependency_string for d in query])

    @property
    def requirement_dict(self):
        query = ProjectDependency.objects.filter(project=self) \
                                         .select_related('package')
        return dict((d.package.name, d.version) for d in query)

    def process_changes(self, user, remove=None, change=None, add=None):
        log_entries = []

        remove = remove if remove else []
        change = change if change else []
        add = add if add else []

        for package_id, version in add:
            log_entries.append(Log(type='project_dependency', action='add',
                                   project_id=self.pk, package_id=package_id,
                                   user=user, data={'version': version}))
        for package_id, version in remove:
            log_entries.append(Log(type='project_dependency', action='remove',
                                   project_id=self.pk, package_id=package_id,
                                   user=user, data={'version': version}))
        for package_id, old_version, new_version in change:
            log_entries.append(Log(type='project_dependency', action='update',
                                   project_id=self.pk, package_id=package_id,
                                   user=user, data={'version': new_version,
                                         'old_version': old_version}))

        Log.objects.bulk_create(log_entries)
        from .tasks import sync_project
        # give the request time to finish before syncing
        sync_project.apply_async(args=[self.pk], countdown=1)

    @property
    def owners(self):
        return self.members.filter(projectmember__state=ProjectMember.OWNER)


class ProjectDependency(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('project'),
                                related_name='dependencies')
    package = models.ForeignKey(Package, verbose_name=_('package'))
    version = models.CharField(_('version'), max_length=255)
    update = models.ForeignKey(PackageVersion, verbose_name=_('update'),
                               null=True, blank=True, default=None)

    class Meta:
        verbose_name = _('project dependency')
        verbose_name_plural = _('project dependencies')
        unique_together = ('project', 'package')

    @property
    def dependency_string(self):
        return u"%s==%s" % (self.package.name, self.version)

    @property
    def update_available(self):
        return self.update_id is not None

    @classmethod
    def process_formset(cls, formset, original_data, user):
        remove = []
        change = []
        for instance in formset.deleted_objects:
            remove.append((instance.package.id, instance.version))
        for instance, d in formset.changed_objects:
            existing = original_data[instance.pk]
            change.append((instance.package.id,
                           existing.version,
                           instance.version))
        formset.instance.process_changes(user, remove, change)


class Log(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('project'))
    package = models.ForeignKey(Package, verbose_name=_('package'),
                                null=True, blank=True, default=None)
    user = models.ForeignKey(User, verbose_name=_('user'), null=True)
    when = models.DateTimeField(_('when'), default=now)
    action = models.CharField(_('action'), max_length=255)
    type = models.CharField(_('type'), max_length=255)
    data = hstore.DictionaryField()

    objects = hstore.HStoreManager()

    class Meta:
        verbose_name = _('log')
        verbose_name_plural = _('logs')

    @property
    def template(self):
        return 'folivora/notifications/{}.{}.html'.format(self.type,
                                                          self.action)


class SyncState(models.Model):
    """Generic model to store syncronization states."""
    CHANGELOG = 'changelog'

    TYPE_CHOICES = (
        (_('Changelog'), CHANGELOG),
    )

    STATE_DOWN = 'down'
    STATE_RUNNING = 'running'

    STATE_CHOICES = (
        (_('Down'), STATE_DOWN),
        (_('Running'), STATE_RUNNING),
    )

    type = models.CharField(max_length=255, choices=TYPE_CHOICES, unique=True)
    state = models.CharField(max_length=255, choices=STATE_CHOICES,
                             default=STATE_RUNNING)
    last_sync = models.DateTimeField(_('Last Sync'), default=now)


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    language = models.CharField(_('Language'), max_length=255,
                                choices=settings.LANGUAGES, blank=True)
    timezone = models.CharField(_('Timezone'), max_length=255, default='UTC')
    jabber = models.CharField(_('JID'), max_length=255, blank=True)

    def get_absolute_url(self):
        return reverse('folivora_profile_edit')
