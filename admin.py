from django.contrib import admin

#Import all of our models
from cochlear.models import *

# Register your models here.
# We need to do this so that they appear in the admin panel.
admin.site.register(User_Attrib)
admin.site.register(User_Session)
admin.site.register(Speaker)
admin.site.register(Speech)
admin.site.register(Closed_Set_Question_Answer)
admin.site.register(Closed_Set_Data)
admin.site.register(Closed_Set_Train_Order)
admin.site.register(User_Closed_Set_Train)
admin.site.register(Open_Set_Train)
admin.site.register(Open_Set_Train_Order)
admin.site.register(User_Open_Set_Train)
#Session, Closed_Set_Train inline registered