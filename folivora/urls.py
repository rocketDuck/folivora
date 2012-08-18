from django.conf.urls import patterns, include, url

urlpatterns = patterns('folivora.views',
    url('^test$', 'test'),
)
