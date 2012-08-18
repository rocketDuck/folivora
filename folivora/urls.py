from django.conf.urls import patterns, include, url

urlpatterns = patterns('folivora.views',
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^accounts/profile/$', 'profile_edit', name='folivora_profile_edit'),
    url(r'^$', 'folivora_index', name='folivora_index'),
    url(r'^projects/$', 'project_list', name='folivora_project_list'),
    url(r'^projects/add$', 'project_add', name='folivora_project_add'),
    url(r'^project/(?P<slug>[\w-]+)/$', 'project_detail', name='folivora_project_detail'),
    url(r'^project/(?P<slug>[\w-]+)/edit/$', 'project_update', name='folivora_project_update'),
    url(r'^project/(?P<slug>[\w-]+)/delete/$', 'project_delete', name='folivora_project_delete'),
    url(r'^project/(?P<slug>[\w-]+)/add/$', 'project_add_member', name='folivora_project_member_add'),
)
