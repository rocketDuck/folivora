from django.conf.urls import patterns, include, url

urlpatterns = patterns('folivora.views',
    (r'^accounts/', include('registration.backends.default.urls')),
    url('^$', 'test', name='folivora_index'),
    url('^projects/$', 'project_list', name='folivora_project_list'),
)
