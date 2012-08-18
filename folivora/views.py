from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from braces.views import LoginRequiredMixin

from .forms import AddProjectForm
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

project_detail = lambda x, slug: render(x, 'folivora/index.html')
project_edit = lambda x, slug: render(x, 'folivora/index.html')


class UpdateUserProfileView(UpdateView):
    model = UserProfile

    def get_queryset(self):
        return self.request.user.get_profile()


profile_edit = UpdateUserProfileView.as_view()
