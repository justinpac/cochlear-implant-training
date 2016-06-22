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

#For genereating csv files
import csv
from django.utils.six.moves import range
from django.http import StreamingHttpResponse


SESSION_CAP = 4

def index(request):
	#If user is manager, redirect to the manager dashboard (so the homepage always takes the manager to their dasboard)
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

# Render the speaker identification page
def speaker(request, speaker_module, repeatFlag, order_id):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="speaker", navbarName=0)
	userObj = User_Attrib.objects.get(username=request.user.username)
	module = Closed_Set_Train.objects.get(id=speaker_module)
	context['test_sound'] = module.test_sound
	context['speaker_choices'] = module.choices.all().order_by('?')
	context['speaker_module_id'] = module.id
	context['user_attrib_id'] = userObj.id
	context['repeatFlag'] = repeatFlag
	context['order_id'] = order_id

	return render(request,'cochlear/speaker.html',context)

#Render a generic page for a closed-set module
def openSet(request, open_set_module, repeatFlag, order_id):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="openSet", navbarName=0)
	user_attrib = User_Attrib.objects.get(username=request.user.username)
	module = Open_Set_Train.objects.get(id=open_set_module)
	context['test_sound'] = module.test_sound.speech_file.url
	context['correctAnswer'] = module.answer
	context['keyWords'] = module.key_words
	context['typeTrain'] = module.type_train
	context['repeatFlag'] = repeatFlag
	context['order_id'] = order_id
	context['open_set_module_id'] = open_set_module
	context['user_attrib_id'] = user_attrib.id

	return render(request,'cochlear/openSet.html',context)

#############################
## Views Without Templates ##
#############################

def startNewSession(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="startNewSession", navbarName=0)
	userObj = User_Attrib.objects.get(username=request.user.username)
	user_sessions = User_Session.objects.filter(user = userObj)

	#If the user has not completed any sessions, then they are on the session for week 1, day 1
	if not user_sessions:
		checkWeekProg(userObj)
		week1Day1 = Session.objects.get(week = 1, day = 1)
		createUserSessionData(week1Day1, userObj)
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
			# We want this date to change the next time there is actually another session to complete, so no call to checkWeekProg
			return redirect('cochlear:trainingEndPage')
	
	# Go to the first module of the next session
	nextSession = nextSession.first()
	
	#Create user-specific objects for this session
	createUserSessionData(nextSession, userObj)

	checkWeekProg(userObj)

	return goToModule(nextSession, 1)

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

def openSetCompleted(request):
	userList = User_Attrib.objects.filter(username=request.user.username)
	user = userList[0]
	#Get some information passed in from the template
	isRepeat = bool(int(request.POST['isRepeat']))
	user_response = request.POST['user_response']
	open_set_train_order = Open_Set_Train_Order.objects.get(id = int(request.POST['order_id']))
	percentCorrect = int(request.POST['percentCorrect'])

	if(not isRepeat):
		# If this module is not being repeated, then we want to edit the existing User_Open Set_Train record
		moduleHist = User_Open_Set_Train.objects.get(open_set_train_order = open_set_train_order, user_attrib = user, repeat = False)
		if (moduleHist.date_completed == None):
			# Indicate the user has completed another module within the session. Tracked in User_Session and User_Open_Set_Train
			user_session = User_Session.objects.get(user=user.id, date_completed=None)
			user_session.modules_completed += 1
			user_session.save()
			moduleHist.date_completed = timezone.now()
			moduleHist.user_response = user_response
			moduleHist.percent_correct = percentCorrect
	else:
		# if this module IS being repeated, then create a new User_Open_Set_Train
		moduleHist = User_Open_Set_Train(open_set_train_order = open_set_train_order, user_attrib = user, repeat = True, 
			date_completed = timezone.now(), user_response = user_response, percent_correct=percentCorrect)
	
	moduleHist.save()
	return HttpResponse("Success")

def isCorrect(request):
	closedSetTrain = Closed_Set_Train.objects.get(id = int(request.GET['module_id']))
	speech = Speech.objects.get(id = int(request.GET['speech_id']))
	iscorrect = Closed_Set_Question_Answer.objects.get(question = closedSetTrain, answer = speech).iscorrect
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
	closed_set_train_order = Closed_Set_Train_Order.objects.get(id = int(request.POST['order_id']))

	if(not isRepeat):
		# If this module is not being repeated, then we want to edit the existing User_Closed Set_Train record
		moduleHist = User_Closed_Set_Train.objects.get(closed_set_train_order = closed_set_train_order, user_attrib = user, repeat = False)
		if(moduleHist.date_completed == None):
			# Indicate the user has completed another module within the session. Tracked in User_Session and User_Closed_Set_Train
			user_session = User_Session.objects.get(user=user.id, date_completed=None)
			user_session.modules_completed += 1
			user_session.save()
			moduleHist.date_completed = timezone.now()
			moduleHist.user_response = user_response
			moduleHist.correct = answered_correctly
	else:
		# if this module IS being repeated, then create a new User_Closed_Set_Train
		moduleHist = User_Closed_Set_Train(closed_set_train_order = closed_set_train_order, user_attrib = user, repeat = True, date_completed = timezone.now(), 
			user_response = user_response, correct = answered_correctly)

	moduleHist.save()
	return HttpResponse("Success")

