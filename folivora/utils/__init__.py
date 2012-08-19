#-*- coding: utf-8 -*-
import pkg_resources


def parse_requirements(lines):
    missing = []
    packages = {}
    for line in lines:
        try:
            req = pkg_resources.parse_requirements(line.strip()).next()
        except ValueError as e:
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
