from .models import Project
from .utils.forms import ModelForm


class AddProjectForm(ModelForm):
    class Meta:
        model = Project
        exclude = ('members',)
