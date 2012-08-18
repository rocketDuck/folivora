#-*- coding: utf-8 -*-
import pkg_resources


def get_model_type(model):
    app = model._meta.app_label
    module = model._meta.module_name
    return '{app_label}.{module_name}'.format(app_label=app, module_name=module)


def parse_requirements(data):
    missing = []
    packages = {}
    for line in data.readlines():
        try:
            req = pkg_resources.parse_requirements(line.strip()).next()
        except ValueError as e:
            missing.append(line)
            continue

        specs = [s for s in req.specs if s[0] == '==']
        if specs:
            packages[req.project_name] = specs[0][1]
        else:
            missing.append(req.project_name)

    return packages, missing
