# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render
from django.utils.translation import ugettext
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from django.contrib import messages

from braces.views import LoginRequiredMixin

from .forms import AddProjectForm, UpdateUserProfileForm
from .models import Project, UserProfile
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


class AddProjectView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = AddProjectForm


project_add = AddProjectView.as_view()


class DeleteProjectView(LoginRequiredMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('folivora_project_list')

    def delete(self, *args, **kwargs):
        object = self.get_object()
        if object:
            messages.success(self.request, ugettext(u"Project “{name}” "
                "deleted successfully.").format(name=object.name))
        return super(DeleteView, self).delete(*args, **kwargs)


project_delete = DeleteProjectView.as_view()

project_detail = lambda x, slug: render(x, 'folivora/index.html')
project_edit = lambda x, slug: render(x, 'folivora/index.html')


class UpdateUserProfileView(UpdateView):
    form_class = UpdateUserProfileForm
    def get_object(self, queryset=None):
        return self.request.user.get_profile()


profile_edit = UpdateUserProfileView.as_view()
