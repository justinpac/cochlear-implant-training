from django.conf.urls import patterns, url

urlpatterns = patterns('cochlea',
    url(r'^$', 'views.index', name='index' ),
)