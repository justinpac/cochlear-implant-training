from django.shortcuts import render,redirect
from django.http import HttpResponse
import json, datetime, logging
from django.db.models import Q, Max

# We need this to generate the navbar
from hipercore.helpers import NavigationBar

# Import our database models
from cochlear.models import *

#Some helper functions
import cochlear.util

#Get django timezone utility
from django.utils import timezone
import random #To generate random numbers

#For generating csv files
import csv
from django.utils.six.moves import range
from django.http import StreamingHttpResponse


SESSION_CAP = 4

OPEN_SET_MODULE_TYPES = ['Other','Meaningful Sentence','Anomalous Sentence','Word','Environmental'] 
CLOSED_SET_TEXT_TYPES = ['Other','Phoneme','Environmental']
ALL_MODULE_TYPES = ['Closed Set Text','Open Set','Speaker ID']

def index(request):
	#If user is manager, redirect to the manager dashboard (so the homepage always takes the manager to their dashboard)
	permission = cochlear.util.GetUserPermission(request.user.username);
	if(permission > 0):
		return redirect('cochlear:dashboard')

	#Render a basic page
	context = NavigationBar.generateAppContext(request,app="cochlear",title="index", navbarName=0)
	userList = User_Attrib.objects.filter(username=request.user.username)
	context['cochlearUser'] = userList[0]

	# Once a user starts their first session on a given week, we give them one week to complete all their sessions
	# If it's been over a week since the user started their first session of a week, We want the progress bar to show 
	# they they have completed 0 sessions that week
	currentTime = timezone.now()
	if (userList[0].current_week_start_date == None) or (currentTime - userList[0].current_week_start_date) > datetime.timedelta(days=7):
		context['sessions'] = 0
	else:
		context['sessions'] = User_Session.objects.filter(user=userList[0], date_completed__range=(userList[0].current_week_start_date,currentTime)).count()
	context['percentComplete'] = context['sessions'] * 25

	#Indicate if less than 24 hours have passed since the last session
	oneDayAgo = currentTime - datetime.timedelta(days=1)
	recentSession = User_Session.objects.filter(user=userList[0], date_completed__range=(oneDayAgo,currentTime))
	if not recentSession:
		context['recentSessionFlag'] = 0
	else:
		context['recentSessionFlag'] = 1

	#Indicate if there is an active session
	active_session = User_Session.objects.filter(user=userList[0], date_completed=None)
	nextSession = getNextSession(userList[0])
	print(str(nextSession))
	if not nextSession: # There are no more sessions for the user to complete
		context['sessionFlag'] = 0
	elif not active_session: # The user may start a new session
		context['sessionFlag'] = 1
	else: # the user may continue their current session
		context['sessionFlag'] = 2
	return render(request,'cochlear/index.html',context)

def history(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="history", navbarName=0)

	return render(request,'cochlear/history.html',context)
def sessionEndPage(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="sessionEndPage", navbarName=0)
	return render(request,'cochlear/sessionEndPage.html',context)

def trainingEndPage(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="trainingEndPage", navbarName=0)
	return render(request,'cochlear/trainingEndPage.html',context)

######################
## Training Modules ##
######################

# Render the speaker identification page
def speaker(request, speaker_module, repeatFlag, order_id):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="speaker", navbarName=0)
	userObj = User_Attrib.objects.get(username=request.user.username)
	module = Speaker_ID.objects.get(id=speaker_module)
	context['unknown_speech'] = module.unknown_speech
	context['speaker_choices'] = module.choices.all().order_by('?')
	context['speaker_module_id'] = module.id
	context['user_attrib_id'] = userObj.id
	context['repeatFlag'] = repeatFlag
	context['order_id'] = order_id

	return render(request,'cochlear/speaker.html',context)

# Render a closed set identification page
def closedSetText(request, closed_set_text, repeatFlag, order_id):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="closedSetText", navbarName=0)
	userObj = User_Attrib.objects.get(username=request.user.username)
	module = Closed_Set_Text.objects.get(id=closed_set_text)
	context['unknown_sound'] = module.unknown_speech.speech_file.url if module.unknown_speech else module.unknown_sound.sound_file.url
	context['text_choices'] = module.text_choices.all().order_by('?')
	context['closed_set_text_id'] = module.id
	context['module_type'] = module.module_type
	context['user_attrib_id'] = userObj.id
	context['repeatFlag'] = repeatFlag
	context['order_id'] = order_id

	return render(request,'cochlear/closedSetText.html',context)

#Render a generic page for a closed-set module
def openSet(request, open_set_module, repeatFlag, order_id):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="openSet", navbarName=0)
	user_attrib = User_Attrib.objects.get(username=request.user.username)
	module = Open_Set_Module.objects.get(id=open_set_module)
	if module.unknown_speech:
		context['unknown_sound'] = module.unknown_speech.speech_file.url
	else:
		context['unknown_sound'] = module.unknown_sound.sound_file.url
	context['module_type'] = module.module_type
	context['repeatFlag'] = repeatFlag
	context['order_id'] = order_id
	context['open_set_module_id'] = open_set_module
	context['user_attrib_id'] = user_attrib.id

	return render(request,'cochlear/openSet.html',context)

#################################
## Training Module "Gap" Pages ##
#################################

def speakerGap(request, speaker_module, repeatFlag, order_id):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="speakerGap", navbarName=0)
	context['speaker_module'] = speaker_module
	context['repeatFlag'] = repeatFlag
	context['order_id'] = order_id
	return render(request,'cochlear/speakerGap.html',context)

def closedSetTextGap(request, closed_set_text, repeatFlag, order_id):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="closedSetTextGap", navbarName=0)
	context['closed_set_text'] = closed_set_text
	context['repeatFlag'] = repeatFlag
	context['order_id'] = order_id
	return render(request,'cochlear/closedSetTextGap.html',context)

def openSetGap(request, open_set_module, repeatFlag, order_id):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="openSetGap", navbarName=0)
	context['open_set_module'] = open_set_module
	context['repeatFlag'] = repeatFlag
	context['order_id'] = order_id
	return render(request,'cochlear/openSetGap.html',context)

###################
## Session Logic ##
###################

def startNewSession(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="startNewSession", navbarName=0)
	userObj = User_Attrib.objects.get(username=request.user.username)
	nextSession = getNextSession(userObj)
	if not nextSession:
		return redirect('cochlear:trainingEndPage')
	#Create user-specific objects for this session
	createUserSessionData(nextSession, userObj)
	checkWeekProg(userObj)

	return goToModule(nextSession, 1, userObj)

def goToNextModule(request):
	userObj = User_Attrib.objects.get(username=request.user.username)
	user_session = User_Session.objects.filter(user = userObj.id, date_completed = None)
	if not user_session:
		return redirect('cochlear:sessionEndPage')
	user_session = user_session.first()
	if user_session.modules_completed == user_session.session.countModules():
		user_session.date_completed = timezone.now()
		user_session.save()
		return redirect('cochlear:sessionEndPage')
	nextModule = user_session.modules_completed + 1
	return goToModule(user_session.session, nextModule, userObj)

