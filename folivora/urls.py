from django.conf.urls import patterns, include, url

# register signal handlers
from . import receivers


project_patterns = patterns('folivora.views',
    url(r'^$', 'project_detail', name='folivora_project_detail'),
    url(r'^edit/$', 'project_update', name='folivora_project_update'),
    url(r'^delete/$', 'project_delete', name='folivora_project_delete'),
    url(r'^add_member/$', 'project_add_member', name='folivora_project_member_add'),
    url(r'^deps/$', 'project_update_dependency', name='folivora_project_dependency_update'),
    url(r'^resign/$', 'project_resign', name='folivora_project_resign'),
)

urlpatterns = patterns('folivora.views',
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^accounts/profile/$', 'profile_edit', name='folivora_profile_edit'),
    url(r'^$', 'folivora_index', name='folivora_index'),
    url(r'^dashboard/$', 'folivora_dashboard', name='folivora_dashboard'),
    url(r'^projects/$', 'project_list', name='folivora_project_list'),
    url(r'^projects/add/$', 'project_add', name='folivora_project_add'),
    url(r'^project/(?P<slug>[\w-]+)/', include(project_patterns)),
)
