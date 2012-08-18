import pytz

from django import forms
from django.utils.translation import ugettext_lazy

from .models import Project, UserProfile
from .utils.forms import ModelForm, JabberField

TIMEZONES = pytz.common_timezones


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
