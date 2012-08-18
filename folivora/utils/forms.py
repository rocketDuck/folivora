from django.db import models
from django.utils.translation import ugettext as _
from django.forms import ValidationError, fields
from django.forms.models import ModelFormMetaclass, ModelForm as BaseModelForm

from floppyforms import widgets, forms

from .jabber import is_valid_jid


widget_map = {
    models.CharField: widgets.TextInput,
    models.IntegerField: widgets.TextInput,
    models.TextField: widgets.Textarea,
    models.ForeignKey: widgets.Select,
    models.ManyToManyField: widgets.SelectMultiple
}


class FloppyFormsModelMetaclass(ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        if BaseModelForm not in bases and 'Meta' in attrs:
            meta = attrs['Meta']
            model = meta.model
            widgets = getattr(meta, 'widgets', None)
            if not widgets:
                widgets = meta.widgets = {}
            for field in model._meta.fields:
                if isinstance(field, models.AutoField):
                    continue
                if field.choices:
                    widgets[field.name] = widget_map[models.ForeignKey]
                elif type(field) in widget_map and field.name not in widgets:
                    widgets[field.name] = widget_map[type(field)]

        return super(FloppyFormsModelMetaclass, cls).__new__(cls, name,
            bases, attrs)


class ModelForm(forms.LayoutRenderer, BaseModelForm):
    __metaclass__ = FloppyFormsModelMetaclass


class JabberField(fields.CharField):
    def clean(self, value):
        if not value:
            return
        value = value.strip()
        if not is_valid_jid(value):
            raise ValidationError(_(u'The entered Jabber address is invalid. '
                u'Please check your input.'))
        return value
