from django.shortcuts import render,redirect

# We need this to generate the navbar
from hipercore.helpers import NavigationBar

# Import our database models
from cochlear.models import *

#Some helper functions
import cochlear.util

#Get django timezone utility
from django.utils import timezone

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
	context['sessions'] = User_Session.objects.filter(user=userList[0].id).count()
	context['percentComplete'] = str(context['sessions'] * 25)
	return render(request,'cochlear/index.html',context)

def speaker(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="speaker", navbarName=0)
	userList = User_Attrib.objects.filter(username=request.user.username)
	#retrive speaker 'choices' files for this training module
	speaker_data =  Closed_Set_Data.objects.filter(user = userList[0].id)
	if not speaker_data:
		speaker_module = Closed_Set_Train.objects.first()
	else:
		speaker_modules = Closed_Set_Train.objects.filter(id != speaker_data.closed_set_train.id)
		speaker_module = speaker_modules.first()

	context['test_sound'] = speaker_module.test_sound
	context['speaker_choices'] = speaker_module.choices.all()
	context['speaker_module_id'] = speaker_module.id
	context['user_attrib_id'] = userList[0].id

	return render(request,'cochlear/speaker.html',context)

def history(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="history", navbarName=0)

	return render(request,'cochlear/history.html',context)


##################
## Ajax methods ##
##################

from django.http import HttpResponse

def sessionCompleted(request):
	return HttpResponse("Success")

###################
## Manager Pages ##
###################

#NOTE: Make sure to add the names of all the pages that should only be accessible
#by managers in middleware.py

def dashboard(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="index", navbarName='manager')
	if(request.method == "POST"):#If the user has submitted something, Handle the upload
		#Get the speaker files
		for fileObj in request.FILES.getlist('speaker_choices'):
			print(fileObj)
		#Get the test sound
		print(request.FILES['test_sound']) 

	context['name'] = request.user.username;
	return render(request,'cochlear/manager_dashboard.html',context)

def settings(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="index", navbarName='manager')
	return render(request,'cochlear/settings.html',context)
