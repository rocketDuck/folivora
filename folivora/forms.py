from itertools import izip

import pytz

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy, gettext as _

from .models import (Project, UserProfile, Package, ProjectDependency,
    ProjectMember)
from .utils.forms import ModelForm, JabberField
from .utils import parse_requirements

import floppyforms as forms


TIMEZONES = pytz.common_timezones


class AddProjectForm(ModelForm):
    requirements = forms.FileField(ugettext_lazy('requirements.txt'))

    class Meta:
        model = Project
        fields = ('name', 'slug')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(AddProjectForm, self).__init__(*args, **kwargs)

    def clean_requirements(self):
        data = self.cleaned_data['requirements']

        packages, missing = parse_requirements(data)

        known_packages = Package.objects.filter(name__in=packages.keys())\
            .values_list('name', 'pk')
        known_package_names = map(lambda x: x[0], known_packages)

        # TODO: report missing back to the ui.
        missing.extend(set(packages.keys()).difference(set(known_package_names)))

        project_deps = []

        for name, pk in known_packages:
            project_deps.append(ProjectDependency(package_id=pk, version=packages[name]))

        return project_deps

    def save(self, commit=True):
        assert commit == True
        project = super(AddProjectForm, self).save(True)
        project.create_logentry('add', self.user, name=project.name)
        ProjectMember.objects.create(user=self.user, state=ProjectMember.OWNER,
            project=project)
        deps = self.cleaned_data['requirements']
        for dep in deps:
            dep.project = project
        ProjectDependency.objects.bulk_create(deps)

        return project


class ProjectDependencyForm(ModelForm):
    class Meta:
        model = ProjectDependency
        fields = ('version', 'id')


class UpdateUserProfileForm(ModelForm):
    timezone = forms.ChoiceField(label=ugettext_lazy('Timezone'), required=True,
                                 choices=zip(TIMEZONES, TIMEZONES))
    jabber = JabberField(required=False)
    class Meta:
        model = UserProfile
        exclude = ('user',)


class ProjectMemberForm(ModelForm):
    class Meta:
        model = ProjectMember
        fields = ('id', 'state')


class CreateProjectMemberForm(ModelForm):
    class Meta:
        model = ProjectMember
        fields = ('user', )
