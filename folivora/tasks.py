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
from django.utils.timezone import make_naive, make_aware
from folivora.models import SyncState, Package, PackageVersion, \
    ProjectDependency
from folivora.utils.pypi import CheeseShop, DEFAULT_SERVER


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
        defaults={'last_sync': make_aware(datetime.datetime.utcnow(), pytz.UTC)})

    epoch = int(time.mktime(state.last_sync.timetuple()))

    client = CheeseShop()
    log = client.get_changelog(epoch, True)

    for package, version, stamp, action in log:
        if action == 'new release':
            print package, version, stamp, action
            try:
                pkg = Package.objects.get(name=package)
            except Package.DoesNotExist:
                pkg = Package.create_with_provider_url(package)

            print pkg
            release_date = make_aware(datetime.datetime.fromtimestamp(stamp),
                                      pytz.UTC)
            print release_date
            if PackageVersion.objects.filter(version=version).exists():
                print "version %s already exists!" % version
            else:
                print "update %s with version %s" % (package, version)
                update = PackageVersion(version=version, release_date=release_date)
                pkg.versions.add(update)
                ProjectDependency.objects.filter(package=pkg).update(update=update)
