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
from .tasks import sync_project
from .utils.views import SortListMixin, MemberRequiredMixin


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


class UpdateProjectView(MemberRequiredMixin, TemplateView):
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
        object = Project.objects.get(slug=self.kwargs['slug'])
        dep_form = self.dep_form_class(data, queryset=self.dep_qs,
                                       instance=object)
        member_form = self.member_form_class(data, instance=object,
                                             queryset=self.member_qs)
        context.update({
            'dep_form': dep_form,
            'member_form': member_form,
            'project': object,
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
            ProjectDependency.process_changed_dependencies(dep_form,
                original_data, self.request.user)
            sync_project(dep_form.instance.pk)
            messages.success(request, _(u'Updated Project “{name}” '
                'successfully.').format(name=dep_form.instance.name))
            return HttpResponseRedirect(reverse('folivora_project_update',
                                    kwargs={'slug': dep_form.instance.slug}))
        return self.render_to_response(ctx)


project_update = UpdateProjectView.as_view()


class DeleteProjectView(MemberRequiredMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('folivora_project_list')
    allow_only_owner = True

    def delete(self, *args, **kwargs):
        object = self.get_object()
        if object:
            messages.success(self.request, _(u'Deleted project “{name}” '
                'successfully.').format(name=object.name))
        return super(DeleteView, self).delete(*args, **kwargs)


project_delete = DeleteProjectView.as_view()


class DetailProjectView(MemberRequiredMixin, DetailView):
    model = Project

    def get_context_data(self, **kwargs):
        context = super(DetailProjectView, self).get_context_data(**kwargs)
        project = context['object']
        context.update({
            'log_entries': Log.objects.filter(project=project) \
                                      .order_by('-when') \
                                      .select_related('user', 'package'),
            'updates': ProjectDependency.objects.filter(project=project) \
                                                .filter(update__isnull=False) \
                                                .count(),
            'deps': project.dependencies.select_related('package') \
                                        .order_by('package__name')
        })
        return context


project_detail = DetailProjectView.as_view()


class CreateProjectMemberView(MemberRequiredMixin, CreateView):
    model = ProjectMember
    form_class = CreateProjectMemberForm
    allow_only_owner = True
    template_name = 'folivora/project_member_add.html'

    def get_success_url(self):
        return reverse('folivora_project_update', args=[self.kwargs['slug']])

    def form_valid(self, form):
        project = Project.objects.get(slug=self.kwargs['slug'])
        self.object = form.save(commit=False)
        self.object.project = project
        user = self.object.user
        if (ProjectMember.objects.filter(project=project)
                         .filter(user=user).exists()):
            pass
            # TODO: do not validate the form
        else:
            self.object.save()
        return FormMixin.form_valid(self, form)


project_add_member = CreateProjectMemberView.as_view()


class UpdateProjectDependencyView(MemberRequiredMixin, FormView):
    form_class = CreateProjectDependencyForm
    allow_only_owner = True
    template_name = 'folivora/project_dependency_update.html'

    def get_success_url(self):
        return reverse('folivora_project_update', args=[self.kwargs['slug']])

    def get_object(self, queryset=None):
        return Project.objects.get(slug=self.kwargs['slug'])

    def get_initial(self):
        return {'packages': self.project.get_requirements()}

    def get(self, request, *args, **kwargs):
        self.project = self.get_object()
        return super(UpdateProjectDependencyView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.project = self.get_object()
        return super(UpdateProjectDependencyView, self).post(request, *args, **kwargs)


    def form_valid(self, form):
        packages = form.cleaned_data['packages']
        ProjectDependency.objects.filter(project=self.project).delete()
        for package_name, version in packages.iteritems():
            try:
                package = Package.objects.get(name=package_name)
            except Package.DoesNotExist:
                package = Package.create_with_provider_url(package_name)
            project_dependency = ProjectDependency.objects.create(
                project=self.project, package=package, version=version)
        return super(UpdateProjectDependencyView, self).form_valid(form)


project_update_dependency = UpdateProjectDependencyView.as_view()


class ResignProjectView(MemberRequiredMixin, DeleteView):
    success_url = reverse_lazy('folivora_project_list')

    def get_object(self, queryset=None):
        slug = self.kwargs['slug']
        self.project = Project.objects.get(slug=slug)
        user = self.request.user
        return ProjectMember.objects.get(project=self.project, user=user)

    def get_context_data(self, **kwargs):
        context = super(ResignProjectView, self).get_context_data(**kwargs)
        context['project'] = self.project
        return context


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
