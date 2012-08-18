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

from .models import (SyncState, Package, PackageVersion,
    ProjectDependency, Log, Project)
from .utils import get_model_type
from .utils.pypi import CheeseShop


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

            release_date = timezone.make_aware(datetime.datetime.fromtimestamp(stamp),
                                               pytz.UTC)
            if not PackageVersion.objects.filter(version=version).exists():
                update = PackageVersion(version=version,
                                        release_date=release_date)
                pkg.versions.add(update)
                ProjectDependency.objects.filter(package=pkg) \
                                         .update(update=update)
            affected_projects = Project.objects.filter(dependencies__package=pkg) \
                                               .values_list('id', flat=True)
            log_entries = []
            for project in affected_projects:
                # Add log entry for new package release
                log = Log(project_id=project,
                          package=pkg,
                          action='new_release',
                          type=get_model_type(Package),
                          data={'version': version})
                log_entries.append(log)
            Log.objects.bulk_create(log_entries)
