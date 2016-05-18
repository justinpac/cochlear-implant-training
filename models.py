from django.db import models
from django.contrib import admin

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
    date_completed = models.DateTimeField('date_completed', blank = True, null = True)
    modules_completed = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.user.username + "_" + str(self.date_completed)

#Tracking Data for a particular user session (a set of training modules copleted on a given day)
class Session(models.Model):
    closed_set_trains = models.ManyToManyField('Closed_Set_Train', through='Closed_Set_Train_Order')
    open_set_trains = models.ManyToManyField('Open_Set_Train', through='Open_Set_Train_Order')
    week = models.PositiveIntegerField()
    day = models.PositiveSmallIntegerField()

    def __str__ (self):
        return "week_" + str(self.week) + "_day_" + str(self.day)

    def countModules(self):
        return self.closed_set_trains.all().count() + self.open_set_trains.count()

class Closed_Set_Train_Order(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    closed_set_train = models.ForeignKey('Closed_Set_Train', on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()

    def __str__(self):
        return "session_" + str(self.session) + "_closedSetTrain_"+ str(self.closed_set_train)

class Open_Set_Train_Order(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    open_set_train = models.ForeignKey('Open_Set_Train', on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()

    def __str__(self):
        return "session_" + str(self.session) + "_openSetTrain_"+ str(self.open_set_train)

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
        return self.speaker.name + "_" + filename.strip('cochlear/speech/')

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

    def __str__(self):
        return str(self.pk) + "_TestSound_" + str(self.test_sound)

# Data tracking for speaker identification training
class Closed_Set_Data(models.Model):
    user = models.ForeignKey(User_Attrib,on_delete=models.CASCADE)
    closed_set_train = models.ForeignKey(Closed_Set_Train,on_delete = models.CASCADE)
    date_completed = models.DateTimeField('date completed')
#    attempts = models.PositiveIntegerField()
#    total_time = models.DurationField()
    def __str__(self):
        return "(" + self.user.username + ")completed_" + self.date_completed

# A training module for open-set responses, such as meaningful sentence training
class Open_Set_Train(models.Model):
    test_sound = models.ForeignKey(Speech)
    answer = models.TextField()
    # type_train indicates the type of training this is. 0 = meaningful sentence training, 1 = anomalous sentence training, 2 = word training
    type_train = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.answer

# Register the choices field within the admin panel
class Closed_Set_Question_Answer_Inline(admin.TabularInline):
    model = Closed_Set_Question_Answer
    extra = 2

class Closed_Set_Train_Order_Inline(admin.TabularInline):
    model = Closed_Set_Train_Order
    extra = 1

class Open_Set_Train_Order_Inline(admin.TabularInline):
    model = Open_Set_Train_Order
    extra = 1

# # Register the choices field within the admin panel
class Closed_Set_Train_Admin(admin.ModelAdmin):
    inlines = [Closed_Set_Question_Answer_Inline,]

class Session_Admin(admin.ModelAdmin):
    inlines = [Closed_Set_Train_Order_Inline, Open_Set_Train_Order_Inline]

admin.site.register(Closed_Set_Train, Closed_Set_Train_Admin)
admin.site.register(Session,Session_Admin)


#first attempt at building a session module. We were unable to get generic relations to work.

#Necessary for GenereicForeignKey Relation
# from django.contrib.contenttypes import generic
# from django.contrib.contenttypes.models import ContentType
# from django.contrib.contenttypes.admin import GenericTabularInline

# Represents a generic module for use in a session.
# For information on generic many-to-many relationships:
# http://stackoverflow.com/questions/933092/generic-many-to-many-relationships
# class Session_Module(models.Model):
#     # session = models.ForeignKey('Session')
#     content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
#     object_id = models.PositiveIntegerField()
#     module = generic.GenericForeignKey('content_type','object_id')
#     orderInSession = models.PositiveSmallIntegerField()

    # def __str__(self):
    #     return self.tag

# register generic relations in admin
# class Session_Module_Inline(GenericTabularInline):
#     model = Session_Module
    # extra = 2
    # ct_field = 'content_type'
    # ct_fk_field = 'object_id'

# class Open_Set_Train_Admin(admin.ModelAdmin):
#     #model = Open_Set_Train
#     inlines = [Session_Module_Inline,]


# admin.site.register(Open_Set_Train, Open_Set_Train_Admin)
