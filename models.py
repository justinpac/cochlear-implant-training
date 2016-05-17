from django.db import models
from django.contrib import admin

#Necessary for GenereicForeignKey Relation
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.admin import GenericTabularInline

# Information about the user
class User_Attrib(models.Model):
    username = models.CharField(max_length = 50)
    first_name = models.CharField(max_length = 50)
    last_name = models.CharField(max_length = 50)
    email = models.EmailField()
    status = models.PositiveSmallIntegerField(default = 0) # 0 = standard user, 1 = manager, 2 = admin

    def __str__(self):
        return self.username

class User_Session(models.Model):
    session = models.ForeignKey('Session',on_delete=models.CASCADE)
    user = models.ForeignKey(User_Attrib, on_delete=models.CASCADE)
    date_completed = models.DateTimeField('date_completed')

    def __str__(self):
        return self.user.username + "_" + str(self.date_completed)

#Tracking Data for a particular user session (a set of training modules copleted on a given day)
class Session(models.Model):
    # closed_set_trains = models.ManyToManyField('Closed_Set_Train', related_name='Sessions')
    # open_set_trains = models.ManyToManyField('Open_Set_Train', related_name='Sessions')
    week = models.PositiveIntegerField()
    day = models.PositiveSmallIntegerField()

    def __str__ (self):
        return self.user.username + str(self.date_completed)

# Represents a generic module for use in a session.
# For information on generic many-to-many relationships:
# http://stackoverflow.com/questions/933092/generic-many-to-many-relationships
class Session_Module(models.Model):
    session = models.ForeignKey('Session')
    module_content_type = models.ForeignKey(ContentType)
    module_id = models.PositiveSmallIntegerField()
    module = generic.GenericForeignKey('module_content_type','module_id')
    orderInSession = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.tag

# class Closed_Set_Train_Order(models.Model):
#     session = models.ForeignKey(Session)
#     closed_set_train = models.ForeignKey('Closed_Set_Train')
#     order = models.PositiveSmallIntegerField()

#     def __str__(self):
#         return self.Session + self.Closed_Set_Train

# Speaker associated with potentiallly many speech files
class Speaker(models.Model):
    name = models.CharField(max_length = 50)
    difficulty = models.PositiveSmallIntegerField(default = 0)

    def __str__(self):
        return self.name

# A sound file of speech, whether it be a sentence, word, or phoneme.
class Speech(models.Model):
    speech_file = models.FileField(upload_to = 'cochlear/speech')
    speaker = models.ForeignKey(Speaker, on_delete=models.SET_NULL, blank = True, null = True)
    difficulty = models.PositiveSmallIntegerField(default = 0)
    uploaded_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        filename =  self.speech_file.name
        return filename.strip('cochlear/speech/')

# Associate each question with an answer, and indicate if that answer is right
class Closed_Set_Question_Answer(models.Model):
    question = models.ForeignKey('Closed_Set_Train',on_delete=models.CASCADE)
    answer = models.ForeignKey(Speech ,on_delete=models.CASCADE)
    iscorrect = models.BooleanField()

    def __str__(self):
        return str(self.question) + "_" + str(self.answer)

# A generic training module for closed-set responses, such as speaker ID training
class Closed_Set_Train(models.Model):
    choices = models.ManyToManyField(Speech, through ='Closed_Set_Question_Answer', related_name = 'Closed_Set_Trains')
    test_sound = models.ForeignKey(Speech)
    session_modules = generic.GenericRelation(Session_Module, related_query_name='Open_Set_Trains',
        content_type_field ='module_content_type', object_id_field = 'module_id')


    def __str__(self):
        return "week_" + str(self.week) + "_day_" + str(self.day)

# Data tracking for speaker identification trainin
class Closed_Set_Data(models.Model):
    user = models.ForeignKey(User_Attrib,on_delete=models.CASCADE)
    closed_set_train = models.ForeignKey(Closed_Set_Train,on_delete = models.CASCADE)
    date_completed = models.DateTimeField('date completed')
#    attempts = models.PositiveIntegerField()
#    total_time = models.DurationField()
    def __str__(self):
        return "(" + self.user.username + ")completed:" + self.date_completed

class Open_Set_Train(models.Model):
    test_sound = models.ForeignKey(Speech)
    answer = models.TextField()
    # type_train indicates the type of training this is. 0 = meaningful sentence trainging,
    # 1 = anomalous sentence training, 2 = word training
    type_train = models.PositiveSmallIntegerField()
    session_modules = generic.GenericRelation(Session_Module, related_query_name='Open_Set_Trains',
        content_type_field ='module_content_type', object_id_field = 'module_id')

    def __str__(self):
        return self.answer

#register generic relations in admin
class Session_Module_Inline(GenericTabularInline):
    model = Session_Module
    extra = 2
    ct_field = 'module_content_type'
    ct_fk_field = 'module_id'

# Register the choices field within the admin panel
class Closed_Set_Question_Answer_Inline(admin.TabularInline):
    model = Closed_Set_Question_Answer
    extra = 2

# Register the choices field within the admin panel
class Closed_Set_Train_Admin(admin.ModelAdmin):
    #model = Closed_Set_Train
    inlines = (Closed_Set_Question_Answer_Inline,Session_Module_Inline)

class Open_Set_Train_Admin(admin.ModelAdmin):
    #model = Open_Set_Train
    inlines = (Session_Module_Inline,)

admin.site.register(Closed_Set_Train, Closed_Set_Train_Admin)
admin.site.register(Open_Set_Train, Open_Set_Train_Admin)