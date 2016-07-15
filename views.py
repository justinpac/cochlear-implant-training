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
CLOSED_SET_TEXT_TYPES = ['Other','Phoneme','Environmental']
OPEN_SET_TYPES = ['Other','Meaningful Sentence','Anomalous Sentence','Word','Environmental']

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

def loadSpeechData(context):
	#Putting all the loading of the data in a separate function so it can be done asynchronously 
	#Sound files
	context['speechFileList'] = {}
	context['speechFileList']['headers'] = ['Filename','Speaker Name','Date Uploaded']
	context['speechFileList']['rows'] = []
	context['speechFileList']['id'] = 'speechfiles'
	context['speechFileList']['colSize'] = int(12/len(context['speechFileList']['headers']))
	soundFiles = Speech.objects.all();
	for sound in soundFiles:
		if(sound.speaker == None):
			speaker_name = "No Speaker"
		else:
			speaker_name = sound.speaker.name
		row = [sound.speech_file.name.strip('cochlear/speech/'), speaker_name,str(sound.uploaded_date)]
		context['speechFileList']['rows'].append(row)

def loadClosedSetTextData(context):
	context['closedSetText'] = {}
	context['closedSetText']['headers'] = ['Test Sound','# of choices']
	context['closedSetText']['rows'] = []
	context['closedSetText']['id'] = 'closedsettext'
	context['closedSetText']['colSize'] = int(12/len(context['closedSetText']['headers']))
	context['closedSetText']['moduleTypes'] = CLOSED_SET_TEXT_TYPES
	context['closedSetText']['rowModuleTypes'] = []
	closedSetTexts = Closed_Set_Text.objects.all();
	for closedSetText in closedSetTexts:
		filename = closedSetText.unknown_speech.speech_file.name.strip('cochlear/speech') if closedSetText.unknown_speech else closedSetText.unknown_sound.sound_file.name.strip('cochlear/sound')
		row = [filename, closedSetText.text_choices.count()]
		context['closedSetText']['rows'].append(row)
		context['closedSetText']['rowModuleTypes'].append(closedSetText.module_type)

def loadOpenSetData(context):
	context['openSet'] = {}
	context['openSet']['headers'] = ['Test Sound','Answer','Keywords']
	context['openSet']['rows'] = []
	context['openSet']['id'] = 'openset'
	context['openSet']['colSize'] = int(12/len(context['openSet']['headers']))
	context['openSet']['moduleTypes'] = OPEN_SET_TYPES
	context['openSet']['rowModuleTypes'] = []
	openSets = Open_Set_Module.objects.all();
	for openSet in openSets:
		filename = openSet.unknown_speech.speech_file.name.strip('cochlear/speech') if openSet.unknown_speech else openSet.unknown_sound.sound_file.name.strip('cochlear/sound')
		row = [filename, openSet.answer, openSet.key_words]
		context['openSet']['rows'].append(row)
		context['openSet']['rowModuleTypes'].append(openSet.module_type)

def loadDashboardData(context):
	loadSpeechData(context)
	loadClosedSetTextData(context)
	loadOpenSetData(context)

	#Speaker objects
	context['speakerFileList'] = {}
	context['speakerFileList']['headers'] = ['Speaker Name','Number of attached files']
	context['speakerFileList']['rows'] = []
	context['speakerFileList']['id'] = 'speakerfiles'
	context['speakerFileList']['colSize'] = int(12/len(context['speakerFileList']['headers']))
	speakerList = Speaker.objects.all();
	for speaker in speakerList:
		numOfFiles = Speech.objects.filter(speaker=speaker).count();
		row = [speaker.name,numOfFiles]
		context['speakerFileList']['rows'].append(row)

	#Closed set questions
	context['closedQuestions'] = {}
	context['closedQuestions']['headers'] = ['Test Sound','# of choices']
	context['closedQuestions']['rows'] = []
	context['closedQuestions']['id'] = 'closedquestions'
	context['closedQuestions']['colSize'] = int(12/len(context['closedQuestions']['headers']))
	questions = Speaker_ID.objects.all();
	for q in questions:
		row = [q.unknown_speech.speech_file.name.strip('cochlear/speech/'),q.choices.count()]
		context['closedQuestions']['rows'].append(row)

	#Open set questions

	#Session objects

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
	soundFiles = Sound.objects.all()
	for sound in soundFiles:
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

def getAllUserDataCSV(request):
	# A view that streams a large CSV file.
	# Documentation: https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
	rows = []
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
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response

