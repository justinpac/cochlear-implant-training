from django.conf.urls import patterns, url
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = patterns('cochlear',
    url(r'^$', 'views.index', name='index' ),
    url(r'^speaker/$', 'views.speaker', name='speaker' ),
    url(r'^history/$','views.history', name = 'history'),
    #Manager pages
    url(r'^dashboard/$','views.dashboard', name = 'dashboard'),
    url(r'^dashboard/newsound$','views.new_sound', name = 'new_sound'),
    url(r'^dashboard/newmodule$','views.new_module', name = 'new_module'),
    url(r'^analytics/$','views.analytics', name = 'analytics'),
    #ajax methods
    url(r'^sessionCompleted/$','views.sessionCompleted',name = 'sessionCompleted'),
    url(r'^getSpeakers/(?P<name>[\w|\W]+)/','views.getSpeakers',name = 'getSpeakers')
)

#if settings.DEBUG is True:
#    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
