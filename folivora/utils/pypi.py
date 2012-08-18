#-*- coding: utf-8 -*-
"""
    folivora.utils.pypi
    ~~~~~~~~~~~~~~~~~~~

    Utilities to access pypi compatible servers.
"""
import time
import xmlrpclib


def get_seconds(hours):
    """Get number of seconds since epoch from now minus `hours`"""
    return int(time.gmtime() - (60 * 60) * hours)


DEFAULT_SERVER = 'http://pypi.python.org/pypi/'


class CheeseShop(object):

    def __init__(self, server=DEFAULT_SERVER):
        self.xmlrpc = xmlrpclib.Server(server)

    def get_package_versions(self, package_name):
        """Fetch list of available versions for a package.

        :param package_name: Name of the package to query.
        """
        return self.xmlrpc.package_releases(package_name)

    def get_package_list(self):
        """Fetch the master list of package names."""
        return self.xmlrpc.list_packages()

    def search(self, spec, operator):
        """Query using search spec."""
        return self.xmlrpc.search(spec, operator.lower())

    def get_changelog(self, hours):
        """Query the changelog.

        :param hours: Hours from now to specify the changelog size.
        """
        return self.xmlrpc.changelog(get_seconds(hours))

    def get_updated_releases(self, hours):
        """Query all updated releases within `hours`.

        :param hours: Specify the number of hours to find updated releases.
        """
        return self.xmlrpc.updated_releases(get_seconds(hours))

    def get_release_urls(self, package_name, version):
        """Query for all available release urls of `package_name`.

        :param package_name: Name of the package.
        :param version: Version of the package.
        """
        return self.xmlrpc.release_urls(package_name, version)

    def get_release_data(self, package_name, version=None):
        """Query for specific release data.

        :param package_name: Name of the package.
        :param version: Version to query the data. If `None`, it's latest
                        version will be used.
        """
        if version is None:
            versions = self.get_package_versions(package_name)
            if not versions:
                return {}
            version = versions[-1]
        return self.xmlrpc.release_data(package_name, version)
