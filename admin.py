from django.contrib import admin

#Import all of our models
from cochlear.models import *

# Register your models here.
# We need to do this so that they appear in the admin panel.
admin.site.register(User)
admin.site.register(Speaker)
admin.site.register(Speach)
admin.site.register(Closed_Set_Question_Answer)
admin.site.register(Closed_Set_Train)
