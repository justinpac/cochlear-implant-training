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
	return render(request,'cochlear/index.html',context)

def speaker(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="speaker", navbarName=0)
	userObj = User_Attrib.objects.get(username=request.user.username)
	#retrive speaker 'choices' files for this training module
	speaker_data =  Closed_Set_Data.objects.filter(user = userObj.id)
	if not speaker_data:
		speaker_module = Closed_Set_Train.objects.first()
	else:
		speaker_modules = Closed_Set_Train.objects.filter(id != speaker_data.closed_set_train.id)
		speaker_module = speaker_modules.first()

	context['test_sound'] = speaker_module.test_sound
	context['speaker_choices'] = speaker_module.choices.all().order_by('?')
	context['speaker_module_id'] = speaker_module.id
	context['user_attrib_id'] = userObj.id

	return render(request,'cochlear/speaker.html',context)

def history(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="history", navbarName=0)

	return render(request,'cochlear/history.html',context)


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
		print("Using speaker ID",speakerID)
		#Create a new speech object, and attach it to the speaker 
		speakerObj = Speaker.objects.get(pk=speakerID);
		newSoundObj = Speech();
		newSoundObj.speaker = speakerObj;
		newSoundObj.speech_file = rawFile;
		newSoundObj.save();


		return HttpResponse("Success")
	else:
		return HttpResponse("No POST data received.")

def sessionCompleted(request):
	userList = User_Attrib.objects.filter(username=request.user.username)
	user = userList[0]
	newSession = User_Session(user = user, date_completed = timezone.now())
	newSession.save();
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

def dashboard(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="index", navbarName='manager',activeLink="Manager Dashboard")

	context['soundFileList'] = {}
	context['soundFileList']['headers'] = ['Filename','Speaker Name','Date Uploaded']
	context['soundFileList']['rows'] = []
	context['soundFileList']['id'] = 'soundfiles'
	context['soundFileList']['colSize'] = int(12/len(context['soundFileList']['headers']))
	soundFiles = Speech.objects.all();
	for sound in soundFiles:
		row = [sound.speech_file.name,sound.speaker.name,str(sound.uploaded_date)]
		context['soundFileList']['rows'].append(row)

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
