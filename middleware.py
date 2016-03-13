from cochlear.models import *

from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

import cochlear.util

APP_NAME = "cochlear"

ManagerOnlyPages = ['dashboard','settings']

class PermissionsCheck:
	#Makes sure each user can only access the pages they have permission for
	def process_request(self,request):
		#This runs on every web request
		if(request.path.find("app/" + APP_NAME) >= 0):#Run this check ONLY if the user is on our app
			username = request.user.username;
			#Check if the user has permission to access this page
			permission = cochlear.util.GetUserPermission(username);
			# If not a user, no access for you!
			if (permission == -1):
					raise PermissionDenied;
			#Snip the name of the app from the url
			url = request.path.replace("app/"+APP_NAME+"/","");
			for page in ManagerOnlyPages:
				if(url.find(page) >= 0 and permission < 1):
					#If we're on a manager page, and have permission less than one
					raise PermissionDenied;
			#If we don't return anything (the same as returning None), it will simply let the user pass through
