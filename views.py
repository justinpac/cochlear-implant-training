from django.shortcuts import render,redirect

# We need this to generate the navbar
from hipercore.helpers import NavigationBar

# Import our database models
from cochlear.models import *

#Some helper functions
import cochlear.util

def index(request):
	#If user is manager, redirect to the manager dashboard (so the homepage always takes the manager to their dasboard)
	permission = cochlear.util.GetUserPermission(request.user.username);
	if(permission > 0):
		return redirect('cochlear:dashboard')
	#Render a basic page
	context = NavigationBar.generateAppContext(request,app="cochlear",title="index", navbarName=0)
	userList = User_Attrib.objects.filter(username=request.user.username)
	context['name'] = userList[0].first_name
	context['sessions'] = userList[0].sessions_this_week
	return render(request,'cochlear/index.html',context)

def speaker(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="speaker", navbarName=0);

	return render(request,'cochlear/speaker.html',context)

def history(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="history", navbarName=0);

	return render(request,'cochlear/history.html',context)

###################
## Manager Pages ##
###################

#NOTE: Make sure to add the names of all the pages that should only be accessible
#by managers in middleware.py

def dashboard(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="index", navbarName='manager');
	context['name'] = request.user.username;
	return render(request,'cochlear/manager_dashboard.html',context)

def settings(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="index", navbarName='manager');
	return render(request,'cochlear/settings.html',context)
