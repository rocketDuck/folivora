import pytz
import mock

from datetime import datetime

from django.core.files.base import ContentFile
from django.test import TestCase
from django.utils.timezone import make_aware, now
from django.test.client import Client
from django.utils.timezone import make_aware

from django.contrib.auth.models import User

from .models import (Package, PackageVersion, Project, Log,
    ProjectDependency)
from . import tasks
from .utils import get_model_type


class CheesyMock(object):

    def get_package_list(self):
        return ['pmxbot', 'gunicorn']

    def get_changelog(self, hours, force=False):
        return [['pmxbot', '1101.8.1', 1345259834, 'new release'],
                ['gunicorn', '0.14.6', 1345259834, 'remove']]

    def get_release_urls(self, name, version):
        return [{'comment_text': '',
                 'downloads': 0,
                 'filename': 'pmxbot-1101.8.1.zip',
                 'has_sig': False,
                 'md5_digest': '0a945fa5ea023036777b7cfde4518932',
                 'packagetype': 'sdist',
                 'python_version': 'source',
                 'size': 223006,
                 'upload_time': datetime.datetime(2012, 8, 18, 3, 17, 15),
                 'url': 'http://pypi.python.org/packages/source/p/pmxbot/pmxbot-1101.8.1.zip'}]


class TestPackageModel(TestCase):

    def setUp(self):
        pkg = Package.create_with_provider_url('pmxbot')
        project = Project.objects.create(name='test', slug='test')
        dependency = ProjectDependency.objects.create(
            project=project,
            package=pkg,
            version='1101.8.0')

    def test_creation(self):
        Package.objects.create(name='gunicorn',
                               url='http://pypi.python.org/pypi/gunicorn',
                               provider='pypi')
        pkg = Package.objects.get(name='gunicorn')
        self.assertEqual(pkg.name, 'gunicorn')
        self.assertEqual(pkg.url, 'http://pypi.python.org/pypi/gunicorn')
        self.assertEqual(pkg.provider, 'pypi')

    @mock.patch('folivora.tasks.CheeseShop', CheesyMock)
    def test_version_sync(self):
        pkg = Package.objects.get(name='pmxbot')
        self.assertEqual(pkg.versions.count(), 0)
        pkg.sync_versions()
        self.assertEqual(pkg.versions.count(), 1)
        version = pkg.versions.all()[0]
        self.assertEqual(version.version, '1101.8.1')


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

    def setUp(self):
        pkg = Package.create_with_provider_url('pmxbot')
        pkg2 = Package.create_with_provider_url('gunicorn')
        self.project = Project.objects.create(name='test', slug='test')
        dependency = ProjectDependency.objects.create(
            project=self.project,
            package=pkg,
            version='1101.8.0')
        dependency2 = ProjectDependency.objects.create(
            project=self.project,
            package=pkg2,
            version='0.14.6')

    @mock.patch('folivora.tasks.CheeseShop', CheesyMock)
    def test_new_release_sync(self):
        result = tasks.sync_with_changelog.apply(throw=True)
        self.assertTrue(result.successful())
        pkg = Package.objects.get(name='pmxbot')
        self.assertEqual(pkg.name, 'pmxbot')
        self.assertEqual(pkg.provider, 'pypi')
        self.assertEqual(pkg.versions.count(), 1)

    @mock.patch('folivora.tasks.CheeseShop', CheesyMock)
    def test_new_release_sync_dependency_update(self):
        result = tasks.sync_with_changelog.apply(throw=True)
        self.assertTrue(result.successful())
        dep = ProjectDependency.objects.get(package__name='pmxbot', version='1101.8.0', project__name='test')
        self.assertEqual(dep.update.version, '1101.8.1')

    @mock.patch('folivora.tasks.CheeseShop', CheesyMock)
    def test_new_release_sync_log_creation(self):
        result = tasks.sync_with_changelog.apply(throw=True)
        self.assertTrue(result.successful())
        self.assertEqual(Log.objects.filter(project=self.project, action='new_release') \
                                    .count(),
                         1)

    @mock.patch('folivora.tasks.CheeseShop', CheesyMock)
    def test_package_removal_sync(self):
        result = tasks.sync_with_changelog.apply(throw=True)
        self.assertTrue(result.successful())
        # We do not delete packages, check for existence
        self.assertTrue(Package.objects.filter(name='gunicorn').exists())
        # dependency stays the way it was, except that `.update` was cleared.
        dep = ProjectDependency.objects.get(package__name='gunicorn')
        self.assertEqual(dep.update, None)

    @mock.patch('folivora.tasks.CheeseShop', CheesyMock)
    def test_package_removal_sync_log_creation(self):
        result = tasks.sync_with_changelog.apply(throw=True)
        self.assertTrue(result.successful())
        self.assertEqual(Log.objects.filter(project=self.project, action='remove_package') \
                                    .count(),
                         1)


