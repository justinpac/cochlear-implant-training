from django.shortcuts import render,redirect

# We need this to generate the navbar
from hipercore.helpers import NavigationBar

# Import our database models
from cochlea.models import *

def index(request):
	#Render a basic page
	context = NavigationBar.generateAppContext(request,app="cochlea",title="index", navbarName=0);

	return render(request,'cochlea/index.html',context)
