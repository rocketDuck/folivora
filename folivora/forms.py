import pytz

from django import forms
from django.utils.translation import ugettext as _, ugettext_lazy

from .models import Project, UserProfile
from .utils.forms import ModelForm
from .utils.jabber import may_be_valid_jabber

TIMEZONES = pytz.common_timezones


class JabberField(forms.fields.CharField):
    def clean(self, value):
        if not value:
            return
        value = value.strip()
        if not may_be_valid_jabber(value):
            raise forms.ValidationError(_(u'The entered Jabber address is invalid. '
                u'Please check your input.'))
        return value


class AddProjectForm(ModelForm):
    class Meta:
        model = Project
        exclude = ('members',)


class UpdateUserProfileForm(ModelForm):
    timezone = forms.ChoiceField(label=ugettext_lazy('Timezone'), required=True,
                                 choices=zip(TIMEZONES, TIMEZONES))
    jabber = JabberField()
    class Meta:
        model = UserProfile
        exclude = ('user',)
