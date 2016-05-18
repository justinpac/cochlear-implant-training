from django.shortcuts import render,redirect
from django.http import HttpResponse
import json, datetime, logging

# We need this to generate the navbar
from hipercore.helpers import NavigationBar

# Import our database models
from cochlear.models import *

#Some helper functions
import cochlear.util

#Get django timezone utility
from django.utils import timezone
import random #To generate random numbers

SESSION_CAP = 4

def index(request):
	#If user is manager, redirect to the manager dashboard (so the homepage always takes the manager to their dasboard)
	permission = cochlear.util.GetUserPermission(request.user.username);
	if(permission > 0):
		return redirect('cochlear:dashboard')
	#Render a basic page
	context = NavigationBar.generateAppContext(request,app="cochlear",title="index", navbarName=0)
	userList = User_Attrib.objects.filter(username=request.user.username)
	context['name'] = userList[0].first_name
	currentTime = timezone.now();
	oneWeekAgo = currentTime - datetime.timedelta(days=7);
	context['sessions'] = User_Session.objects.filter(user=userList[0].id, date_completed__range=(oneWeekAgo,currentTime)).count()
	context['percentComplete'] = str(context['sessions'] * 25)
	#Indicate if there is an active session
	active_session = User_Session.objects.filter(date_completed=None)
	if not active_session:
		context['activeSessionFlag'] = False
	else:
		context['activeSessionFlag'] = True
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

def speaker(request, speaker_module, repeatFlag):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="speaker", navbarName=0)
	userObj = User_Attrib.objects.get(username=request.user.username)
	module = Closed_Set_Train.objects.get(id=speaker_module)
	context['test_sound'] = module.test_sound
	context['speaker_choices'] = module.choices.all().order_by('?')
	context['speaker_module_id'] = module.id
	context['user_attrib_id'] = userObj.id
	context['repeatFlag'] = repeatFlag

	return render(request,'cochlear/speaker.html',context)

def openSet(request, open_set_module, repeatFlag):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="openSet", navbarName=0)
	user_attrib = User_Attrib.objects.get(username=request.user.username)
	module = Open_Set_Train.objects.get(id=open_set_module)
	context['test_sound'] = module.test_sound.speech_file.url
	context['correctAnswer'] = module.answer
	context['repeatFlag'] = repeatFlag
	context['open_set_module_id'] = open_set_module
	context['user_attrib_id'] = user_attrib.id
	if (module.type_train == 2):
		context['typeOfSpeech'] = "word"
	else:
		context['typeOfSpeech'] = "sentence"
	return render(request,'cochlear/openSet.html',context)

#############################
## Views Without Templates ##
#############################

def startNewSession(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="startNewSession", navbarName=0)
	userObj = User_Attrib.objects.filter(username=request.user.username).first()
	user_sessions = User_Session.objects.filter(user = userObj.id)

	#If the user has not completed any sessions, then they are on the session for week 1, day 1
	if not user_sessions:
		week1Day1 = Session.objects.get(week = 1, day = 1)
		newSession = User_Session(session = week1Day1,user = userObj, date_completed = None, modules_completed = 0)
		newSession.save()
		return goToModule(week1Day1, 1)

	#Get the max session day and week that the user has completed
	maxWeekComplete = 0;
	maxDayComplete = 0;
	for user_session in user_sessions:
		day = user_session.session.day
		week = user_session.session.week
		if (day > maxDayComplete):
			maxDayComplete = day
		if (week > maxWeekComplete):
			maxWeekComplete = week

	# Get the next session the user needs to complete
	nextSession = Session.objects.filter(week = (maxWeekComplete), day = (maxDayComplete + 1))
	if not nextSession: 
		# Either the next session is on a new week or there are no sessions left for the user to complete
		nextSession = Session.objects.filter(week = (maxWeekComplete + 1), day = 1)
		if not nextSession:
			return redirect('cochlear:trainingEndPage')
	
	# Go to the first module of the next session
	nextSession = nextSession.first()
	newSession = User_Session(session = nextSession, user = userObj, date_completed = None, modules_completed = 0)
	newSession.save()
	return goToModule(nextSession, 1)

