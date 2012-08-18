from .models import Project, UserProfile
from .utils.forms import ModelForm


class AddProjectForm(ModelForm):
    class Meta:
        model = Project
        exclude = ('members',)


class UpdateUserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('user',)
