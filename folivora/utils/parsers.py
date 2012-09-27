#-*- coding: utf-8 -*-
import pkg_resources
import re
from django.utils.translation import ugettext_lazy


class BaseParser(object):
    name = None
    title = None

    def parse(self, lines):
        raise NotImplementedError


def get_parser(name):
    for parser in PARSERS:
        if parser.name == name:
            return parser()
    raise ValueError('Parser %s does not exist' % name)


def get_parser_choices():
    return [(parser.name, parser.title) for parser in PARSERS]


class PipRequirementsParser(BaseParser):
    name = 'pip_requirements'
    title = ugettext_lazy('Pip Requirements')

    def parse(self, lines):
        missing = []
        packages = {}
        for line in lines:
            try:
                req = pkg_resources.parse_requirements(line.strip()).next()
            except ValueError:
                missing.append(line)
                continue
            except StopIteration:
                continue

            specs = [s for s in req.specs if s[0] == '==']
            if specs:
                packages[req.project_name] = specs[0][1]
            else:
                missing.append(req.project_name)

        return packages, missing


class BuildoutVersionsParser(BaseParser):
    name = 'buildout_versions'
    title = ugettext_lazy('Buildout Versions')

    # Ref: https://github.com/buildout/buildout/blob/master/src/zc/buildout/configparser.py
    RE_SECTION = re.compile(
        r'\['                                 # [
        r'(?P<header>[^]]+)'                  # very permissive!
        r'\]'                                 # ]
    )
    RE_OPTION = re.compile(
        r'(?P<option>[^:=\s][^:=]*)'          # very permissive!
        r'\s*(?P<vi>[:=])\s*'                 # any number of space/tab,
        # followed by separator
        # (either : or =), followed
        # by any # space/tab
        r'(?P<value>.*)$'                     # everything up to eol
    )

    def __init__(self, *args, **kwargs):
        super(BuildoutVersionsParser, self).__init__(*args, **kwargs)
        self._sections = {}
        self._cur_sect = None

    def _is_ignorable(self, line):
        # whitespace & comments are ignorable
        return ((line.strip() == '' or line[0] in '#;') or
                (line.split(None, 1)[0].lower() == 'rem' and line[0] in "rR"))

    def _handle_line(self, line):
        if self._is_ignorable(line):
            return
        # is it a section header?
        match = self.RE_SECTION.match(line)
        if match:
            header = match.group('header')
            if header in self._sections:
                self._cur_sect = self._sections[header]
            else:
                self._cur_sect = {}
                self._sections[header] = self._cur_sect
        # is it an option line?
        if self._cur_sect is not None:
            match = self.RE_OPTION.match(line)
            if match:
                option, vi, value = match.group('option', 'vi', 'value')
                if value is not None:
                    if ';' in value:
                        # ';' is a comment delimiter only if it follows
                        # a spacing character
                        pos = value.find(';')
                        if pos != -1 and value[pos-1].isspace():
                            value = value[:pos]
                    value = value.strip()
                # allow empty values
                if value == '""':
                    value = ''
                option = option.rstrip()
                self._cur_sect[option] = value

    def parse(self, lines):
        for line in lines:
            self._handle_line(line)
        self._cur_sect = None
        buildout = self._sections.get('buildout', {})
        versions_section = buildout.get('versions', 'versions')
        versions = self._sections.get(versions_section, {})
        packages = {}
        missing = []
        for package, version in versions.items():
            if version and version[0] != '=':
                packages[package] = version
            else:
                missing.append(package)
        return packages, missing


PARSERS = [PipRequirementsParser, BuildoutVersionsParser]
