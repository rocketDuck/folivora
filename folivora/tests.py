import pytz
import mock

from datetime import datetime

from django.core.files.base import ContentFile
from django.test import TestCase
from django.utils.timezone import make_aware
from django.test.client import Client

from django.contrib.auth.models import User

from .models import (Package, PackageVersion, Project, Log,
    ProjectDependency, ProjectMember)
from . import tasks
from .utils import parse_requirements
from .utils.jabber import is_valid_jid
from .utils.forms import JabberField
from .utils.views import SortListMixin


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
                 'upload_time': datetime(2012, 8, 18, 3, 17, 15),
                 'url': 'http://pypi.python.org/packages/source/p/pmxbot/pmxbot-1101.8.1.zip'}]

    def get_package_versions(self, name):
        if name == 'pmxbot':
            return ['1101.8.1']
        elif name == 'pytz':
            return ['2012d']
        else:
            return ['0']


class TestPackageModel(TestCase):

    def setUp(self):
        pkg = Package.create_with_provider_url('pmxbot')
        project = Project.objects.create(name='test', slug='test')
        ProjectDependency.objects.create(
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

    @mock.patch('folivora.models.CheeseShop', CheesyMock)
    def test_version_sync(self):
        pkg = Package.objects.get(name='pmxbot')
        self.assertEqual(pkg.versions.count(), 0)
        pkg.sync_versions()
        self.assertEqual(pkg.versions.count(), 1)
        version = pkg.versions.all()[0]
        self.assertEqual(version.version, '1101.8.1')
        self.assertNumQueries(0, pkg.sync_versions)


class TestPackageVersionModel(TestCase):

    def test_creation(self):
        Package.objects.create(name='gunicorn',
                               url='http://pypi.python.org/pypi/gunicorn',
                               provider='pypi')
        pkg = Package.objects.get(name='gunicorn')
        dt = make_aware(datetime(2012, 7, 26, 23, 51, 18), pytz.UTC)
        PackageVersion.objects.create(package=pkg,
                                      version='0.14.6',
                                      release_date=dt)
        vers = PackageVersion.objects.get(package__name='gunicorn',
                                          version='0.14.6')
        self.assertEqual(vers.package, pkg)
        self.assertEqual(vers.version, '0.14.6')
        self.assertEqual(vers.release_date, dt)


class TestChangelogSync(TestCase):

    def setUp(self):
        pkg = Package.create_with_provider_url('pmxbot')
        pkg2 = Package.create_with_provider_url('gunicorn')
        self.project = Project.objects.create(name='test', slug='test')
        ProjectDependency.objects.create(
            project=self.project,
            package=pkg,
            version='1101.8.0')
        ProjectDependency.objects.create(
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
        dep = ProjectDependency.objects.get(package__name='pmxbot',
                                            version='1101.8.0',
                                            project__name='test')
        self.assertEqual(dep.update.version, '1101.8.1')
        self.assertTrue(dep.update_available)

    @mock.patch('folivora.tasks.CheeseShop', CheesyMock)
    def test_new_release_sync_log_creation(self):
        result = tasks.sync_with_changelog.apply(throw=True)
        self.assertTrue(result.successful())
        qs = Log.objects.filter(project=self.project, action='new_release')
        self.assertEqual(qs.count(), 1)

    @mock.patch('folivora.tasks.CheeseShop', CheesyMock)
    def test_package_removal_sync(self):
        result = tasks.sync_with_changelog.apply(throw=True)
        self.assertTrue(result.successful())
        # We do not delete packages, check for existence
        self.assertTrue(Package.objects.filter(name='gunicorn').exists())
        # dependency stays the way it was, except that `.update` was cleared.
        dep = ProjectDependency.objects.get(package__name='gunicorn')
        self.assertEqual(dep.update, None)
        self.assertFalse(dep.update_available)

    @mock.patch('folivora.tasks.CheeseShop', CheesyMock)
    def test_package_removal_sync_log_creation(self):
        result = tasks.sync_with_changelog.apply(throw=True)
        self.assertTrue(result.successful())
        qs = Log.objects.filter(project=self.project, action='remove_package')
        self.assertEqual(qs.count(), 1)


class TestSyncProjectTask(TestCase):

    def setUp(self):
        pkg = Package.create_with_provider_url('pmxbot')
        pkg2 = Package.create_with_provider_url('gunicorn')
        pkg3 = Package.create_with_provider_url('pytz')
        self.project = Project.objects.create(name='test', slug='test')
        ProjectDependency.objects.create(
            project=self.project,
            package=pkg,
            version='1101.8.0')
        ProjectDependency.objects.create(
            project=self.project,
            package=pkg2,
            version='0.14.6')
        ProjectDependency.objects.create(
            project=self.project,
            package=pkg3,
            version='2012a')

    @mock.patch('folivora.models.CheeseShop', CheesyMock)
    def test_sync_project(self):
        result = tasks.sync_project.apply(args=(self.project.pk,), throw=True)
        self.assertTrue(result.successful())
        dep = ProjectDependency.objects.get(project=self.project,
                                            package__name='pmxbot')
        self.assertEqual(dep.update.version, '1101.8.1')
        dep = ProjectDependency.objects.get(project=self.project,
                                            package__name='pytz')
        self.assertEqual(dep.update.version, '2012d')
        dep = ProjectDependency.objects.get(project=self.project,
                                            package__name='gunicorn')
        self.assertEqual(dep.update, None)


VALID_REQUIREMENTS = 'Django==1.4.1\nSphinx==1.10'
BROKEN_REQUIREMENTS = ('Django==1.4.1\n_--.>=asdhasjk ,,, [borked]\n'
                       'Sphinx==1.10')


class TestProjectForms(TestCase):
    def setUp(self):
        User.objects.create_user('apollo13', 'mail@example.com', 'pwd')
        self.c = Client()
        self.c.login(username='apollo13', password='pwd')
        Package.objects.bulk_create([
            Package(name='Django'),
            Package(name='Sphinx')
        ])

    def test_create_project_without_req(self):
        response = self.c.post('/projects/add/',
                               {'slug': 'test', 'name': 'test'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                         'http://testserver/project/test/')

    def test_create_project(self):
        """Test that basic project creation works"""
        response = self.c.post('/projects/add/', {
            'slug': 'test', 'name': 'test',
            'requirements': ContentFile(VALID_REQUIREMENTS, name='req.txt')})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                         'http://testserver/project/test/')
        p = Project.objects.get(slug='test')
        # The requirements file contained two requirements
        self.assertEqual(p.dependencies.count(), 2)
        # We should have one member at this stage, the creator of the project
        self.assertEqual(p.members.count(), 1)
        self.assertEqual(p.members.all()[0].username, 'apollo13')

    def test_create_project_with_borked_req(self):
        """Ensure that unsupported requirement lines are skipped"""
        response = self.c.post('/projects/add/', {
            'slug': 'test', 'name': 'test',
            'requirements': ContentFile(BROKEN_REQUIREMENTS, name='req.txt')})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                         'http://testserver/project/test/')
        p = Project.objects.get(slug='test')
        # although the requirements are somewhat borked we import what we can
        self.assertEqual(p.dependencies.count(), 2)

    def test_update_project(self):
        """Test project changes work"""
        response = self.c.post('/projects/add/', {
            'slug': 'test', 'name': 'test',
            'requirements': ContentFile('Django==1.4.1', name='req.txt')})
        p = Project.objects.get(slug='test')
        dep = ProjectDependency.objects.get(project=p)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                         'http://testserver/project/test/')
        data = {
            'projectmember_set-TOTAL_FORMS': u'1',
            'projectmember_set-INITIAL_FORMS': u'1',
            'projectmember_set-MAX_NUM_FORMS': u'',
            'projectmember_set-0-id': str(p.projectmember_set.all()[0].pk),
            'projectmember_set-0-state': u'0',
            'dependencies-TOTAL_FORMS': u'1',
            'dependencies-INITIAL_FORMS': u'1',
            'dependencies-MAX_NUM_FORMS': u'',
            'dependencies-0-id': str(dep.id),
            'dependencies-0-version': u'1.5.1',
        }
        response = self.c.post('/project/test/edit/', data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                         'http://testserver/project/test/edit/')

        # Assert that logentries are created
        log = Log.objects.get(type='project_dependency', action='update')
        self.assertEqual(log.data['old_version'], '1.4.1')
        self.assertEqual(log.data['version'], '1.5.1')

        data['dependencies-0-DELETE'] = '1'
        response = self.c.post('/project/test/edit/', data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                         'http://testserver/project/test/edit/')

        # Assert that logentries are created
        log = Log.objects.get(type='project_dependency', action='remove')

    def test_jabber_field(self):
        """Make sure reg ex validation doesn't kick in for blank data"""
        f = JabberField(required=False)
        self.assertEqual(f.clean(''), '')