def getDashboardData(request):
	#Wrap dashboard data in json 
	ctx =  {}
	loadDashboardData(ctx)
	data = json.dumps(ctx)
	return HttpResponse(data, content_type='application/json')

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
	newSpeaker.save();
	return HttpResponse("Success")

###################
## Manager Pages ##
###################

#NOTE: Make sure to add the names of all the pages that should only be accessible
#by managers in middleware.py

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
		if(sound.speaker == None):
			speaker_name = "No Speaker"
		else:
			speaker_name = sound.speaker.name
		row = [sound.speech_file.name.strip('cochlear/speech/'), speaker_name,str(sound.uploaded_date)]
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
	context['closedQuestions']['headers'] = ['Test Sound','# of choices']
	context['closedQuestions']['rows'] = []
	context['closedQuestions']['id'] = 'closedquestions'
	context['closedQuestions']['colSize'] = int(12/len(context['closedQuestions']['headers']))
	questions = Closed_Set_Train.objects.all();
	for q in questions:
		row = [q.test_sound.speech_file.name.strip('cochlear/speech/'),q.choices.count()]
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

# If the user started their first session of the week more than one week ago, set the current time
# as the beginning of their training week
def checkWeekProg(userObj):
	if (userObj.current_week_start_date == None) or (timezone.now() - userObj.current_week_start_date) > datetime.timedelta(days=7):
			userObj.current_week_start_date = timezone.now()
			userObj.save()

# Get a module in a particular session based on its order in sequence (moduleNum)
# This is in a separate function because it will be used in multiple contexts and
# continue to grow with the number of modules
def goToModule(session, moduleNum):
	module = session.closed_set_trains.filter(closed_set_train_order__order = moduleNum)
	if not module:
		module = session.open_set_trains.filter(open_set_train_order__order = moduleNum)
		order_id = Open_Set_Train_Order.objects.all().get(session = session, order = moduleNum).id
		return redirect('cochlear:openSet', open_set_module=module.first().id, repeatFlag = 0, order_id = order_id)
	order_id = Closed_Set_Train_Order.objects.all().get(session = session, order = moduleNum).id
	return redirect('cochlear:speaker', speaker_module=module.first().id, repeatFlag = 0, order_id = order_id)

# Create user-specific objects for a given session
def createUserSessionData(sessionObj, userObj):
	newSession = User_Session(session = sessionObj, user = userObj, date_completed = None, modules_completed = 0)
	newSession.save()
	closed_set_train_orders = Closed_Set_Train_Order.objects.filter(session = sessionObj)
	for closed_set_train_order in closed_set_train_orders:
		temp = User_Closed_Set_Train(user_attrib = userObj, closed_set_train_order = closed_set_train_order, repeat = False)
		temp.save()
	open_set_train_orders = Open_Set_Train_Order.objects.filter(session = sessionObj)
	for open_set_train_order in open_set_train_orders:
		temp = User_Open_Set_Train(user_attrib = userObj, open_set_train_order = open_set_train_order, repeat = False)
		temp.save()

###################
## CSV downloads ##
###################

def appendTalkerID(rows):
	# Add Rows for the Talker Identification training module 
	rows.append(['Talker Identification'])
	talkerIDHeaders = ['User','Session Week','Session Day', 'Repeat', 'Session Completed (Date)','Session Completed (Time)', 
		'Module Completed (Date)','Module Completed (Time)', 'Talker Identification ID', 'Test Sound Speaker', 'Test Sound File', 
		'Choices Speakers','Choices Files', 'User Response (Speaker)','User Response (File)', 'Correct']
	rows.append(talkerIDHeaders)
	talkerIDs = User_Closed_Set_Train.objects.filter(date_completed__isnull = False)
	for talkerID in talkerIDs:
		talkerIDRow = []
		talkerIDRow.append(talkerID.user_attrib.username)
		talkerIDRow.append(talkerID.closed_set_train_order.session.week)
		talkerIDRow.append(talkerID.closed_set_train_order.session.day)
		talkerIDRow.append(("yes" if talkerID.repeat else "no"))
		session = talkerID.closed_set_train_order.session
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
		module = talkerID.closed_set_train_order.closed_set_train
		talkerIDRow.append(module.id)
		testSoundSpeaker = module.test_sound.speaker.name
		talkerIDRow.append('NA') if (testSoundSpeaker == None) else talkerIDRow.append(testSoundSpeaker)
		talkerIDRow.append(module.test_sound.speech_file.name.strip('cochlear/speech/'))
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
		openSetRow.append(openSet.open_set_train_order.session.week)
		openSetRow.append(openSet.open_set_train_order.session.day)
		openSetRow.append(("yes" if openSet.repeat else "no"))
		session = openSet.open_set_train_order.session
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
		module = openSet.open_set_train_order.open_set_train
		speakerName = module.test_sound.speaker.name
		openSetRow.append('NA' if (speakerName == None) else speakerName)
		openSetRow.append(module.test_sound.speech_file.name.strip('cochlear/speech/'))
		openSetRow.append(module.answer)
		openSetRow.append(module.key_words)
		openSetRow.append(openSet.user_response)
		openSetRow.append(openSet.percent_correct)
		rows.append(openSetRow)

