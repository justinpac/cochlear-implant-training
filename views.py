from django.shortcuts import render,redirect

# We need this to generate the navbar
from hipercore.helpers import NavigationBar

# Import our database models
from cochlear.models import *

def index(request):
	#Render a basic page
	context = NavigationBar.generateAppContext(request,app="cochlear",title="index", navbarName=0);
	#Fancy database queries
	context['name'] = "\"False\"";#request.user.username;
	return render(request,'cochlear/index.html',context)

def speaker(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="speaker", navbarName=0);

	return render(request,'cochlear/speaker.html',context)

def history(request):
	context = NavigationBar.generateAppContext(request,app="cochlear",title="history", navbarName=0);

	return render(request,'cochlear/history.html',context)
