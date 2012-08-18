from django.db import models


PROVIDES = ('pypi',)


class Package(models.Model):
    name = models.CharField(max_length=255, unique=True)
    url = models.URLField()
    provider = models.CharField(max_length=255, choices=(('PyPi', 'pypi'),))
