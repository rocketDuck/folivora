# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse_lazy, reverse
from django.forms.models import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from django.contrib import messages

from braces.views import LoginRequiredMixin, UserFormKwargsMixin

from .forms import (AddProjectForm, UpdateUserProfileForm,
    ProjectDependencyForm, ProjectMemberForm)
from .models import Project, UserProfile, ProjectDependency, ProjectMember
from .utils.views import SortListMixin


folivora_index = TemplateView.as_view(template_name='folivora/index.html')


class ListProjectView(LoginRequiredMixin, SortListMixin, ListView):
    model = Project
    context_object_name = 'projects'
    sort_fields = ['name']
    default_order = ('name',)

    def get_queryset(self):
#        return Project.objects.filter(members=self.request.user)
        return super(ListProjectView, self).get_queryset()


project_list = ListProjectView.as_view()


class AddProjectView(LoginRequiredMixin, UserFormKwargsMixin, CreateView):
    model = Project
    form_class = AddProjectForm
    template_name_suffix = '_add'


project_add = AddProjectView.as_view()


class UpdateProjectView(LoginRequiredMixin, TemplateView):
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
        context.update({
            'dep_form': dep_form,
            'member_form': member_form
        })
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        forms = [v for k,v in context.items() if k.endswith('form')]
        if all(map(lambda f: f.is_valid, forms)):
            for form in forms:
                form.save()
            object = Project.objects.get(slug=kwargs['slug'])
            messages.success(request, _(u'Updated Project “{name}” '
                'successfully.').format(name=object.name))
            return HttpResponseRedirect(reverse('folivora_project_update',
                                                kwargs={'slug': object.slug}))
        return self.render_to_response(context)


project_update = UpdateProjectView.as_view()


class DeleteProjectView(LoginRequiredMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('folivora_project_list')

    def delete(self, *args, **kwargs):
        object = self.get_object()
        if object:
            messages.success(self.request, _(u'Deleted project “{name}” '
                'successfully.').format(name=object.name))
        return super(DeleteView, self).delete(*args, **kwargs)


project_delete = DeleteProjectView.as_view()

project_detail = lambda x, slug: render(x, 'folivora/index.html')


class UpdateUserProfileView(LoginRequiredMixin, UpdateView):
    form_class = UpdateUserProfileForm
    def get_object(self, queryset=None):
        return self.request.user.get_profile()


profile_edit = UpdateUserProfileView.as_view()