# Get a module in a particular session based on its order in sequence (moduleNum)
# This is in a separate function because it will be used in multiple contexts and
# continue to grow with the number of modules
def goToModule(session, moduleNum, userObj):
	user_session = User_Session.objects.get(user = userObj, date_completed = None)
	module = session.speaker_ids.filter(speaker_id_order__order = moduleNum)
	if not module:
		module = session.open_set_modules.filter(open_set_module_order__order = moduleNum)
		if not module:
			module = session.closed_set_texts.filter(closed_set_text_order__order = moduleNum)
			order_id = Closed_Set_Text_Order.objects.get(session = session, order = moduleNum).id
			if user_session.first_closed_set_text:
				user_session.first_closed_set_text = False
				user_session.save()
				return redirect('cochlear:closedSetTextGap', closed_set_text = module.first().id, repeatFlag = 0, order_id = order_id)
			return redirect('cochlear:closedSetText', closed_set_text = module.first().id, repeatFlag = 0, order_id = order_id)

		order_id = Open_Set_Module_Order.objects.get(session = session, order = moduleNum).id
		if user_session.first_open_set_module:
			user_session.first_open_set_module = False
			user_session.save()
			return redirect('cochlear:openSetGap', open_set_module=module.first().id, repeatFlag = 0, order_id = order_id)
		return redirect('cochlear:openSet', open_set_module=module.first().id, repeatFlag = 0, order_id = order_id)

	order_id = Speaker_ID_Order.objects.get(session = session, order = moduleNum).id
	if user_session.first_speaker_id:
		user_session.first_speaker_id = False
		user_session.save()
		return redirect('cochlear:speakerGap', speaker_module=module.first().id, repeatFlag = 0, order_id = order_id)
	return redirect('cochlear:speaker', speaker_module=module.first().id, repeatFlag = 0, order_id = order_id)

#Takes in a user_attrib object and returns the next session the user needs to complete
def getNextSession(userObj):
	user_sessions = User_Session.objects.filter(user = userObj, date_completed__isnull = False) # get the sessions that the user has completed
	#If the user has not completed any sessions, then they are on the session for week 1, day 1
	if not user_sessions:
		checkWeekProg(userObj)
		week1Day1 = Session.objects.get(week = 1, day = 1)
		return week1Day1

	#Get the max session day and week that the user has completed
	maxWeekComplete = user_sessions.aggregate(Max('session__week'))['session__week__max']
	user_sessions_cur_week = user_sessions.filter(session__week = maxWeekComplete)
	maxDayComplete = user_sessions_cur_week.aggregate(Max('session__day'))['session__day__max']

	print(maxWeekComplete)
	print(maxDayComplete)

	# Get the next session the user needs to complete
	nextSession = Session.objects.filter(Q(speaker_ids__isnull=False) | Q(open_set_modules__isnull=False) | Q(closed_set_texts__isnull=False), week = (maxWeekComplete), day = (maxDayComplete + 1)).distinct()
	if not nextSession: 
		# Either the next session is on a new week or there are no sessions left for the user to complete
		nextSession = Session.objects.filter(Q(speaker_ids__isnull=False) | Q(open_set_modules__isnull=False) | Q(closed_set_texts__isnull=False), week = (maxWeekComplete + 1), day = 1).distinct()
		if not nextSession:
			# We want this date to change the next time there is actually another session to complete, so no call to checkWeekProg
			return None
	return nextSession.first()


##################
## Ajax methods ##
##################

def openSetCompleted(request):
	userList = User_Attrib.objects.filter(username=request.user.username)
	user = userList[0]
	#Get some information passed in from the template
	isRepeat = bool(int(request.POST['isRepeat']))
	user_response = request.POST['user_response']
	open_set_module_order = Open_Set_Module_Order.objects.get(id = int(request.POST['order_id']))
	percentCorrect = int(request.POST['percentCorrect'])

	if(not isRepeat):
		# If this module is not being repeated, then we want to edit the existing User_Open Set_Train record
		moduleHist = User_Open_Set_Module.objects.get(open_set_module_order = open_set_module_order, user_attrib = user, repeat = False)
		if (moduleHist.date_completed == None):
			# Indicate the user has completed another module within the session. Tracked in User_Session and User_Open_Set_Module
			user_session = User_Session.objects.get(user=user.id, date_completed=None)
			user_session.modules_completed += 1
			user_session.save()
			moduleHist.date_completed = timezone.now()
			moduleHist.user_response = user_response
			moduleHist.percent_correct = percentCorrect
	else:
		# if this module IS being repeated, then create a new User_Open_Set_Module
		moduleHist = User_Open_Module_Train(open_set_module_order = open_set_module_order, user_attrib = user, repeat = True, 
			date_completed = timezone.now(), user_response = user_response, percent_correct=percentCorrect)
	
	moduleHist.save()
	return HttpResponse("Success")

def openSetAnswerKey(request):
	module = Open_Set_Module_Order.objects.get(id = int(request.GET['order_id'])).open_set_module
	keyWords = module.key_words
	correctAnswer = module.answer
	purelist = [{'keyWords':keyWords, 'correctAnswer':correctAnswer}]
	data = json.dumps(purelist)
	return HttpResponse(data, content_type='application/json')

def isCorrectClosedSetText(request):
	closedSetText = Closed_Set_Text.objects.get(id = int(request.GET['module_id']))
	textChoice = Text_Choice.objects.get(id = int(request.GET['text_choice_id']))
	iscorrect = Closed_Set_Text_Choice.objects.get(closed_set_text = closedSetText , choice = textChoice).iscorrect
	purelist = [{'iscorrect':iscorrect}]
	data = json.dumps(purelist)
	return HttpResponse(data, content_type='application/json')

def closedSetTextCompleted(request):
	userList = User_Attrib.objects.filter(username=request.user.username)
	user = userList[0]
	#Get some information passed in from the template
	isRepeat = bool(int(request.POST['isRepeat']))
	user_response = Text_Choice.objects.get(id = int(request.POST['user_response']))
	answered_correctly = bool(int(request.POST['answered_correctly']))
	closed_set_text_order = Closed_Set_Text_Order.objects.get(id = int(request.POST['order_id']))

	if(not isRepeat):
		# If this module is not being repeated, then we want to edit the existing User_Closed Set_Text record
		moduleHist = User_Closed_Set_Text.objects.get(closed_set_text_order = closed_set_text_order, user_attrib = user, repeat = False)
		if(moduleHist.date_completed == None):
			# Indicate the user has completed another module within the session. Tracked in User_Session and User_Closed_Set_Text
			user_session = User_Session.objects.get(user=user.id, date_completed=None)
			user_session.modules_completed += 1
			user_session.save()
			moduleHist.date_completed = timezone.now()
			moduleHist.user_response = user_response
			moduleHist.correct = answered_correctly
	else:
		# if this module IS being repeated, then create a new User_Speaker_ID
		moduleHist = User_Closed_Set_Text(closed_set_text_order = closed_set_text_order, user_attrib = user, repeat = True, date_completed = timezone.now(), 
			user_response = user_response, correct = answered_correctly)

	moduleHist.save()
	return HttpResponse("Success")

