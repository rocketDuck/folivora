# -*- coding: utf-8 -*-
import copy
import json

from django.core.urlresolvers import reverse_lazy, reverse
from django.forms.models import inlineformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import (CreateView, UpdateView, DeleteView,
    FormView, FormMixin)
from django.views.generic.list import ListView

from django.contrib import messages

from braces.views import LoginRequiredMixin, UserFormKwargsMixin

from .forms import (AddProjectForm, UpdateUserProfileForm,
    ProjectDependencyForm, ProjectMemberForm, CreateProjectMemberForm,
    CreateProjectDependencyForm)
from .models import (Project, UserProfile, ProjectDependency, ProjectMember,
    Log, Package)
from .utils import parse_requirements
from .utils.views import SortListMixin, ProjectMixin


folivora_index = TemplateView.as_view(template_name='folivora/index.html')
folivora_dashboard = TemplateView.as_view(template_name='folivora/dashboard.html')

class ListProjectView(LoginRequiredMixin, SortListMixin, ListView):
    model = Project
    context_object_name = 'projects'
    sort_fields = ['name']
    default_order = ('name',)

    def get_queryset(self):
        qs = super(ListProjectView, self).get_queryset()
        return qs.filter(members=self.request.user)


project_list = ListProjectView.as_view()


class AddProjectView(LoginRequiredMixin, UserFormKwargsMixin, CreateView):
    model = Project
    form_class = AddProjectForm
    template_name_suffix = '_add'


project_add = AddProjectView.as_view()


class UpdateProjectView(ProjectMixin, TemplateView):
    model = Project
    template_name = 'folivora/project_update.html'

    dep_qs = ProjectDependency.objects.select_related('package').order_by('package__name')
    dep_form_class = inlineformset_factory(Project, ProjectDependency, extra=0,
        form=ProjectDependencyForm)

    member_qs = ProjectMember.objects.select_related('user').order_by('user__username')
    member_form_class = inlineformset_factory(Project, ProjectMember, extra=0,
        form=ProjectMemberForm)

    allow_only_owner = True

    def get_context_data(self, **kwargs):
        context = super(UpdateProjectView, self).get_context_data(**kwargs)
        data = self.request.POST if self.request.method == 'POST' else None
        dep_form = self.dep_form_class(data, queryset=self.dep_qs,
                                       instance=self.project)
        member_form = self.member_form_class(data, instance=self.project,
                                             queryset=self.member_qs)
        context.update({
            'dep_form': dep_form,
            'member_form': member_form,
        })
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        ctx = self.get_context_data(**kwargs)
        dep_form = ctx['dep_form']
        member_form = ctx['member_form']
        original_data = ProjectDependency.objects.in_bulk(
            dep_form.get_queryset())
        if all([dep_form.is_valid(), member_form.is_valid()]):
            member_form.save()
            dep_form.save()
            ProjectDependency.process_formset(dep_form,
                original_data, self.request.user)
            messages.success(request, _(u'Updated Project “{name}” '
                'successfully.').format(name=dep_form.instance.name))
            return HttpResponseRedirect(reverse('folivora_project_update',
                                    kwargs={'slug': dep_form.instance.slug}))
        return self.render_to_response(ctx)


project_update = UpdateProjectView.as_view()


class DeleteProjectView(ProjectMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('folivora_project_list')
    allow_only_owner = True

    def delete(self, *args, **kwargs):
        if self.project:
            messages.success(self.request, _(u'Deleted project “{name}” '
                'successfully.').format(name=self.project.name))
        return super(DeleteView, self).delete(*args, **kwargs)


project_delete = DeleteProjectView.as_view()


class DetailProjectView(ProjectMixin, DetailView):
    model = Project

    def get_context_data(self, **kwargs):
        context = super(DetailProjectView, self).get_context_data(**kwargs)
        context.update({
            'log_entries': Log.objects.filter(project=self.project)
                                      .order_by('-when')
                                      .select_related('user', 'package'),
            'updates': ProjectDependency.objects.filter(project=self.project)
                                                .filter(update__isnull=False)
                                                .count(),
            'deps': self.project.dependencies.select_related('package')
                                        .order_by('package__name')
        })
        return context


project_detail = DetailProjectView.as_view()


class CreateProjectMemberView(ProjectMixin, CreateView):
    model = ProjectMember
    form_class = CreateProjectMemberForm
    allow_only_owner = True
    template_name = 'folivora/project_member_add.html'

    def get_success_url(self):
        return reverse('folivora_project_update', args=[self.kwargs['slug']])

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.project = self.project
        user = self.object.user
        if (ProjectMember.objects.filter(project=self.project)
                         .filter(user=user).exists()):
            pass
            # TODO: do not validate the form
        else:
            self.object.save()
        return FormMixin.form_valid(self, form)


project_add_member = CreateProjectMemberView.as_view()


class UpdateProjectDependencyView(ProjectMixin, FormView):
    form_class = CreateProjectDependencyForm
    allow_only_owner = True
    template_name = 'folivora/project_dependency_update.html'

    def get_success_url(self):
        return reverse('folivora_project_update', args=[self.kwargs['slug']])

    def get_initial(self):
        return {'packages': self.project.requirements}

    def form_valid(self, form):
        new_requirements = form.cleaned_data['packages']
        old_requirements = self.project.requirement_dict
        new = set(new_requirements.keys())
        old = set(old_requirements.keys())

        ids = dict(Package.objects.filter(name__in=old.union(new)) \
                                  .values_list('name', 'id'))

        add = [(ids[n], new_requirements[n]) for n in new.difference(old) if n in ids]
        new_objects = [ProjectDependency(project=self.project,
                                         package_id=x[0], version=x[1])
                       for x in add]
        ProjectDependency.objects.bulk_create(new_objects)
        remove = [(ids[n], old_requirements[n]) for n in old.difference(new) if n in ids]

        change = []
        for package in new.intersection(old):
            if not package in ids:
                continue
            if old_requirements[package] == new_requirements[package]:
                continue
            change.append((ids[package], old_requirements[package],
                           new_requirements[package]))
            ProjectDependency.objects.filter(package_id=ids[package],
                                             project=self.project) \
                                     .update(version=new_requirements[package])

        ProjectDependency.objects.filter(project=self.project,
            package_id__in=[x[0] for x in remove]).delete()
        self.project.process_changes(self.request.user, remove, change, add)
        return super(UpdateProjectDependencyView, self).form_valid(form)


project_update_dependency = UpdateProjectDependencyView.as_view()


class ResignProjectView(ProjectMixin, DeleteView):
    success_url = reverse_lazy('folivora_project_list')

    def get_object(self, queryset=None):
        user = self.request.user
        return ProjectMember.objects.get(project=self.project, user=user)


project_resign = ResignProjectView.as_view()


class UpdateUserProfileView(LoginRequiredMixin, UpdateView):
    form_class = UpdateUserProfileForm

    def form_valid(self, form):
        lang = form.cleaned_data['language']
        if lang:
            self.request.session['django_language'] = lang
        timezone = form.cleaned_data['timezone']
        if timezone:
            self.request.session['django_timezone'] = timezone
        response = super(UpdateUserProfileView, self).form_valid(form)
        self.object.user.email = form.cleaned_data['email']
        self.object.user.save()
        return response

    def get_object(self, queryset=None):
        return UserProfile.objects.get_or_create(user=self.request.user)[0]


profile_edit = UpdateUserProfileView.as_view()