class Echo(object):
	# An object that implements just the write method of the file-like interface.
	def write(self, value):
		# Write the value by returning it, instead of storing in a buffer.
		return value

def getAllUserDataCSV(request):
	# A view that streams a large CSV file.
	# Generate a sequence of rows. The range is based on the maximum number of
	# rows that can be handled by a single sheet in most spreadsheet
	# applications.
	# Documentation: https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
	rows = []
	appendTalkerID(rows)
	rows.append([]) #skip a line in the csv file

	rows.append(['Meaningful'])
	openSets = User_Open_Set_Train.objects.filter(open_set_train_order__open_set_train__type_train = 0, date_completed__isnull = False)
	appendOpenSets(rows, openSets)
	rows.append([])
	
	rows.append(['Anomalous'])
	openSets = User_Open_Set_Train.objects.filter(open_set_train_order__open_set_train__type_train = 1, date_completed__isnull = False)
	appendOpenSets(rows, openSets)
	rows.append([])

	rows.append(['Word'])
	openSets = User_Open_Set_Train.objects.filter(open_set_train_order__open_set_train__type_train = 2, date_completed__isnull = False)
	appendOpenSets(rows, openSets)

	pseudo_buffer = Echo()
	writer = csv.writer(pseudo_buffer)
	response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
	filename = "CI_Training_All_User_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response

def talkerIDCSV(request):
	# A view that streams a large CSV file.
	# Generate a sequence of rows. The range is based on the maximum number of
	# rows that can be handled by a single sheet in most spreadsheet
	# applications.
	# Documentation: https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
	rows = []
	appendTalkerID(rows)

	pseudo_buffer = Echo()
	writer = csv.writer(pseudo_buffer)
	response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
	filename = "CI_Training_Talker_ID_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response

def meaningfulCSV(request):
	# A view that streams a large CSV file.
	# Generate a sequence of rows. The range is based on the maximum number of
	# rows that can be handled by a single sheet in most spreadsheet
	# applications.
	# Documentation: https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
	rows = []
	rows.append(['Meaningful'])
	openSets = User_Open_Set_Train.objects.filter(open_set_train_order__open_set_train__type_train = 0, date_completed__isnull = False)
	appendOpenSets(rows, openSets)

	pseudo_buffer = Echo()
	writer = csv.writer(pseudo_buffer)
	response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
	filename = "CI_Training_Meaningful_Sentence_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response

def anomalousCSV(request):
	# A view that streams a large CSV file.
	# Generate a sequence of rows. The range is based on the maximum number of
	# rows that can be handled by a single sheet in most spreadsheet
	# applications.
	# Documentation: https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
	rows = []
	rows.append(['Anomalous'])
	openSets = User_Open_Set_Train.objects.filter(open_set_train_order__open_set_train__type_train = 1, date_completed__isnull = False)
	appendOpenSets(rows, openSets)

	pseudo_buffer = Echo()
	writer = csv.writer(pseudo_buffer)
	response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
	filename = "CI_Training_Anomalous_Sentence_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response

def wordCSV(request):
	# A view that streams a large CSV file.
	# Generate a sequence of rows. The range is based on the maximum number of
	# rows that can be handled by a single sheet in most spreadsheet
	# applications.
	# Documentation: https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
	rows = []
	rows.append(['Word'])
	openSets = User_Open_Set_Train.objects.filter(open_set_train_order__open_set_train__type_train = 2, date_completed__isnull = False)
	appendOpenSets(rows, openSets)

	pseudo_buffer = Echo()
	writer = csv.writer(pseudo_buffer)
	response = StreamingHttpResponse((writer.writerow(row) for row in rows), content_type="text/csv")
	filename = "CI_Training_Word_Data_" + str(timezone.now()).split(' ')[0].replace('-','') + ".csv"
	response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
	return response