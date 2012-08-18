from django.shortcuts import render
from django.views.generic.list import ListView

from braces.views import LoginRequiredMixin

from .models import Project

def test(request):
    return render(request, 'base.html')


class ProjectListView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        return Project.objects.filter(members=self.request.user)


project_list = ProjectListView.as_view()