def isCorrectSpeaker(request):
	speakerID = Speaker_ID.objects.get(id = int(request.GET['module_id']))
	speech = Speech.objects.get(id = int(request.GET['speech_id']))
	iscorrect = Speaker_ID_Choice.objects.get(speaker_id = speakerID, choice = speech).iscorrect
	purelist = [{'iscorrect':iscorrect}]
	data = json.dumps(purelist)
	return HttpResponse(data, content_type='application/json')


def speakerCompleted(request):
	userList = User_Attrib.objects.filter(username=request.user.username)
	user = userList[0]
	#Get some information passed in from the template
	isRepeat = bool(int(request.POST['isRepeat']))
	user_response = Speech.objects.get(id = int(request.POST['user_response']))
	answered_correctly = bool(int(request.POST['answered_correctly']))
	speaker_id_order = Speaker_ID_Order.objects.get(id = int(request.POST['order_id']))

	if(not isRepeat):
		# If this module is not being repeated, then we want to edit the existing User_Closed Set_Train record
		moduleHist = User_Speaker_ID.objects.get(speaker_id_order = speaker_id_order, user_attrib = user, repeat = False)
		if(moduleHist.date_completed == None):
			# Indicate the user has completed another module within the session. Tracked in User_Session and User_Speaker_ID
			user_session = User_Session.objects.get(user=user.id, date_completed=None)
			user_session.modules_completed += 1
			user_session.save()
			moduleHist.date_completed = timezone.now()
			moduleHist.user_response = user_response
			moduleHist.correct = answered_correctly
	else:
		# if this module IS being repeated, then create a new User_Speaker_ID
		moduleHist = User_Speaker_ID(speaker_id_order = speaker_id_order, user_attrib = user, repeat = True, date_completed = timezone.now(), 
			user_response = user_response, correct = answered_correctly)

	moduleHist.save()
	return HttpResponse("Success")

def getDashboardData(request):
	#Wrap dashboard data in json 
	ctx =  {}
	loadDashboardData(ctx)
	data = json.dumps(ctx)
	return HttpResponse(data, content_type='application/json')

def uploadSpeech(request):
	if(request.method == "POST"):#If the user has submitted something, Handle the upload
		speakerID = int(request.POST['speaker_id']);
		rawFile = request.FILES['file'];
		#A new speaker was added via the popup
		if(speakerID == -1):
			speaker_name = str(request.POST['speaker_name'])
			speakerList = Speaker.objects.filter(name=speaker_name);
			speakerID = speakerList[0].pk;
		#Create a new speech object, and attach it to the speaker
		speakerObj = Speaker.objects.get(pk=speakerID);
		newSoundObj = Speech();
		newSoundObj.speaker = speakerObj;
		newSoundObj.speech_file = rawFile;
		newSoundObj.save();
		return HttpResponse("Success")
	else:
		return HttpResponse("No POST data received.")

def getSpeakers(request):
	#Gets a list of authors whose names start with 'name'
	speakerList = Speaker.objects.filter(name__istartswith=request.GET['name'])
	purelist = []
	for speaker in speakerList:
		speakerObj = {}
		speakerObj['name'] = speaker.name;
		speakerObj['id'] = speaker.pk;
		#Get number of attached sound files
		speakerObj['file_count'] = Speech.objects.filter(speaker=speaker).count();
		purelist.append(speakerObj)
	data = json.dumps(purelist)
	return HttpResponse(data, content_type='application/json')

def createSpeaker(request):
	newSpeaker = Speaker();
	newSpeaker.name = request.POST['speaker_name']
	newSpeaker.display_name = request.POST['speaker_display_name']
	newSpeaker.gender = request.POST['speaker_gender']
	newSpeaker.notes = request.POST['speaker_notes']
	newSpeaker.save();
	return HttpResponse("Success")

def uploadSound(request):
	if(request.method == "POST"):#If the user has submitted something, Handle the upload
		sourceID = int(request.POST['source_id']);
		rawFile = request.FILES['file'];
		# A new source was added via the popup
		if(sourceID == -1):
			source_name = str(request.POST['source_name'])
			sourceList = Sound_Source.objects.filter(name=source_name);
			sourceID = sourceList[0].pk;
		#Create a new speech object, and attach it to the speaker
		sourceObj = Sound_Source.objects.get(pk=sourceID);
		newSoundObj = Sound();
		newSoundObj.source = sourceObj;
		newSoundObj.sound_file = rawFile;
		newSoundObj.save();
		return HttpResponse("Success")
	else:
		return HttpResponse("No POST data received.")

def getSoundSources(request):
	#Gets a list of authors whose names start with 'name'
	sourceList = Sound_Source.objects.filter(name__istartswith=request.GET['name'])
	purelist = []
	for source in sourceList:
		sourceObj = {}
		sourceObj['name'] = source.name;
		sourceObj['id'] = source.pk;
		#Get number of attached sound files
		sourceObj['file_count'] = Sound.objects.filter(source=source).count();
		purelist.append(sourceObj)
	data = json.dumps(purelist)
	return HttpResponse(data, content_type='application/json')

def createSoundSource(request):
	newSource = Sound_Source(name = request.POST['source_name'], display_name = request.POST['source_display_name'], notes = request.POST['source_notes']);
	newSource.save();
	return HttpResponse("Success")



###################
## Manager Pages ##
###################

#NOTE: Make sure to add the names of all the pages that should only be accessible
#by managers in middleware.py

