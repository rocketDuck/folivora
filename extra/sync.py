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

    for name in package_names:
        print 'Query and store history of %s' % name
        url = SERVER.get_release_data(name).get('package_url',
                                                urlparse.urljoin(DEFAULT_SERVER, name))
        pkg, created = Package.objects.get_or_create(name=name, url=url, provider='pypi')

        for version in SERVER.get_package_versions(name):
            urls = SERVER.get_release_urls(name, version)
            # It can happen that there are no releases, we simply
            # ignore these versions yet.
            if urls:
                url = urls[0]
            else:
                continue
            release_date = make_aware(
                datetime.datetime.fromtimestamp(
                    time.mktime(url['upload_time'].timetuple())),
                pytz.UTC)
            PackageVersion.objects.get_or_create(
                package=pkg, version=version, release_date=release_date)


if __name__ == '__main__':
    sync()
