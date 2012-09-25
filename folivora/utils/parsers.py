#-*- coding: utf-8 -*-
import pkg_resources
from django.utils.translation import ugettext_lazy


class BaseParser(object):
    name = None
    title = None


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


PARSERS = [PipRequirementsParser]
