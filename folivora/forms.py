import pytz

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy, ugettext as _

from .models import (Project, UserProfile, Package, ProjectDependency,
    ProjectMember)
from .utils.forms import ModelForm, JabberField
from .utils.parsers import get_parser, get_parser_choices
from .utils.pypi import normalize_name
from .tasks import sync_project

import floppyforms as forms


TIMEZONES = pytz.common_timezones


class AddProjectForm(ModelForm):
    requirements = forms.FileField(required=False)
    parser = forms.ChoiceField(choices=get_parser_choices())

    class Meta:
        model = Project
        fields = ('name', 'slug')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(AddProjectForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = self.cleaned_data
        data = cleaned_data.get('requirements', None)
        project_deps = []
        if data and 'parser' in cleaned_data:
            parser = get_parser(cleaned_data['parser'])
            packages, missing = parser.parse(data)
            packages = dict((normalize_name(k), v) for k, v in packages.iteritems())

            pkg_names = [normalize_name(name) for name in packages.keys()]

            known_packages = Package.objects.filter(normalized_name__in=pkg_names)\
                .values_list('normalized_name', 'name', 'pk')
            known_package_names = map(lambda x: x[1], known_packages)

            # TODO: report missing back to the ui.
            normalized = (normalize_name(n) for n in known_package_names)
            missing.extend(set(pkg_names).difference(normalized))

            for normalized, name, pk in known_packages:
                project_deps.append(ProjectDependency(package_id=pk,
                                                      version=packages[normalized]))
        cleaned_data['requirements'] = project_deps
        return cleaned_data

    def save(self, commit=True):
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
    timezone = forms.ChoiceField(label=ugettext_lazy('Timezone'),
                                 required=True,
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
        fields = ('user', 'state')


class UpdateProjectDependencyForm(forms.Form):
    packages = forms.CharField(widget=forms.Textarea, required=False)
    parser = forms.ChoiceField(choices=get_parser_choices())

    def clean(self):
        cleaned_data = self.cleaned_data
        if 'packages' in cleaned_data and 'parser' in cleaned_data:
            data = cleaned_data['packages']
            parser = get_parser(cleaned_data['parser'])
            packages, missing_packages = parser.parse(data.splitlines())
            pkg_names = [normalize_name(name) for name in packages.keys()]
            known_packages = set(Package.objects.filter(normalized_name__in=pkg_names)
                                       .values_list('normalized_name', 'name'))
            pkg_mapping = dict(known_packages)

            # Show real package names instead of normalized version.
            unknown_packages = set(pkg_mapping[n] for n in
                set(pkg_names).difference(x[0] for x in known_packages))

            if unknown_packages:
                raise ValidationError(_(
                    'Could not find the following dependencies: %s') %
                    ', '.join(unknown_packages))
            if missing_packages:
                raise ValidationError(_(
                    'Could not parse the following dependencies: %s') %
                    ', '.join(missing_packages))
            cleaned_data['packages'] = packages
        return cleaned_data