def goToNextModule(request):
	userObj = User_Attrib.objects.get(username=request.user.username)
	user_session = User_Session.objects.get(user = userObj.id, date_completed = None)
	if user_session.modules_completed == user_session.session.countModules():
		user_session.date_completed = timezone.now()
		user_session.save()
		return redirect('cochlear:sessionEndPage')
	nextModule = user_session.modules_completed + 1
	return goToModule(user_session.session, nextModule)

##################
## Ajax methods ##
##################

def uploadSound(request):
	if(request.method == "POST"):#If the user has submitted something, Handle the upload
		speakerID = int(request.POST['speaker_id']);
		rawFile = request.FILES['file'];
		#If the speaker doesn't exist, create it
		if(speakerID == -1):
			#Check if it's just been created
			speakerList = Speaker.objects.filter(name=request.POST['speaker_name']);
			if(len(speakerList) == 0):
				newSpeaker = Speaker();
				newSpeaker.name=request.POST['speaker_name']
				newSpeaker.save();
				speakerID = newSpeaker.pk;
			else:
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

def moduleCompleted(request):
	userList = User_Attrib.objects.filter(username=request.user.username)
	user = userList[0]
	user_session = User_Session.objects.get(user=user.id, date_completed=None)
	user_session.modules_completed += 1
	user_session.save()
	return HttpResponse("Success")

def getSpeakers(request,name):
	#Gets a list of authors whose names start with 'name'
	speakerList = Speaker.objects.filter(name__istartswith=name)
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

###################
## Manager Pages ##
###################

#NOTE: Make sure to add the names of all the pages that should only be accessible
#by managers in middleware.py

def getDashboardData(request):
	#Wrap dashboard data in json 
	ctx =  {}
	loadDashboardData(ctx)
	data = json.dumps(ctx)
	return HttpResponse(data, content_type='application/json')

def loadDashboardData(context):
	#Putting all the loading of the data in a seperate function so it can be done asynchronously 
	#Sound files
	context['soundFileList'] = {}
	context['soundFileList']['headers'] = ['Filename','Speaker Name','Date Uploaded']
	context['soundFileList']['rows'] = []
	context['soundFileList']['id'] = 'soundfiles'
	context['soundFileList']['colSize'] = int(12/len(context['soundFileList']['headers']))
	soundFiles = Speech.objects.all();
	for sound in soundFiles:
		row = [sound.speech_file.name,sound.speaker.name,str(sound.uploaded_date)]
		context['soundFileList']['rows'].append(row)

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
	context['closedQuestions']['headers'] = ['Filename','Speaker Name','Date Uploaded']
	context['closedQuestions']['rows'] = []
	context['closedQuestions']['id'] = 'closedquestions'
	context['closedQuestions']['colSize'] = int(12/len(context['closedQuestions']['headers']))
	soundFiles = Speech.objects.all();
	for sound in soundFiles:
		row = [sound.speech_file.name,sound.speaker.name,str(sound.uploaded_date)]
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
	context['modules'] = Closed_Set_Train.objects.all().count();
	return render(request,'cochlear/manager_dashboard.html',context)

def new_sound(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="new_sound", navbarName='manager',activeLink="Manager Dashboard")
	return render(request,'cochlear/new_sound.html',context)

def new_module(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="new_module", navbarName='manager',activeLink="Manager Dashboard")

	return render(request,'cochlear/new_module.html',context)

def analytics(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="index", navbarName='manager',activeLink="Analytics")
	return render(request,'cochlear/analytics.html',context)

######################
## Helper Functions ##
######################

# Get a module in a particular session based on its order in sequence (moduleNum)
# This is in a separate function because it will be used in multiple contexts and
# continue to grow with the number of modules
def goToModule(session, moduleNum):
	module = session.closed_set_trains.filter(closed_set_train_order__order = moduleNum)
	if not module:
		module = session.open_set_trains.filter(open_set_train_order__order = moduleNum)
		return redirect('cochlear:openSet', open_set_module=module.first().id, repeatFlag = 0)
	return redirect('cochlear:speaker', speaker_module=module.first().id, repeatFlag = 0)
#		module = session.open_set_trains.get(orderInSession=moduleNum)
