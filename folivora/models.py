import time
import urlparse
import datetime

import pytz

from django.db import models
from django.db.models.signals import post_save
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import make_aware

from django.contrib.auth.models import User

from django_orm.postgresql import hstore

from folivora.utils.pypi import DEFAULT_SERVER, CheeseShop


PROVIDES = ('pypi',)


class Package(models.Model):
    PYPI = 'pypi'
    PROVIDER_CHOICES = (
        ('PyPi', PYPI),
    )

    name = models.CharField(_('name'), max_length=255, unique=True)
    url = models.URLField(_('url'))
    provider = models.CharField(_('provider'), max_length=255,
        choices=PROVIDER_CHOICES)
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

    def __unicode__(self):
        return '{}{}'.format(self.package.name, self.version)


class ProjectMember(models.Model):
    OWNER = 0
    MEMBER = 1
    STATE_CHOICES = (
        (_('owner'), OWNER),
        (_('member'), MEMBER)
    )

    project = models.ForeignKey('Project', verbose_name=_('project'))
    user = models.ForeignKey(User, verbose_name=_('user'))
    state = models.IntegerField(_('state'), choices=STATE_CHOICES)
    mail = models.EmailField(_('Email'), max_length=255, null=True)
    jabber = models.CharField(_('Jabber'), max_length=255, blank=True)

    class Meta:
        verbose_name = _('project member')
        verbose_name_plural = _('project members')


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


class ProjectDependency(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('project'))
    package = models.ForeignKey(Package, verbose_name=_('package'))
    version = models.CharField(_('version'), max_length=255)
    update = models.ForeignKey(PackageVersion,
                               verbose_name=_('update'),
                               null=True,
                               blank=True,
                               default=None)

    class Meta:
        verbose_name = _('project dependency')
        verbose_name_plural = _('project dependencies')


class Log(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('project'))
    when = models.DateTimeField(_('when'))
    action = models.CharField(_('action'), max_length=255)
    type = models.CharField(_('type'), max_length=255)
    data = data = hstore.DictionaryField()

    objects = hstore.HStoreManager()

    class Meta:
        verbose_name = _('log')
        verbose_name_plural = _('logs')


class SyncState(models.Model):
    """Generic model to store syncronization states."""
    CHANGELOG = 'changelog'

    TYPE_CHOICES = (
        (_('Changelog'), CHANGELOG),
    )

    type = models.CharField(max_length=255, choices=TYPE_CHOICES, unique=True)
    last_sync = models.DateTimeField(_('Last Sync'))


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    language = models.CharField(_('Language'), max_length=255)
    timezone = models.CharField(_('Timezone'), max_length=255)
    jabber = models.CharField(_('Jabber'), max_length=255, blank=True)

    def get_absolute_url(self):
        return reverse('folivora_profile_edit')


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


post_save.connect(create_user_profile, sender=User)
