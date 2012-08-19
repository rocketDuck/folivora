from itertools import izip

import pytz

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy, gettext as _

from .models import (Project, UserProfile, Package, ProjectDependency,
    ProjectMember)
from .utils.forms import ModelForm, JabberField
from .utils import parse_requirements
from .tasks import sync_project

import floppyforms as forms


TIMEZONES = pytz.common_timezones


class AddProjectForm(ModelForm):
    requirements = forms.FileField(required=False)

    class Meta:
        model = Project
        fields = ('name', 'slug')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(AddProjectForm, self).__init__(*args, **kwargs)

    def clean_requirements(self):
        data = self.cleaned_data['requirements']
        if data is None:
            return []

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
        project.create_logentry('project', 'add', self.user, name=project.name)
        ProjectMember.objects.create(user=self.user, state=ProjectMember.OWNER,
            project=project)
        deps = self.cleaned_data['requirements']
        for dep in deps:
            dep.project = project
        ProjectDependency.objects.bulk_create(deps)
        sync_project.delay(project.pk)
        return project


class ProjectDependencyForm(ModelForm):
    class Meta:
        model = ProjectDependency
        fields = ('version', 'id')


class UpdateUserProfileForm(ModelForm):
    timezone = forms.ChoiceField(label=ugettext_lazy('Timezone'), required=True,
                                 choices=zip(TIMEZONES, TIMEZONES))
    jabber = JabberField(required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = UserProfile
        fields = ('email', 'jabber', 'language', 'timezone')

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        if instance is not None:
            initial = kwargs.setdefault('initial', {})
            initial['email'] = instance.user.email

        super(UpdateUserProfileForm, self).__init__(*args, **kwargs)


class ProjectMemberForm(ModelForm):
    class Meta:
        model = ProjectMember
        fields = ('id', 'state')


class CreateProjectMemberForm(ModelForm):
    class Meta:
        model = ProjectMember
        fields = ('user', 'state' )


class UpdateProjectDependencyForm(forms.Form):
    packages = forms.CharField(widget=forms.Textarea, required=False)

    def clean_packages(self):
        data = self.cleaned_data['packages']
        packages, missing_packages = parse_requirements(
            data.splitlines())
        if missing_packages:
            raise ValidationError(_(
                'could not parse the following dependencies: %s') %
                ', '.join(missing_packages))
        return packages
