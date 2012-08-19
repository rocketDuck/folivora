#!/usr/bin/env python
#-*- coding: utf-8 -*-
import sys
import urlparse
import datetime
import logging
import time
import pytz
from django.utils import timezone
from folivora.models import Package, SyncState
from folivora.utils.pypi import CheeseShop, DEFAULT_SERVER


SERVER = CheeseShop(DEFAULT_SERVER)


def sync():
    if ('delete_all' in sys.argv and
        raw_input('sure (this resets everything)? [y/n]: ') == 'y'):
            Package.objects.all().delete()

    SyncState.objects.all().delete()
    SyncState.objects.create(type=SyncState.CHANGELOG,
        last_sync=timezone.now())

    print 'Query package list'
    package_names = SERVER.get_package_list()

    packages = []
    for name in package_names:
        url = urlparse.urljoin(DEFAULT_SERVER, name)
        packages.append(Package(name=name, url=url, provider='pypi'))
    print 'Sync all packages to db...'
    Package.objects.bulk_create(packages)


if __name__ == '__main__':
    sync()