class TestSyncNewProjectTask(TestCase):

    def setUp(self):
        pkg = Package.create_with_provider_url('pmxbot')
        pkg.versions.add(PackageVersion(version='1101.8.0',
                                        release_date=now()))
        pkg.versions.add(PackageVersion(version='1101.8.1',
                                        release_date=now()))
        pkg2 = Package.create_with_provider_url('gunicorn')
        self.project = Project.objects.create(name='test', slug='test')
        dependency = ProjectDependency.objects.create(
            project=self.project,
            package=pkg,
            version='1101.8.0')
        dependency2 = ProjectDependency.objects.create(
            project=self.project,
            package=pkg2,
            version='0.14.6')

    def test_sync_new_project(self):
        result = tasks.sync_new_project.apply(args=(self.project.pk,), throw=True)
        self.assertTrue(result.successful())
        dep = ProjectDependency.objects.get(project=self.project,
                                            package__name='pmxbot',
                                            version='1101.8.0')
        self.assertEqual(dep.update.version, '1101.8.1')


VALID_REQUIREMENTS = 'Django==1.4.1\nSphinx==1.10'
BROKEN_REQUIREMENTS = 'Django==1.4.1\n_--.>=asdhasjk ,,, [borked]\nSphinx==1.10'


class TestProjectForms(TestCase):
    def setUp(self):
        user = User.objects.create_user('apollo13', 'mail@example.com', 'pwd')
        self.c = Client()
        self.c.login(username='apollo13', password='pwd')
        Package.objects.bulk_create([
            Package(name='Django'),
            Package(name='Sphinx')
        ])

    def test_create_project(self):
        """Test that basic project creation works"""
        response = self.c.post('/projects/add/', {'slug':'test', 'name':'test',
            'requirements':ContentFile(VALID_REQUIREMENTS, name='req.txt')})
        self.assertEqual(response.status_code, 302)
        p = Project.objects.get(slug='test')
        # The requirements file contained two requirements
        self.assertEqual(p.dependencies.count(), 2)
        # We should have one member at this stage, the creator of the project
        self.assertEqual(p.members.count(), 1)
        self.assertEqual(p.members.all()[0].username, 'apollo13')

    def test_create_project_with_borked_req(self):
        """Ensure that unsupported requirement lines are skipped"""
        response = self.c.post('/projects/add/', {'slug':'test', 'name':'test',
            'requirements':ContentFile(BROKEN_REQUIREMENTS, name='req.txt')})
        self.assertEqual(response.status_code, 302)
        p = Project.objects.get(slug='test')
        # although the requirements are somewhat borked we import what we can
        self.assertEqual(p.dependencies.count(), 2)


class TestProjectModel(TestCase):

    def setUp(self):
        self.project = Project.objects.create(name='test', slug='test')
        self.user = User.objects.create_user('test', 'test@example.com', 'test')

    def test_create_logentry_basic(self):
        self.project.create_logentry('some_testing', self.user)
        log = Log.objects.get(project=self.project, action='some_testing')
        self.assertEqual(log.project, self.project)
        self.assertEqual(log.type, 'folivora.project')
        self.assertEqual(log.package, None)
        self.assertEqual(log.user, self.user)

    def test_create_logentry_with_data(self):
        self.project.create_logentry('shoutout', self.user,
                                     type=Log,
                                     message='Hey everybody!')
        log = Log.objects.get(project=self.project, action='shoutout')
        self.assertEqual(log.project, self.project)
        self.assertEqual(log.type, 'folivora.log')
        self.assertEqual(log.package, None)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.data['message'], 'Hey everybody!')


class TestUtils(TestCase):

    def test_get_model_type(self):
        self.assertEqual(get_model_type(Package), 'folivora.package')
        self.assertEqual(get_model_type(User), 'auth.user')