# Loads data for a table
# ID - the uniwue identifier for this table
# headerArr - a one-dimensional array of table column headers
# dropDownHeaderArr - a one-dimensional array of labels for each dropdown (may be empty)
# dropDownArr - A two dimensionsal array of arrays, with each inner arrray being a set of dropdown options for eac dropdown header
# The outer array of dropdown arr should have as many elements as dropDownHeaderArr
# IMPORTANT - user must populate context[ID][rows] and context[ID][rowData] themselves after using this function.
# These are also arrays of arrays, with rows and rowData corresponding to headers and dropdown headers respectively.  
def loadTableData(context, ID, headerArr, dropDownHeaderArr, dropDownArr, subDropHeaderArr, subDropArr):
	context[ID] = {}
	context[ID]['headers'] = headerArr
	stdID = ID
	stdID = stdID.lower()
	stdID = stdID.replace(" ","-")
	context[ID]['id'] = stdID
	context[ID]['dropDownHeaders'] = dropDownHeaderArr
	#Each dropDownHeader should have an associated array in it
	context[ID]['dropDowns'] = dropDownArr
	# Sub drop down array positions should correspond to the drop down positions
	context[ID]['subDropHeaders'] = subDropHeaderArr
	context[ID]['subDrops'] = subDropArr

	#The below lines should not change between tables
	context[ID]['colSize'] = int(12/len(context[ID]['headers']))
	context[ID]['dropDownHeaderIDs'] = list(context[ID]['dropDownHeaders'])
	for i in range(len(context[ID]['dropDownHeaderIDs'])):
		context[ID]['dropDownHeaderIDs'][i] = context[ID]['dropDownHeaderIDs'][i].replace(' ','-')
		context[ID]['dropDownHeaderIDs'][i] = context[ID]['dropDownHeaderIDs'][i].lower()	
	context[ID]['subDropHeaderIDs'] = list(context[ID]['subDropHeaders'])
	for i in range(len(context[ID]['subDropHeaderIDs'])):
		context[ID]['subDropHeaderIDs'][i] = context[ID]['subDropHeaderIDs'][i].replace(' ','-')
		context[ID]['subDropHeaderIDs'][i] = context[ID]['subDropHeaderIDs'][i].lower()

	context[ID]['rows'] = []
	context[ID]['rowData'] = []
	context[ID]['rowSubData'] = []

def loadSpeechData(context):
	ID = 'speechFileList'
	headerArr = ['Filename','Speaker Name','Speaker Gender','Modules']
	dropDownHeaderArr = ['Module','Gender']
	dropDownArr = []
	dropDownArr.append(ALL_MODULE_TYPES)
	dropDownArr.append(['Male','Female','Other'])
	subDropHeaderArr = ['Module Type']
	subDropArr = []
	subDropArr.append([CLOSED_SET_TEXT_TYPES,OPEN_SET_MODULE_TYPES,[]])
	loadTableData(context, ID, headerArr, dropDownHeaderArr, dropDownArr, subDropHeaderArr, subDropArr)

	speechFiles = Speech.objects.all();
	for speech in speechFiles:
		rowSubData = [''] * len(context[ID]['dropDownHeaders'])

		module = ""
		modules = ""
		if Closed_Set_Text.objects.filter(unknown_speech=speech).exists():
			module += "0"
			modules += "CST "
			cst_speech = Closed_Set_Text.objects.filter(unknown_speech=speech)
			if cst_speech:
				for cst in cst_speech:
					rowSubData[0] += str(cst.module_type)
					rowSubData[0] += ','
		else:
			rowSubData[0] += 'N,'

		if Open_Set_Module.objects.filter(unknown_speech=speech).exists():
			module += "1"
			modules += "OSM "
			osm_speech = Open_Set_Module.objects.filter(unknown_speech=speech)
			if osm_speech:
				for osm in osm_speech:
					rowSubData[0] += str(osm.module_type)
					rowSubData[0] += ','
		else:
			rowSubData[0] += 'N,'
		if Speaker_ID.objects.filter(Q(unknown_speech=speech) | Q(choices=speech)).exists():
			module += "2"
			modules += "SID "
		rowSubData[0] += 'N,'
		if speech.speaker.gender.lower() == 'male':
			gender = 0
		elif speech.speaker.gender.lower() == 'female':
			gender = 1
		else:
			gender = 2
		row = [speech.speech_file.name.strip('cochlear/speech/'),speech.speaker.name, speech.speaker.gender, modules]
		context[ID]['rows'].append(row)
		context[ID]['rowData'].append([module, gender])
		context[ID]['rowSubData'].append(rowSubData)

def loadSpeakerData(context):
	ID = 'speakerFileList'
	headerArr = ['Speaker Name','Number of attached files','Gender','Modules','Notes']
	dropDownHeaderArr = ['Module']
	dropDownArr = []
	dropDownArr.append(ALL_MODULE_TYPES)
	subDropHeaderArr = ['Module Type']
	subDropArr = []
	subDropArr.append([CLOSED_SET_TEXT_TYPES,OPEN_SET_MODULE_TYPES,[]])
	loadTableData(context, ID, headerArr, dropDownHeaderArr, dropDownArr, subDropHeaderArr, subDropArr)

	speakerList = Speaker.objects.all();
	for speaker in speakerList:
		numOfFiles = Speech.objects.filter(speaker=speaker).count();
		rowSubData = [''] * len(context[ID]['dropDownHeaders'])
		module = ""
		modules = ""
		if Closed_Set_Text.objects.filter(unknown_speech__speaker=speaker).exists():
			module += "0"
			modules += "CST "
			cst_speakers = Closed_Set_Text.objects.filter(unknown_speech__speaker=speaker)
			if cst_speakers:
				for cst in cst_speakers:
					rowSubData[0] += str(cst.module_type)
					rowSubData[0] += ','
		else:
			rowSubData[0] += 'N,'
		if Open_Set_Module.objects.filter(unknown_speech__speaker=speaker).exists():
			module += "1"
			modules += "OSM "
			osm_speakers = Open_Set_Module.objects.filter(unknown_speech__speaker=speaker)
			if osm_speakers:
				for osm in osm_speakers:
					rowSubData[0] += str(osm.module_type)
					rowSubData[0] +=','
		else:
			rowSubData[0] += 'N,'
		if Speaker_ID.objects.filter(Q(unknown_speech__speaker=speaker) | Q(choices__speaker=speaker)).exists():
			module += "2"
			modules += "SID "
		rowSubData[0] += 'N,'
		if speaker.gender.lower() == 'male':
			gender = 0
		elif speaker.gender.lower() == 'female':
			gender = 1
		else:
			gender = 2
		
		row = [speaker.name,numOfFiles,speaker.gender,modules,speaker.notes]
		context['speakerFileList']['rows'].append(row)
		context[ID]['rowData'].append([module,gender])
		context[ID]['rowSubData'].append(rowSubData)

def loadSoundData(context):
	ID = 'soundFileList'
	headerArr = ['Filename','Source Name','Modules']
	dropDownHeaderArr = ['Module']
	dropDownArr = []
	dropDownArr.append(['Closed Set Text','Open Set'])
	subDropHeaderArr = ['Module Type']
	subDropArr = []
	subDropArr.append([CLOSED_SET_TEXT_TYPES,OPEN_SET_MODULE_TYPES])
	loadTableData(context, ID, headerArr, dropDownHeaderArr, dropDownArr, subDropHeaderArr, subDropArr)

	sourceFiles = Sound.objects.all();
	for sound in sourceFiles:
		rowSubData = [''] * len(context[ID]['dropDownHeaders'])
		
		module = ""
		modules = ""
		if Closed_Set_Text.objects.filter(unknown_sound=sound).exists():
			module += "0"
			modules +="CST "
			cst_sounds = Closed_Set_Text.objects.filter(unknown_sound=sound)
			if cst_sounds:
				for cst in cst_sounds:
					rowSubData[0] += str(cst.module_type)
					rowSubData[0] += ','
		else:
			rowSubData[0] += 'N,'

		if Open_Set_Module.objects.filter(unknown_sound=sound).exists():
			module += "1"
			modules += "OSM"
			osm_sounds = Open_Set_Module.objects.filter(unknown_sound=sound)
			if osm_sounds:
				for osm in osm_sounds:
					rowSubData[0] += str(osm.module_type)
					rowSubData[0] += ','
		else:
			rowSubData[0] += 'N,'
		row = [sound.sound_file.name.strip('cochlear/sound/'),sound.source.name, modules]
		context[ID]['rows'].append(row)
		context[ID]['rowData'].append([module])
		context[ID]['rowSubData'].append(rowSubData)

