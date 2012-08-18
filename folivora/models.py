import urlparse

from django.db import models
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User

from django_orm.postgresql import hstore

from folivora.utils.pypi import DEFAULT_SERVER


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

    @classmethod
    def create_with_provider_url(cls, name, provider='pypi', url=None):
        if url is None:
            url = urlparse.urljoin(DEFAULT_SERVER, name)
        pkg = cls(name=name, url=url, provider=provider)
        pkg.save()
        return pkg

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

    class Meta:
        verbose_name = _('project member')
        verbose_name_plural = _('project members')


class Project(models.Model):
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'))
    members = models.ManyToManyField(User, through=ProjectMember,
          verbose_name=_('members'))

    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')


class ProjectDependency(models.Model):
    project = models.ForeignKey(Project, verbose_name=_('project'))
    package = models.ForeignKey(Package, verbose_name=_('package'))
    version = models.CharField(_('version'), max_length=255)
    update = models.ForeignKey(PackageVersion, verbose_name=_('update'))

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