class TestProjectModel(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='test', slug='test')
        self.user = User.objects.create_user('test', 'test@example.com',
                                             'test')

    def test_create_logentry_basic(self):
        self.project.create_logentry('project', 'some_testing', self.user)
        log = Log.objects.get(project=self.project, action='some_testing')
        self.assertEqual(log.project, self.project)
        self.assertEqual(log.type, 'project')
        self.assertEqual(log.package, None)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.template,
            'folivora/notifications/project.some_testing.html')

    def test_create_logentry_with_data(self):
        self.project.create_logentry(action='shoutout', user=self.user,
                                     type='log', message='Hey everybody!')
        log = Log.objects.get(project=self.project, action='shoutout')
        self.assertEqual(log.project, self.project)
        self.assertEqual(log.type, 'log')
        self.assertEqual(log.package, None)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.data['message'], 'Hey everybody!')

    def test_members(self):
        self.assertEqual(self.project.members.count(), 0)
        ProjectMember.objects.create(user=self.user, project=self.project,
                                     state=ProjectMember.MEMBER)
        self.assertEqual(self.project.members.count(), 1)
        self.assertEqual(self.project.owners.count(), 0)
        owner = User.objects.create_user('owner', 'owner@example.com', 'pwd')
        ProjectMember.objects.create(user=owner, project=self.project,
                                     state=ProjectMember.OWNER)
        self.assertEqual(self.project.members.count(), 2)
        self.assertEqual(self.project.owners.count(), 1)