def loadSourceData(context):
	ID = 'sourceFileList'
	headerArr = ['Source Name','Number of attached files','Modules','Notes']
	dropDownHeaderArr = ['Module']
	dropDownArr = []
	dropDownArr.append(['Closed Set Text','Open Set'])
	subDropHeaderArr = ['Module Type']
	subDropArr = []
	subDropArr.append([CLOSED_SET_TEXT_TYPES,OPEN_SET_MODULE_TYPES])
	loadTableData(context, ID, headerArr, dropDownHeaderArr, dropDownArr, subDropHeaderArr, subDropArr)

	sourceFiles = Sound_Source.objects.all();
	for source in sourceFiles:
		rowSubData = [''] * len(context[ID]['dropDownHeaders'])
		
		module = ""
		modules = ""
		if Closed_Set_Text.objects.filter(unknown_sound__source=source).exists():
			module += "0"
			modules +="CST "
			cst_sources = Closed_Set_Text.objects.filter(unknown_sound__source=source)
			if cst_sources:
				for cst in cst_sources:
					rowSubData[0] += str(cst.module_type)
					rowSubData[0] += ','
		else:
			rowSubData[0] += 'N,'

		if Open_Set_Module.objects.filter(unknown_sound__source=source).exists():
			module += "1"
			modules += "OSM"
			osm_sources = Open_Set_Module.objects.filter(unknown_sound__source=source)
			if osm_sources:
				for osm in osm_sources:
					rowSubData[0] += str(osm.module_type)
					rowSubData[0] += ','
		else:
			rowSubData[0] += 'N,'
		numOfFiles = Sound.objects.filter(source=source).count();
		row = [source.name,numOfFiles, modules,source.notes]
		context[ID]['rows'].append(row)
		context[ID]['rowData'].append([module])
		context[ID]['rowSubData'].append(rowSubData)

def loadClosedSetTextData(context):
	ID = 'closedSetText'
	headerArr = ['Test Sound','# of choices']
	dropDownHeaderArr = ['Module Types']
	dropDownArr = []
	dropDownArr.append(CLOSED_SET_TEXT_TYPES)
	loadTableData(context, ID, headerArr, dropDownHeaderArr, dropDownArr, [], [])
	
	closedSetTexts = Closed_Set_Text.objects.all();
	for closedSetText in closedSetTexts:
		filename = closedSetText.unknown_speech.speech_file.name.strip('cochlear/speech') if closedSetText.unknown_speech else closedSetText.unknown_sound.sound_file.name.strip('cochlear/sound')
		row = [filename, closedSetText.text_choices.count()]
		context[ID]['rows'].append(row)
		data = [closedSetText.module_type]
		context[ID]['rowData'].append(data)

def loadOpenSetData(context):
	ID = 'openSet'
	headerArr = ['Test Sound','Answer','Keywords']
	dropDownHeaderArr = ['Module Types']
	dropDownArr = []
	dropDownArr.append(OPEN_SET_MODULE_TYPES)
	loadTableData(context, ID, headerArr, dropDownHeaderArr, dropDownArr, [], [])

	openSets = Open_Set_Module.objects.all();
	for openSet in openSets:
		filename = openSet.unknown_speech.speech_file.name.strip('cochlear/speech') if openSet.unknown_speech else openSet.unknown_sound.sound_file.name.strip('cochlear/sound')
		row = [filename, openSet.answer, openSet.key_words]
		context[ID]['rows'].append(row)
		context[ID]['rowData'].append([openSet.module_type])

def loadSpeakerIDData(context):
	ID = 'speakerid'
	headerArr = ['Test Sound','# of choices']
	loadTableData(context, ID, headerArr, [], [], [], [])

	questions = Speaker_ID.objects.all();
	for q in questions:
		row = [q.unknown_speech.speech_file.name.strip('cochlear/speech/'),q.choices.count()]
		context[ID]['rows'].append(row)

def loadDashboardData(context):
	loadSpeechData(context)
	loadSpeakerData(context)
	loadSoundData(context)
	loadSourceData(context)
	loadClosedSetTextData(context)
	loadOpenSetData(context)
	loadSpeakerIDData(context)
	context['csvOptions'] = [ 'All User Data', 'Speaker ID', '(Open Set) Meaningful Sentence',  '(Open Set) Anomalous Sentence',
	  '(Open Set) Word','(Open Set) Environmental', '(Open Set) Other', '(Closed Set Text) Phoneme', '(Closed Set Text) Environmental', '(Closed Set Text) Other']

def dashboard(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="index", navbarName='manager',activeLink="Manager Dashboard")

	loadDashboardData(context)

	userAttribObj = User_Attrib.objects.get(username=request.user.username)
	context['name'] = userAttribObj.first_name;
	#Just for fun, let's randomize the welcome message
	context['welcome_msg'] = random.choice(["Welcome","Hello","Howdy","What a fine day","Welcome back","Good to see you"])
	#Get the number of speech files and modules in the app
	context['file_number'] = Speech.objects.all().count();
	context['modules'] = Speaker_ID.objects.all().count();
	return render(request,'cochlear/manager_dashboard.html',context)

def closedsettextAdd(request):
	if request.method == 'POST':
		moduleNum = int(request.POST['moduleNum']) # Number of modules to be created
		for mn in range(1, moduleNum + 1):
			newCST = Closed_Set_Text()
			# indicate the type of closed set text
			newCST.module_type = int(request.POST['moduleType_' + str(mn)])
			# save so that we can edit the many to many field
			newCST.save()
			# Add a test sound or speech
			speechFile = request.POST['speechFile_' + str(mn)]
			soundFile = request.POST['soundFile_' + str(mn)]
			if (soundFile != ""):
				testSoundFile = ('cochlear/sound/' + soundFile)
				testSound =  Sound.objects.get(sound_file=testSoundFile)
				newCST.unknown_sound = testSound
			else:
				testSpeechFile = ('cochlear/speech/' + speechFile)
				testSpeech = Speech.objects.get(speech_file=testSpeechFile)
				newCST.unknown_speech = testSpeech
			# Add text choices
			textChoices = request.POST.getlist('textChoice_' + str(mn));
			first = True
			for textChoice in textChoices:
				if textChoice != "":
					if first:
						first = False
						obj, __ = Text_Choice.objects.get_or_create(text=textChoice)
						Closed_Set_Text_Choice(iscorrect = True, closed_set_text = newCST, choice = obj).save()
					else:
						obj, __ = Text_Choice.objects.get_or_create(text=textChoice)
						Closed_Set_Text_Choice(iscorrect = False, closed_set_text = newCST, choice = obj).save()
			newCST.save()
		return redirect('cochlear:closedsettextAdd') # prevent form resubmission of refresh

	context = NavigationBar.generateAppContext(request,app="cochlear",title="closedSetTextAdd",navbarName='manager')
	loadClosedSetTextData(context)
	context['text_choices'] = Text_Choice.objects.all()
	context['speech_choices'] = Speech.objects.all()
	context['sound_choices'] = Sound.objects.all()
	return render(request,'cochlear/closedsettextAdd.html',context)

