from django.conf.urls import patterns, include, url

urlpatterns = patterns('folivora.views',
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^accounts/profile/$', 'profile_edit', name='folivora_profile_edit'),
    url(r'^$', 'folivora_index', name='folivora_index'),
    url(r'^dashboard/$', 'folivora_dashboard', name='folivora_dashboard'),
    url(r'^projects/$', 'project_list', name='folivora_project_list'),
    url(r'^projects/add/$', 'project_add', name='folivora_project_add'),
    url(r'^project/(?P<slug>[\w-]+)/$', 'project_detail', name='folivora_project_detail'),
    url(r'^project/(?P<slug>[\w-]+)/edit/$', 'project_update', name='folivora_project_update'),
    url(r'^project/(?P<slug>[\w-]+)/delete/$', 'project_delete', name='folivora_project_delete'),
    url(r'^project/(?P<slug>[\w-]+)/add_member/$', 'project_add_member', name='folivora_project_member_add'),
    url(r'^project/(?P<slug>[\w-]+)/deps/$', 'project_update_dependency', name='folivora_project_dependency_update'),
    url(r'^project/(?P<slug>[\w-]+)/resign/$', 'project_resign', name='folivora_project_resign'),
)
