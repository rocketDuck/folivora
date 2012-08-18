#-*- coding: utf-8 -*-

def get_model_type(model):
    app = model._meta.app_label
    module = model._meta.module_name
    return '{app_label}.{module_name}'.format(app_label=app, module_name=module)