def refreshClosedSetTextAdd(request):
	#Wrap dashboard data in json 
	context =  {}
	context['speechFileList'] = {}
	context['speechFileList']['Names'] = []
	speechFiles = Speech.objects.all()
	for speech in speechFiles:
		context['speechFileList']['Names'].append(str(speech))
	context['soundFileList'] = {}
	context['soundFileList']['Names'] = []
	sourceFiles = Sound.objects.all()
	for sound in sourceFiles:
		context['soundFileList']['Names'].append(str(sound))
	data = json.dumps(context)
	return HttpResponse(data, content_type='application/json')

def opensetAdd(request):
	if request.method == 'POST':
		moduleNum = int(request.POST['moduleNum']) # Number of modules to be created
		for mn in range(1, moduleNum + 1):
			newOSM = Open_Set_Module()
			# indicate the type of closed set text
			newOSM.module_type = int(request.POST['moduleType_' + str(mn)])
			# save so that we can edit the many to many field
			newOSM.save()
			# Add a test sound or speech
			speechFile = request.POST['speechFile_' + str(mn)]
			soundFile = request.POST['soundFile_' + str(mn)]
			if (soundFile != ""):
				testSoundFile = ('cochlear/sound/' + soundFile)
				testSound =  Sound.objects.get(sound_file=testSoundFile)
				newOSM.unknown_sound = testSound
			else:
				testSpeechFile = ('cochlear/speech/' + speechFile)
				testSpeech = Speech.objects.get(speech_file=testSpeechFile)
				newOSM.unknown_speech = testSpeech
			# Add answer
			newOSM.answer = request.POST['answer_' + str(mn)]
			newOSM.key_words = request.POST['keywords_' + str(mn)]
			newOSM.save()
		return redirect('cochlear:opensetAdd') # prevent form resubmission of refresh

	context = NavigationBar.generateAppContext(request,app="cochlear",title="opensetAdd",navbarName='manager')
	loadOpenSetData(context)
	context['speech_choices'] = Speech.objects.all()
	context['sound_choices'] = Sound.objects.all()
	return render(request,'cochlear/opensetAdd.html',context)

def speakeridAdd(request):
	if request.method == 'POST':
		moduleNum = int(request.POST['moduleNum']) # Number of modules to be created
		for mn in range(1, moduleNum + 1):
			newSID = Speaker_ID()
			# Add a test sound or speech
			speechFile = request.POST['unknownSpeech_' + str(mn)]
			testSpeechFile = ('cochlear/speech/' + speechFile)
			testSpeech = Speech.objects.get(speech_file=testSpeechFile)
			newSID.unknown_speech = testSpeech
			#save so we can add to manytomany field
			newSID.save()
			# Add text choices
			speechChoices = request.POST.getlist('speechChoice_' + str(mn));
			first = True
			for speechChoice in speechChoices:
				if speechChoice != "":
					speechChoiceFile = ('cochlear/speech/' + speechChoice)
					speechObj = Speech.objects.get(speech_file=speechChoiceFile)
					if first:
						first = False
						Speaker_ID_Choice(iscorrect = True, speaker_id = newSID, choice = speechObj).save()
					else:
						Speaker_ID_Choice(iscorrect = False,speaker_id = newSID, choice = speechObj).save()
			newSID.save()
		return redirect('cochlear:speakeridAdd') # prevent form resubmission of refresh

	context = NavigationBar.generateAppContext(request,app="cochlear",title="speakeridAdd",navbarName='manager')
	loadSpeakerIDData(context)
	context['speech_choices'] = Speech.objects.all()
	return render(request,'cochlear/speakeridAdd.html',context)

def refreshspeakeridAdd(request):
	#Wrap dashboard data in json 
	context =  {}
	context['speechFileList'] = {}
	context['speechFileList']['Names'] = []
	speechFiles = Speech.objects.all()
	for speech in speechFiles:
		context['speechFileList']['Names'].append(str(speech))
	data = json.dumps(context)
	return HttpResponse(data, content_type='application/json')

def analytics(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="index", navbarName='manager',activeLink="Analytics")
	return render(request,'cochlear/analytics.html',context)

######################
## Helper Functions ##
######################

# If the user started their first session of the week more than one week ago, set the current time
# as the beginning of their training week
def checkWeekProg(userObj):
	if (userObj.current_week_start_date == None) or (timezone.now() - userObj.current_week_start_date) > datetime.timedelta(days=7):
			userObj.current_week_start_date = timezone.now()
			userObj.save()

# Create user-specific objects for a given session
# We create user module data at the start of a session in case there is any data we
# want to gather as a module is being completed (time to complete a module, for example).
def createUserSessionData(sessionObj, userObj):
	newSession = User_Session(session = sessionObj, user = userObj, date_completed = None, modules_completed = 0)
	newSession.save()
	speaker_id_orders = Speaker_ID_Order.objects.filter(session = sessionObj)
	for speaker_id_order in speaker_id_orders:
		temp = User_Speaker_ID(user_attrib = userObj, speaker_id_order = speaker_id_order, repeat = False)
		temp.save()
	open_set_module_orders = Open_Set_Module_Order.objects.filter(session = sessionObj)
	for open_set_module_order in open_set_module_orders:
		temp = User_Open_Set_Module(user_attrib = userObj, open_set_module_order = open_set_module_order, repeat = False)
		temp.save()
	closed_set_text_orders = Closed_Set_Text_Order.objects.filter(session = sessionObj)
	for closed_set_text_order in closed_set_text_orders:
		temp = User_Closed_Set_Text(user_attrib = userObj, closed_set_text_order = closed_set_text_order, repeat = False)
		temp.save()

###################
## CSV downloads ##
###################

