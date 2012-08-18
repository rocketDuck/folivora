import pytz

from django import forms
from django.utils.translation import ugettext_lazy

from .models import (Project, UserProfile, Package, ProjectDependency,
    ProjectMember)
from .utils.forms import ModelForm, JabberField
from .utils.jabber import is_valid_jid

import floppyforms as forms

import pkg_resources


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
        requirements = pkg_resources.parse_requirements(data.readlines())
        missing = []
        packages = {}
        for req in requirements:
            specs = [s for s in req.specs if s[0] == '==']
            if specs:
                packages[req.project_name] = specs[0][1]
            else:
                missing.append(req.project_name)

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
    jabber = JabberField()
    class Meta:
        model = UserProfile
        exclude = ('user',)


class ProjectMemberForm(ModelForm):
    class Meta:
        model = ProjectMember
        fields = ('id', 'state')
