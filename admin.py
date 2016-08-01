from django.contrib import admin

#Import all of our models
from cochlear.models import *

# Register your models here.
# We need to do this so that they appear in the admin panel.
admin.site.register(Public_Sound)

admin.site.register(User_Attrib)
admin.site.register(User_Session)

admin.site.register(Speaker)
admin.site.register(Speech)

admin.site.register(Sound_Source)
admin.site.register(Sound)

admin.site.register(Text_Choice)

admin.site.register(User_Closed_Set_Text)

admin.site.register(User_Speaker_ID)

admin.site.register(Open_Set_Module)
admin.site.register(User_Open_Set_Module)

# IN-LINE REGISTERED:

# Session

# Closed_Set_Text
# Closed_Set_Text_Choice
# Closed_Set_Text_Order

# Speaker_ID
# Speaker_ID_Choice
# Speaker_ID_Order

# Open_Set_Module_Order