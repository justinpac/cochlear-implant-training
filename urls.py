from django.conf.urls import patterns, url
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = patterns('cochlear',
    url(r'^$', 'views.index', name='index' ),
    url(r'^speaker/$', 'views.speaker', name='speaker' ),
    url(r'^history/$','views.history', name = 'history'),
    #Manager pages
    url(r'^dashboard/$','views.dashboard', name = 'dashboard'),
    url(r'^settings/$','views.settings', name = 'settings'),
    #ajax methods
    url(r'^sessionCompleted/$','views.sessionCompleted',name = 'sessionCompleted')
)

#if settings.DEBUG is True:
#    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
