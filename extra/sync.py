#-*- coding: utf-8 -*-
import urlparse
import datetime
import logging
import time
import pytz
from django.utils.timezone import make_aware
from folivora.models import Package, PackageVersion
from folivora.utils.pypi import CheeseShop, DEFAULT_SERVER

SERVER = CheeseShop(DEFAULT_SERVER)


def sync():
    print 'Query package list'
    package_names = SERVER.get_package_list()

    packages = []
    for name in package_names:
        print "Query and store %s" % name
        url = urlparse.urljoin(DEFAULT_SERVER, name)
        packages.append(Package(name=name, url=url, provider='pypi'))
    print "sync all packages to disk..."
    Package.objects.bulk_create(packages)


if __name__ == '__main__':
    sync()
