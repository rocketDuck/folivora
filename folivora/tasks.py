#-*- coding: utf-8 -*-
"""
    folivora.tasks
    ~~~~~~~~~~~~~~

    Celery tasks that execute syncronization
    with PyPi and other stuff.
"""
import time
import datetime
import pytz
from celery import task
from django.utils import timezone
from distutils.version import LooseVersion

from .models import (SyncState, Package, PackageVersion,
    ProjectDependency, Log, Project)
from .utils.pypi import CheeseShop
from .utils.notifications import route_notifications


def log_affected_projects(pkg, **kwargs):
    affected_projects = Project.objects.filter(dependencies__package=pkg) \
                                       .values_list('id', flat=True)

    log_entries = []
    for project in affected_projects:
        # Add log entry for new package release
        log = Log(project_id=project, **kwargs)
        log_entries.append(log)
    Log.objects.bulk_create(log_entries)


#TODO: send notifications
@task
def sync_with_changelog():
    """Syncronize with pypi changelog.

    Right now we only listen for `new-release`, `remove`, `rename`,
    and `create` as we do not store any metadata information.

    Following actions can be issued according to pypi source code:
        new release			- Creates a new Release
        remove				- Removes a Package from the Shop
        rename from %(old)s		- Rename a package
        add %(pyversion)s %(filename)s  - Add a new file to a version
        remove file %(filename)s        - Remove a file
        docupdate                       - Notify for documentation update
        create				- Create a new package
        update %(type)s                 - Update some detailed classifiers
    """
    next_last_sync = timezone.now()

    state, created = SyncState.objects.get_or_create(
        type=SyncState.CHANGELOG,
        defaults={'last_sync': timezone.now()})

    epoch = int(time.mktime(state.last_sync.timetuple()))

    client = CheeseShop()
    log = client.get_changelog(epoch, True)

    for package, version, stamp, action in log:
        if action == 'new release':
            try:
                pkg = Package.objects.get(name=package)
            except Package.DoesNotExist:
                pkg = Package.create_with_provider_url(package)

            dt = datetime.datetime.fromtimestamp(stamp)
            release_date = timezone.make_aware(dt, pytz.UTC)
            if not PackageVersion.objects.filter(version=version).exists():
                update = PackageVersion(version=version,
                                        release_date=release_date)
                pkg.versions.add(update)
                ProjectDependency.objects.filter(package=pkg) \
                                         .update(update=update)

            log_affected_projects(pkg,
                                  action='new_release',
                                  type='package',
                                  data={'version': version})
        elif action == 'remove':
            # We only clear versions and set the recent updated version
            # on every project dependency to NULL. This way we can ensure
            # stability on ProjectDependency.
            pkg = Package.objects.get(name=package)
            if version is None:
                pkg.versions.delete()
            ProjectDependency.objects.filter(package=pkg) \
                                     .update(update=None)
            log_affected_projects(pkg, action='remove_package',
                                  type='package',
                                  data={'package': package})

        elif action == 'create':
            if not Package.objects.filter(name=package).exists():
                Package.objects.create_with_provider(package)

    SyncState.objects.filter(type=SyncState.CHANGELOG) \
                     .update(last_sync=next_last_sync)


@task
def sync_project(project_pk):
    project = Project.objects.get(pk=project_pk)

    log_entries = []
    for dependency in project.dependencies.all():
        package = dependency.package
        package.sync_versions()
        versions = list(package.versions.values_list('version', flat=True))

        if versions:
            # We use LooseVersion since at least pytz fails with StrictVersion
            # TODO: tests
            versions.sort(key=LooseVersion)

            if LooseVersion(dependency.version) >= LooseVersion(versions[-1]):
                ProjectDependency.objects.filter(pk=dependency.pk) \
                                         .update(update=None)
                continue  # The dependency is up2date, nothing to do

            pv = PackageVersion.objects.get(package=package,
                                            version=versions[-1])

            if pv.pk == dependency.update_id:
                continue

            dependency.update = pv
            dependency.save()
            tz = timezone.utc
            since = str(timezone.make_naive(pv.release_date, tz))
            log_entries.append(Log(type='project_dependency',
                                   action='update_available',
                                   project=project, package=package,
                                   data={'version': versions[-1],
                                         'since': since}))
    if log_entries:
        Log.objects.bulk_create(log_entries)
        route_notifications(*log_entries)
