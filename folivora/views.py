from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from braces.views import LoginRequiredMixin

from .forms import AddProjectForm
from .models import Project


folivora_index = TemplateView.as_view(template_name='folivora/index.html')


class ListProjectView(LoginRequiredMixin, ListView):
    context_object_name = 'projects'

    def get_queryset(self):
        return Project.objects.filter(members=self.request.user)


project_list = ListProjectView.as_view()


class AddProjectView(CreateView):
    model = Project
    form_class = AddProjectForm


project_add = AddProjectView.as_view()

project_detail = lambda x, slug: render(x, 'folivora/index.html')
