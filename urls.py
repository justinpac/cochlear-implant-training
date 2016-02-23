from django.conf.urls import patterns, url

urlpatterns = patterns('cochlear',
    url(r'^$', 'views.index', name='index' ),
    url(r'^speaker/$', 'views.speaker', name='speaker' ),
)
