from django.conf.urls import patterns, url
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = patterns('cochlear',
    url(r'^$', 'views.index', name='index' ),
    url(r'^history/$','views.history', name = 'history'),
    url(r'^sessionEndPage/$','views.sessionEndPage', name = 'sessionEndPage'),
    url(r'^trainingEndPage/$','views.trainingEndPage', name = 'trainingEndPage'),
    url(r'^speaker/(?P<speaker_module>[\d]+)/(?P<repeatFlag>[\d]+)/(?P<order_id>[\d]+)/$', 'views.speaker', name='speaker' ),
    url(r'^openSet/(?P<open_set_module>[\d]+)/(?P<repeatFlag>[\d]+)/(?P<order_id>[\d]+)/$','views.openSet', name = 'openSet'),
    url(r'^startNewSession/$','views.startNewSession', name = 'startNewSession'),
    url(r'^goToNextModule/$','views.goToNextModule', name = 'goToNextModule'),
    #Manager pages
    url(r'^dashboard/$','views.dashboard', name = 'dashboard'),
    url(r'^dashboard/newsound$','views.new_sound', name = 'new_sound'),
    url(r'^dashboard/newmodule$','views.new_module', name = 'new_module'),
    url(r'^analytics/$','views.analytics', name = 'analytics'),
    #ajax methods
    url(r'^openSetCompleted/$','views.openSetCompleted', name = 'openSetCompleted'),
    url(r'^speakerCompleted/$','views.speakerCompleted', name = 'speakerCompleted'),
    url(r'^getSpeakers/(?P<name>[\w|\W]+)/','views.getSpeakers',name = 'getSpeakers'),
    url(r'^upload_sound/','views.uploadSound',name = 'uploadSound'),
    url(r'^getDashboardData/','views.getDashboardData',name = 'getDashboardData'),
)

#if settings.DEBUG is True:
#    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
