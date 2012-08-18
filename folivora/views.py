# -*- coding: utf-8 -*-


import json

from django.core.urlresolvers import reverse_lazy, reverse
from django.forms.models import inlineformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from django.contrib import messages

from braces.views import LoginRequiredMixin, UserFormKwargsMixin

from .forms import (AddProjectForm, UpdateUserProfileForm,
    ProjectDependencyForm, ProjectMemberForm, CreateProjectMemberForm)
from .models import (Project, UserProfile, ProjectDependency, ProjectMember,
    Log)
from .utils.views import SortListMixin, MemberRequiredMixin


folivora_index = TemplateView.as_view(template_name='folivora/index.html')


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

    def get_context_data(self, **kwargs):
        context = super(UpdateProjectView, self).get_context_data(**kwargs)
        data = self.request.POST if self.request.method == 'POST' else None
        object = Project.objects.get(slug=self.kwargs['slug'])
        dep_form = self.dep_form_class(data, queryset=self.dep_qs,
                                       instance=object)
        member_form = self.member_form_class(data, instance=object,
                                             queryset=self.member_qs)
        add_member_form = CreateProjectMemberForm()
        context.update({
            'dep_form': dep_form,
            'member_form': member_form,
            'add_member_form': add_member_form,
            'project': object,
        })
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        ctx = self.get_context_data(**kwargs)
        forms = [ctx['dep_form'], ctx['member_form']]
        if all(map(lambda f: f.is_valid(), forms)):
            for form in forms:
                form.save()
            object = Project.objects.get(slug=kwargs['slug'])
            messages.success(request, _(u'Updated Project “{name}” '
                'successfully.').format(name=object.name))
            return HttpResponseRedirect(reverse('folivora_project_update',
                                                kwargs={'slug': object.slug}))
        return self.render_to_response(ctx)


project_update = UpdateProjectView.as_view()


class DeleteProjectView(MemberRequiredMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('folivora_project_list')

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


class CreateProjectMemberView(LoginRequiredMixin, TemplateView):
    model = ProjectMember
    form_class = CreateProjectMemberForm

    def post(self, request, *args, **kwargs):
        project = Project.objects.get(slug=kwargs['slug'])
        form = CreateProjectMemberForm(request.POST)
        if form.is_valid():
            project_member = form.save(commit=False)
            project_member.project = project
            project_member.state = ProjectMember.MEMBER
            user = project_member.user
            if (ProjectMember.objects.filter(project=project)
                                     .filter(user=user).exists()):
                context = {'error': _('"%s" is already a member of this project'
                                       % user)}
            else:
                project_member.save()
                context = {'id': project_member.id,
                           'username': project_member.user.username}
        else:
            context = {'error': form.errors}
        return HttpResponse(json.dumps(context))


project_add_member = CreateProjectMemberView.as_view()


class ResignProjectView(LoginRequiredMixin, DeleteView):
    success_url = reverse_lazy('folivora_project_list')

    def get_object(self, queryset=None):
        slug = self.kwargs.get('slug', None)
        if slug is None:
            raise AttributeError('ResignProjectView must be called with a slug')
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
        return self.request.user.get_profile()


profile_edit = UpdateUserProfileView.as_view()