def appendTalkerID(rows):
	# Add Rows for the Talker Identification training module 
	rows.append(['Speaker Identification'])
	talkerIDHeaders = ['User','Session Week','Session Day', 'Repeat', 'Session Completed (Date)','Session Completed (Time)', 
		'Module Completed (Date)','Module Completed (Time)', 'Talker Identification ID', 'Test Sound Speaker', 'Test Sound File', 
		'Choices Speakers','Choices Files', 'User Response (Speaker)','User Response (File)', 'Correct']
	rows.append(talkerIDHeaders)
	talkerIDs = User_Speaker_ID.objects.filter(date_completed__isnull = False)
	for talkerID in talkerIDs:
		talkerIDRow = []
		talkerIDRow.append(talkerID.user_attrib.username)
		talkerIDRow.append(talkerID.speaker_id_order.session.week)
		talkerIDRow.append(talkerID.speaker_id_order.session.day)
		talkerIDRow.append(("yes" if talkerID.repeat else "no"))
		session = talkerID.speaker_id_order.session
		user = talkerID.user_attrib
		sessionDateTime = User_Session.objects.get(user = user, session = session).date_completed
		if sessionDateTime == None:
			talkerIDRow.append('NA')
			talkerIDRow.append('NA')
		else:
			sessionDateTime = str(sessionDateTime)
			sessionDate = sessionDateTime.split(' ')[0]
			sessionTime = sessionDateTime.split(' ')[1].split('.')[0]
			talkerIDRow.append(sessionDate)
			talkerIDRow.append(sessionTime)
		moduleDateTime = str(talkerID.date_completed)
		moduleDate = moduleDateTime.split(' ')[0]
		moduleTime = moduleDateTime.split(' ')[1].split('.')[0]
		talkerIDRow.append(moduleDate)
		talkerIDRow.append(moduleTime)
		module = talkerID.speaker_id_order.speaker_id
		talkerIDRow.append(module.id)
		testSoundSpeaker = module.unknown_speech.speaker.name
		talkerIDRow.append('NA') if (testSoundSpeaker == None) else talkerIDRow.append(testSoundSpeaker)
		talkerIDRow.append(module.unknown_speech.speech_file.name.strip('cochlear/speech/'))
		choicesSpeakers = ''
		choicesFiles = ''
		first = True
		for choice in module.choices.all():
			if first:
				first = False
				speakerName = choice.speaker.name
				choicesSpeakers += ('NA' if (speakerName == None) else  speakerName)
				choicesFiles += choice.speech_file.name.strip('cochlear/speech/')
			else:
				speakerName = choice.speaker.name
				choicesSpeakers += (", NA" if (speakerName == None) else (", " + choice.speaker.name))
				choicesFiles += ", " + choice.speech_file.name.strip('cochlear/speech/')
		talkerIDRow.append(choicesSpeakers)
		talkerIDRow.append(choicesFiles)
		speakerName = talkerID.user_response.speaker.name
		talkerIDRow.append('NA') if (speakerName == None) else talkerIDRow.append(speakerName) 
		talkerIDRow.append(talkerID.user_response.speech_file.name.strip('cochlear/speech/'))
		talkerIDRow.append('correct' if talkerID.correct else 'incorrect')
		rows.append(talkerIDRow)

def appendOpenSets(rows, openSets):
	openSetHeaders = ['User','Session Week','Session Day', 'Repeat', 'Session Completed (Date)','Session Completed (Time)', 
	'Module Completed (Date)','Module Completed (Time)', 'Test Sound (Speaker)', 'Test Sound (File)', 'Correct Answer', 'Key Words','User Response','Percent Correct']
	rows.append(openSetHeaders)
	for openSet in openSets:
		openSetRow = []
		openSetRow.append(openSet.user_attrib.username)
		openSetRow.append(openSet.open_set_module_order.session.week)
		openSetRow.append(openSet.open_set_module_order.session.day)
		openSetRow.append(("yes" if openSet.repeat else "no"))
		session = openSet.open_set_module_order.session
		user = openSet.user_attrib
		sessionDateTime = User_Session.objects.get(user = user, session = session).date_completed
		if sessionDateTime == None:
			openSetRow.append('NA')
			openSetRow.append('NA')
		else:
			sessionDateTime = str(sessionDateTime)
			sessionDate = sessionDateTime.split(' ')[0]
			sessionTime = sessionDateTime.split(' ')[1].split('.')[0]
			openSetRow.append(sessionDate)
			openSetRow.append(sessionTime)
		moduleDateTime = str(openSet.date_completed)
		moduleDate = moduleDateTime.split(' ')[0]
		moduleTime = moduleDateTime.split(' ')[1].split('.')[0]
		openSetRow.append(moduleDate)
		openSetRow.append(moduleTime)
		module = openSet.open_set_module_order.open_set_module
		speakerName = module.unknown_speech.speaker.name
		openSetRow.append('NA' if (speakerName == None) else speakerName)
		openSetRow.append(module.unknown_speech.speech_file.name.strip('cochlear/speech/'))
		openSetRow.append(module.answer)
		openSetRow.append(module.key_words)
		openSetRow.append(openSet.user_response)
		openSetRow.append(openSet.percent_correct)
		rows.append(openSetRow)

def appendClosedSetTexts(rows, closedSetTexts):
	# Add Rows for the Talker Identification training module 
	closedSetTextHeaders = ['User','Session Week','Session Day', 'Repeat', 'Session Completed (Date)','Session Completed (Time)', 
		'Module Completed (Date)','Module Completed (Time)', 'Closed Set Text ID', 'Test Sound Source', 'Test Sound File', 
		'Choices', 'User Response', 'Correct']
	rows.append(closedSetTextHeaders)
	for closedSetText in closedSetTexts:
		closedSetTextRow = []
		closedSetTextRow.append(closedSetText.user_attrib.username)
		closedSetTextRow.append(closedSetText.closed_set_text_order.session.week)
		closedSetTextRow.append(closedSetText.closed_set_text_order.session.day)
		closedSetTextRow.append(("yes" if closedSetText.repeat else "no"))
		session = closedSetText.closed_set_text_order.session
		user = closedSetText.user_attrib
		sessionDateTime = User_Session.objects.get(user = user, session = session).date_completed
		if sessionDateTime == None:
			closedSetTextRow.append('NA')
			closedSetTextRow.append('NA')
		else:
			sessionDateTime = str(sessionDateTime)
			sessionDate = sessionDateTime.split(' ')[0]
			sessionTime = sessionDateTime.split(' ')[1].split('.')[0]
			closedSetTextRow.append(sessionDate)
			closedSetTextRow.append(sessionTime)
		moduleDateTime = str(closedSetText.date_completed)
		moduleDate = moduleDateTime.split(' ')[0]
		moduleTime = moduleDateTime.split(' ')[1].split('.')[0]
		closedSetTextRow.append(moduleDate)
		closedSetTextRow.append(moduleTime)
		module = closedSetText.closed_set_text_order.closed_set_text
		closedSetTextRow.append(module.id)
		if module.unknown_speech:
			testSoundSource = module.unknown_speech.speaker.name
			closedSetTextRow.append(testSoundSource)
			closedSetTextRow.append(module.unknown_speech.speech_file.name.strip('cochlear/speech/'))
		elif module.unknown_sound:
			testSoundSource = module.unknown_sound.source.name
			closedSetTextRow.append(testSoundSource)
			closedSetTextRow.append(module.unknown_sound.sound_file.name.strip('cochlear/sound/'))
		else:
			testSoundSource = 'NA'
			closedSetTextRow.append(testSoundSource)
			closedSetTextRow.append('NA')
		textChoices = ''
		first = True
		for choice in module.text_choices.all():
			if first:
				first = False
				textChoices += choice.text
			else:
				textChoices += ", " + choice.text
		closedSetTextRow.append(textChoices)
		closedSetTextRow.append(closedSetText.user_response.text) 
		closedSetTextRow.append('correct' if closedSetText.correct else 'incorrect')
		rows.append(closedSetTextRow)