def talkerIDCSV(request):
	# A view that streams a large CSV file.
	# Documentation: https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
	rows = []
	appendTalkerID(rows)

	pseudo_buffer = Echo()
	writer = csv.writer(pseudo_buffer)
	response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
	filename = "CI_Training_Speaker_ID_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response

def otherCSV(request):
	# A view that streams a large CSV file.
	# Documentation: https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
	rows = []
	rows.append(['Other (Open Set)'])
	openSets = User_Open_Set_Module.objects.filter(open_set_module_order__open_set_module__module_type = 0, date_completed__isnull = False)
	appendOpenSets(rows, openSets)

	pseudo_buffer = Echo()
	writer = csv.writer(pseudo_buffer)
	response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
	filename = "CI_Training_OpenSet_Other_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response

def meaningfulCSV(request):
	# A view that streams a large CSV file.
	# Documentation: https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
	rows = []
	rows.append(['Meaningful (Open Set)'])
	openSets = User_Open_Set_Module.objects.filter(open_set_module_order__open_set_module__module_type = 1, date_completed__isnull = False)
	appendOpenSets(rows, openSets)

	pseudo_buffer = Echo()
	writer = csv.writer(pseudo_buffer)
	response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
	filename = "CI_Training_OpenSet_Meaningful_Sentence_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response

def anomalousCSV(request):
	# A view that streams a large CSV file.
	# Documentation: https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
	rows = []
	rows.append(['Anomalous (Open Set)'])
	openSets = User_Open_Set_Module.objects.filter(open_set_module_order__open_set_module__module_type = 2, date_completed__isnull = False)
	appendOpenSets(rows, openSets)

	pseudo_buffer = Echo()
	writer = csv.writer(pseudo_buffer)
	response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
	filename = "CI_Training_OpenSet_Anomalous_Sentence_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response

def wordCSV(request):
	# A view that streams a large CSV file.
	# Documentation: https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
	rows = []
	rows.append(['Word (Open Set)'])
	openSets = User_Open_Set_Module.objects.filter(open_set_module_order__open_set_module__module_type = 3, date_completed__isnull = False)
	appendOpenSets(rows, openSets)

	pseudo_buffer = Echo()
	writer = csv.writer(pseudo_buffer)
	response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
	filename = "CI_Training_OpenSet_Word_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response

def environmentalCSV(request):
	# A view that streams a large CSV file.
	# Documentation: https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
	rows = []
	rows.append(['Environmental (Open Set)'])
	openSets = User_Open_Set_Module.objects.filter(open_set_module_order__open_set_module__module_type = 4, date_completed__isnull = False)
	appendOpenSets(rows, openSets)

	pseudo_buffer = Echo()
	writer = csv.writer(pseudo_buffer)
	response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
	filename = "CI_Training_OpenSet_Environmental_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response

def cstOtherCSV(request):
	# A view that streams a large CSV file.
	# Documentation: https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
	rows = []
	rows.append(['Other (Closed Set Text)'])
	closedSetTexts = User_Closed_Set_Text.objects.filter(closed_set_text_order__closed_set_text__module_type = 0, date_completed__isnull = False)
	appendClosedSetTexts(rows, closedSetTexts)

	pseudo_buffer = Echo()
	writer = csv.writer(pseudo_buffer)
	response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
	filename = "CI_Training_ClosedSetText_Other_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response

def cstPhonemeCSV(request):
	# A view that streams a large CSV file.
	# Documentation: https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
	rows = []
	rows.append(['Phoneme (Closed Set Text)'])
	closedSetTexts = User_Closed_Set_Text.objects.filter(closed_set_text_order__closed_set_text__module_type = 1, date_completed__isnull = False)
	appendClosedSetTexts(rows, closedSetTexts)

	pseudo_buffer = Echo()
	writer = csv.writer(pseudo_buffer)
	response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
	filename = "CI_Training_ClosedSetText_Phoneme_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response

def cstEnvironmentalCSV(request):
	# A view that streams a large CSV file.
	# Documentation: https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
	rows = []
	rows.append(['Environmental (Closed Set Text)'])
	closedSetTexts = User_Closed_Set_Text.objects.filter(closed_set_text_order__closed_set_text__module_type = 2, date_completed__isnull = False)
	appendClosedSetTexts(rows, closedSetTexts)

	pseudo_buffer = Echo()
	writer = csv.writer(pseudo_buffer)
	response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
	filename = "CI_Training_ClosedSetText_Environmental_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response