class TestProjectViews(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin', 'admin@example.com',
                                              'pwd')
        self.user = User.objects.create_user('apollo13', 'mail@example.com',
                                             'pwd')
        self.project = Project.objects.create(name='test', slug='test')
        ProjectMember.objects.create(user=self.admin, project=self.project,
                                     state=ProjectMember.OWNER)
        self.c = Client()
        self.c.login(username='admin', password='pwd')
        Package.create_with_provider_url('Django')
        Package.create_with_provider_url('test')
        self.new_package = Package.create_with_provider_url('new')

    def test_dashboard(self):
        response = self.c.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['log_entries'])
        self.c.post('/projects/add/',
                   {'name': 'new_project',
                    'slug': 'new_project'})
        response = self.c.get('/dashboard/')
        self.assertEqual(len(response.context['log_entries']), 1)

    def test_project_list(self):
        response = self.c.get('/projects/')
        self.assertEqual(response.status_code, 200)

    def test_view_project(self):
        response = self.c.get('/project/test/')
        self.assertEqual(response.status_code, 200)

    def test_edit_project(self):
        response = self.c.get('/project/test/edit/')
        self.assertEqual(response.status_code, 200)

    def test_delete_project(self):
        project = Project.objects.create(name='trash', slug='trash')
        response = self.c.get('/project/trash/delete/')
        self.assertEqual(response.status_code, 403)

        project_member = ProjectMember.objects.create(
            user=self.admin, project=project, state=ProjectMember.MEMBER)
        response = self.c.get('/project/trash/delete/')
        self.assertEqual(response.status_code, 403)

        project_member.state = ProjectMember.OWNER
        project_member.save()
        response = self.c.get('/project/trash/delete/')
        self.assertEqual(response.status_code, 200)

        self.assertTrue(Project.objects.filter(slug='trash').exists())
        response = self.c.post('/project/trash/delete/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Project.objects.filter(slug='trash').exists())

    def test_app_project_member(self):
        response = self.c.post('/project/test/add_member/',
                               {'user': self.user.id,
                                'state': ProjectMember.MEMBER})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'],
                         'http://testserver/project/test/edit/')

    def test_resign_project(self):
        self.c.login(username='apollo13', password='pwd')
        ProjectMember.objects.create(user=self.user, project=self.project,
                                     state=ProjectMember.MEMBER)
        response = self.c.get('/project/test/resign/')
        self.assertEqual(response.status_code, 200)
        response = self.c.post('/project/test/resign/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'http://testserver/projects/')
        self.assertFalse(ProjectMember.objects.filter(project=self.project,
                                                      user=self.user).exists())
        response = self.c.post('/project/test/resign/')
        self.assertEqual(response.status_code, 403)

    def test_update_dependency(self):
        response = self.c.get('/project/test/deps/')
        self.assertEqual(response.context['form'].initial['packages'], '')
        response = self.c.post('/project/test/deps/',
                               {'packages': 'Django==1\ntest==2'})
        self.assertEqual(response.status_code, 302)
        response = self.c.get('/project/test/deps/')
        self.assertEqual(response.context['form'].initial['packages'],
                         'Django==1\ntest==2')
        response = self.c.post('/project/test/deps/',
                               {'packages': 'Django==2\ntest==2\nnew==3'})
        self.assertTrue(ProjectDependency.objects.filter(
            project=self.project, package=self.new_package).exists())
        response = self.c.post('/project/test/deps/',
                               {'packages': 'Django==2\nunknown==3'})
        self.assertEqual(response.status_code, 200)
        response = self.c.post('/project/test/deps/',
                               {'packages': 'FAIL'})
        self.assertEqual(response.status_code, 200)


class TestUserProfileView(TestCase):
    def setUp(self):
        User.objects.create_user('apollo13', 'mail@example.com', 'pwd')
        self.c = Client()
        self.c.login(username='apollo13', password='pwd')

    def test_update_profile(self):
        response = self.c.get('/accounts/profile/')
        self.assertEqual(response.status_code, 200)
        response = self.c.post('/accounts/profile/', {
            'jabber': 'jabber@example.com',
            'language': 'de',
            'timezone': 'Europe/Berlin',
            'email': 'mail@example.com'})
        self.assertEqual(response.status_code, 302)
        response = self.c.post('/accounts/profile/', {
            'jabber': 'wrong',
            'language': 'de',
            'timezone': 'Europe/Berlin',
            'email': 'mail@example.com'})
        self.assertEqual(response.status_code, 200)

    def test_set_user_lang(self):
        self.c = Client()
        user = User.objects.get(username='apollo13')
        profile = user.get_profile()
        profile.language = 'at'
        profile.timezone = 'Europe/Vienna'
        profile.save()
        self.c.login(username='apollo13', password='pwd')
        self.assertEqual(self.c.session['django_language'], 'at')
        self.assertEqual(self.c.session['django_timezone'], 'Europe/Vienna')
        profile.delete()
        # Even without a profile login shouldn't throw errors.
        self.c.login(username='apollo13', password='pwd')


class TestUtils(TestCase):

    def test_jid_verification(self):
        self.assertTrue(is_valid_jid('apollo13@example.com'))
        self.assertTrue(is_valid_jid('apollo13@example.com/res'))
        self.assertFalse(is_valid_jid('example.com'))

    def test_parse_requirements(self):
        packages, missing = parse_requirements(
            ContentFile(VALID_REQUIREMENTS).readlines())
        self.assertEqual(packages, {'Sphinx': '1.10', 'Django': '1.4.1'})
        self.assertFalse(missing)
        packages, missing = parse_requirements(
            ContentFile(BROKEN_REQUIREMENTS))
        self.assertEqual(packages, {'Sphinx': '1.10', 'Django': '1.4.1'})
        self.assertEqual(missing, ['_--.>=asdhasjk ,,, [borked]\n'])
        packages, missing = parse_requirements(ContentFile('Django'))
        self.assertEqual(missing, ['Django'])

    def test_sort_mixin(self):
        p1 = Project.objects.create(name='test', slug='test')
        p2 = Project.objects.create(name='apo', slug='zzz')

        class Base(object):
            class request():
                GET = {}

            def get_context_data(self):
                return {}

            def get_queryset(self):
                return Project.objects.all()

        class TestClass(SortListMixin, Base):
            sort_fields = ['name', 'slug']

        t = TestClass()
        t.request.GET['sort'] = '-slug'

        qs = t.get_queryset()
        self.assertEqual(qs[0].pk, p2.pk)
        self.assertEqual(t.get_context_data(), {
            'sort_field': 'slug', 'sort_fields': ['name', 'slug'],
            'sort_order': 'desc'
        })

        t.request.GET['sort'] = 'blabla'
        qs = t.get_queryset()
        self.assertEqual(qs[0].pk, p1.pk)
