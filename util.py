#Just some misc helper functions
from cochlear.models import *

def GetUserPermission(username):
	#Takes a username and returns 0,1 or 2 depending on their permission status
	#If no user is found, returns 0 
	userList = User.objects.filter(username=username);
	if(len(userList) == 0):
		return 0;
	else:
		return userList[0].status;