from django.db import models


PROVIDES = ('pypi',)


class Package(models.Model):
    name = models.CharField(max_length=255, unique=True)
    url = models.URLField()
    provider = models.CharField(max_length=255, choices=(('PyPi', 'pypi'),))

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)


class PackageVersion(models.Model):
    package = models.ForeignKey(Package)
    version = models.CharField(max_length=255)
    release_date = models.DateTimeField()
