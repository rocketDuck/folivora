import pytz
import mock
from datetime import datetime
from django.test import TestCase
from django.utils.timezone import make_aware
from folivora.models import Package, PackageVersion
from folivora import tasks


class CheesyMock(object):

    def get_package_list(self):
        return ['pmxbot']

    def get_changelog(self, hours, force=False):
        return [['pmxbot', '1101.8.1', 1345259834, 'new release']]


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
                                      release_date=make_aware(datetime(2012, 7, 26, 23, 51, 18), pytz.UTC))
        vers = PackageVersion.objects.get(package__name='gunicorn',
                                          version='0.14.6')
        self.assertEqual(vers.package, pkg)
        self.assertEqual(vers.version, '0.14.6')
        self.assertEqual(vers.release_date,
                         make_aware(datetime(2012, 7, 26, 23, 51, 18), pytz.UTC))


class TestChangelogSync(TestCase):

    @mock.patch('folivora.tasks.CheeseShop', CheesyMock)
    def test_new_release_sync(self):
        result = tasks.sync_with_changelog.apply(throw=True)
        self.assertTrue(result.successful())
        pkg = Package.objects.get(name='pmxbot')
        self.assertEqual(pkg.name, 'pmxbot')
        self.assertEqual(pkg.provider, 'pypi')
        self.assertEqual(pkg.versions.count(), 1)
