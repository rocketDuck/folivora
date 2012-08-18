from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url('^accounts/', include('django.contrib.auth.urls')),
    url('^', include('folivora.urls')),
)
