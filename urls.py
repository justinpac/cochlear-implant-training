from django.conf.urls import patterns, url
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = patterns('cochlear',
    url(r'^$', 'views.index', name='index' ),
    url(r'^history/$','views.history', name = 'history'),
    url(r'^sessionEndPage/$','views.sessionEndPage', name = 'sessionEndPage'),
    url(r'^trainingEndPage/$','views.trainingEndPage', name = 'trainingEndPage'),
    #Training modules
    url(r'^speaker/(?P<speaker_module>[\d]+)/(?P<repeatFlag>[\d]+)/(?P<order_id>[\d]+)/$', 'views.speaker', name='speaker'),
    url(r'^closedSetText/(?P<closed_set_text>[\d]+)/(?P<repeatFlag>[\d]+)/(?P<order_id>[\d]+)/$','views.closedSetText', name = 'closedSetText'),
    url(r'^openSet/(?P<open_set_module>[\d]+)/(?P<repeatFlag>[\d]+)/(?P<order_id>[\d]+)/$','views.openSet', name = 'openSet'),
    #Training module "gap" pages
    url(r'^speakerGap/(?P<speaker_module>[\d]+)/(?P<repeatFlag>[\d]+)/(?P<order_id>[\d]+)/$', 'views.speakerGap', name='speakerGap'),
    url(r'^closedSetTextGap/(?P<closed_set_text>[\d]+)/(?P<repeatFlag>[\d]+)/(?P<order_id>[\d]+)/$','views.closedSetTextGap', name = 'closedSetTextGap'),
    url(r'^openSetGap/(?P<open_set_module>[\d]+)/(?P<repeatFlag>[\d]+)/(?P<order_id>[\d]+)/$','views.openSetGap', name = 'openSetGap'),
    #Session logic
    url(r'^startNewSession/$','views.startNewSession', name = 'startNewSession'),
    url(r'^goToNextModule/$','views.goToNextModule', name = 'goToNextModule'),
    #Manager pages
    url(r'^dashboard/$','views.dashboard', name = 'dashboard'),
    url(r'^dashboard/closedsettextAdd/$','views.closedsettextAdd', name='closedsettextAdd'),
    url(r'^dashboard/refreshClosedSetTextAdd/$','views.refreshClosedSetTextAdd', name = 'refreshClosedSetTextAdd'),
    url(r'^dashboard/opensetAdd/$','views.opensetAdd', name='opensetAdd'),
    url(r'^dashboard/speakeridAdd/$','views.speakeridAdd', name='speakeridAdd'),
    url(r'^dashboard/refreshspeakeridAdd/$','views.refreshspeakeridAdd', name = 'refreshspeakeridAdd'),
    url(r'^analytics/$','views.analytics', name = 'analytics'),
    #ajax methods
    url(r'^loadUserStat/$','views.loadUserStat',name = 'loadUserStat'),
    url(r'^loadSpeechDatatable/$','views.loadSpeechDatatable',name = 'loadSpeechDatatable'),
    url(r'^loadSpeakerDatatable/$','views.loadSpeakerDatatable',name = 'loadSpeakerDatatable'),
    url(r'^loadSoundDatatable/$','views.loadSoundDatatable',name = 'loadSoundDatatable'),
    url(r'^loadSourceDatatable/$','views.loadSourceDatatable',name = 'loadSourceDatatable'),
    url(r'^loadCSTDatatable/$','views.loadCSTDatatable',name = 'loadCSTDatatable'),
    url(r'^loadOSMDatatable/$','views.loadOSMDatatable',name = 'loadOSMDatatable'),
    url(r'^loadSIDDatatable/$','views.loadSIDDatatable',name = 'loadSIDDatatable'),
    url(r'^openSetCompleted/$','views.openSetCompleted', name = 'openSetCompleted'),
    url(r'^openSetAnswerKey/$','views.openSetAnswerKey', name = 'openSetAnswerKey'),
    url(r'^isCorrectClosedSetText/$','views.isCorrectClosedSetText', name = 'isCorrectClosedSetText'),
    url(r'^closedSetTextCompleted/$','views.closedSetTextCompleted', name = 'closedSetTextCompleted'),
    url(r'^isCorrectSpeaker/$','views.isCorrectSpeaker', name = 'isCorrectSpeaker'),
    url(r'^speakerCompleted/$','views.speakerCompleted', name = 'speakerCompleted'),
    url(r'^getDashboardData/','views.getDashboardData',name = 'getDashboardData'),
    url(r'^upload_speech/','views.uploadSpeech',name = 'uploadSpeech'),
    url(r'^getSpeakers/$','views.getSpeakers',name = 'getSpeakers'),
    url(r'^createSpeaker/$','views.createSpeaker', name = 'createSpeaker'),
    url(r'^upload_sound/','views.uploadSound',name = 'uploadSound'),
    url(r'^getSoundSources/$','views.getSoundSources',name = 'getSoundSources'),
    url(r'^createSoundSource/$','views.createSoundSource', name = 'createSoundSource'),
    #CSV downloads
    url(r'^getUserDataCSV/$','views.getUserDataCSV', name = 'getUserDataCSV'),
    url(r'^getUserDataCSV/(?P<subset>[\d]+)/$','views.getUserDataCSV', name = 'getUserDataCSV'),
)