class Echo(object):
	# An object that implements just the write method of the file-like interface.
	def write(self, value):
		# Write the value by returning it, instead of storing in a buffer.
		return value

def getUserDataCSV(request,subset):
	# A view that streams a large CSV file.
	# Documentation: https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
	rows = []
	subset = int(subset)
	if subset == 0:
		appendTalkerID(rows)
		rows.append([]) #skip a line in the csv file

		rows.append(['Meaningful (Open Set)'])
		openSets = User_Open_Set_Module.objects.filter(open_set_module_order__open_set_module__module_type = 1, date_completed__isnull = False)
		appendOpenSets(rows, openSets)
		rows.append([])
		
		rows.append(['Anomalous (Open Set)'])
		openSets = User_Open_Set_Module.objects.filter(open_set_module_order__open_set_module__module_type = 2, date_completed__isnull = False)
		appendOpenSets(rows, openSets)
		rows.append([])

		rows.append(['Word (Open Set)'])
		openSets = User_Open_Set_Module.objects.filter(open_set_module_order__open_set_module__module_type = 3, date_completed__isnull = False)
		appendOpenSets(rows, openSets)
		rows.append([])

		rows.append(['Environmental (Open Set)'])
		openSets = User_Open_Set_Module.objects.filter(open_set_module_order__open_set_module__module_type = 4, date_completed__isnull = False)
		appendOpenSets(rows, openSets)
		rows.append([])

		rows.append(['Other (Open Set)'])
		openSets = User_Open_Set_Module.objects.filter(open_set_module_order__open_set_module__module_type = 0, date_completed__isnull = False)
		appendOpenSets(rows, openSets)

		rows.append(['Phoneme (Closed Set Text)'])
		closedSetTexts = User_Closed_Set_Text.objects.filter(closed_set_text_order__closed_set_text__module_type = 1, date_completed__isnull = False)
		appendClosedSetTexts(rows, closedSetTexts)

		rows.append(['Environmental (Closed Set Text)'])
		closedSetTexts = User_Closed_Set_Text.objects.filter(closed_set_text_order__closed_set_text__module_type = 2, date_completed__isnull = False)
		appendClosedSetTexts(rows, closedSetTexts)

		rows.append(['Other (Closed Set Text)'])
		closedSetTexts = User_Closed_Set_Text.objects.filter(closed_set_text_order__closed_set_text__module_type = 0, date_completed__isnull = False)
		appendClosedSetTexts(rows, closedSetTexts)

		pseudo_buffer = Echo()
		writer = csv.writer(pseudo_buffer)
		response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
		filename = "CI_Training_All_User_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"

	elif subset == 1:
		appendTalkerID(rows)
		pseudo_buffer = Echo()
		writer = csv.writer(pseudo_buffer)
		response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
		filename = "CI_Training_Speaker_ID_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"

	elif subset == 2:
		rows.append(['Meaningful (Open Set)'])
		openSets = User_Open_Set_Module.objects.filter(open_set_module_order__open_set_module__module_type = 1, date_completed__isnull = False)
		appendOpenSets(rows, openSets)

		pseudo_buffer = Echo()
		writer = csv.writer(pseudo_buffer)
		response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
		filename = "CI_Training_OpenSet_Meaningful_Sentence_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"

	elif subset == 3:
		rows.append(['Anomalous (Open Set)'])
		openSets = User_Open_Set_Module.objects.filter(open_set_module_order__open_set_module__module_type = 2, date_completed__isnull = False)
		appendOpenSets(rows, openSets)

		pseudo_buffer = Echo()
		writer = csv.writer(pseudo_buffer)
		response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
		filename = "CI_Training_OpenSet_Anomalous_Sentence_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	elif subset == 4:
		rows.append(['Word (Open Set)'])
		openSets = User_Open_Set_Module.objects.filter(open_set_module_order__open_set_module__module_type = 3, date_completed__isnull = False)
		appendOpenSets(rows, openSets)

		pseudo_buffer = Echo()
		writer = csv.writer(pseudo_buffer)
		response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
		filename = "CI_Training_OpenSet_Word_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	elif subset == 5:
		rows.append(['Environmental (Open Set)'])
		openSets = User_Open_Set_Module.objects.filter(open_set_module_order__open_set_module__module_type = 4, date_completed__isnull = False)
		appendOpenSets(rows, openSets)
		
		pseudo_buffer = Echo()
		writer = csv.writer(pseudo_buffer)
		response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
		filename = "CI_Training_OpenSet_Environmental_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	elif subset == 6:
		rows.append(['Other (Open Set)'])
		openSets = User_Open_Set_Module.objects.filter(open_set_module_order__open_set_module__module_type = 0, date_completed__isnull = False)
		appendOpenSets(rows, openSets)

		pseudo_buffer = Echo()
		writer = csv.writer(pseudo_buffer)
		response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
		filename = "CI_Training_OpenSet_Other_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
		response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	elif subset == 7:
		rows.append(['Phoneme (Closed Set Text)'])
		closedSetTexts = User_Closed_Set_Text.objects.filter(closed_set_text_order__closed_set_text__module_type = 1, date_completed__isnull = False)
		appendClosedSetTexts(rows, closedSetTexts)

		pseudo_buffer = Echo()
		writer = csv.writer(pseudo_buffer)
		response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
		filename = "CI_Training_ClosedSetText_Phoneme_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	elif subset == 8:
		rows.append(['Environmental (Closed Set Text)'])
		closedSetTexts = User_Closed_Set_Text.objects.filter(closed_set_text_order__closed_set_text__module_type = 2, date_completed__isnull = False)
		appendClosedSetTexts(rows, closedSetTexts)

		pseudo_buffer = Echo()
		writer = csv.writer(pseudo_buffer)
		response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
		filename = "CI_Training_ClosedSetText_Environmental_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	elif subset == 9:
		rows.append(['Other (Closed Set Text)'])
		closedSetTexts = User_Closed_Set_Text.objects.filter(closed_set_text_order__closed_set_text__module_type = 0, date_completed__isnull = False)
		appendClosedSetTexts(rows, closedSetTexts)

		pseudo_buffer = Echo()
		writer = csv.writer(pseudo_buffer)
		response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
		filename = "CI_Training_ClosedSetText_Other_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"

	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response