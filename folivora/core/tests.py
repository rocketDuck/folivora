import pytz
from datetime import datetime
from django.test import TestCase
from django.utils.timezone import make_aware
from folivora.core.models import Package, PackageVersion


class TestPackageModel(TestCase):

    def test_creation(self):
        Package.objects.create(name='gunicorn',
                               url='http://pypi.python.org/pypi/gunicorn',
                               provider='pypi')
        pkg = Package.objects.get(name='gunicorn')
        self.assertEqual(pkg.name, 'gunicorn')
        self.assertEqual(pkg.url, 'http://pypi.python.org/pypi/gunicorn')
        self.assertEqual(pkg.provider, 'pypi')


class TestPackageVersionModel(TestCase):

    def test_creation(self):
        Package.objects.create(name='gunicorn',
                               url='http://pypi.python.org/pypi/gunicorn',
                               provider='pypi')
        pkg = Package.objects.get(name='gunicorn')
        PackageVersion.objects.create(package=pkg,
                                      version='0.14.6',
                                      release_date=datetime(2012, 7, 26, 23, 51, 18))
        vers = PackageVersion.objects.get(package__name='gunicorn',
                                          version='0.14.6')
        self.assertEqual(vers.package, pkg)
        self.assertEqual(vers.version, '0.14.6')
        self.assertEqual(vers.release_date,
                         make_aware(datetime(2012, 7, 26, 23, 51, 18), pytz.UTC))
