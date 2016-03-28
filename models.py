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

#Tracking Data for a particular user session (a set of training modules completed on a given day)
class User_Session(models.Model):
    user = models.ForeignKey(User_Attrib, on_delete=models.CASCADE)
    date_completed = models.DateTimeField('date_completed')

    def __str__ (self):
        return self.user.username + self.date_completed

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

    def __str__(self):
        filename =  self.speech_file.name
        return filename.strip('cochlear/speech/')

# Associate each question with an answer, and indicate if that answer is right
class Closed_Set_Question_Answer(models.Model):
    question = models.ForeignKey('Closed_Set_Train',on_delete=models.SET_NULL, blank = True, null = True)
    answer = models.ForeignKey(Speech ,on_delete=models.SET_NULL, blank = True, null = True)
    iscorrect = models.BooleanField(default = False)

    def __str__(self):
        return str(self.question) + "_" + str(self.answer)

# A generic training module for closed-set responses, such as speaker ID training
class Closed_Set_Train(models.Model):
    choices = models.ManyToManyField(Speech, through ='Closed_Set_Question_Answer', related_name = 'Closed_Set_Trains')
    test_sound = models.ForeignKey(Speech)
    week = models.PositiveSmallIntegerField()
    day = models.PositiveSmallIntegerField()

    def __str__(self):
        return "week_" + str(self.week) + "_day_" + str(self.day)

# Data tracking for speaker identification training - to be implemented later
class Closed_Set_Data(models.Model):
    user = models.ForeignKey(User_Attrib,on_delete=models.CASCADE)
    closed_set_train = models.ForeignKey(Closed_Set_Train,on_delete = models.CASCADE)
    date_completed = models.DateTimeField('date completed')
#    attempts = models.PositiveIntegerField()
#    total_time = models.DurationField()

# Register the choices field within the admin panel
class Closed_Set_Question_Answer_Inline(admin.TabularInline):
        model = Closed_Set_Question_Answer
        extra = 2

# Register the choices field within the admin panel
class Closed_Set_Train_Admin(admin.ModelAdmin):
        inlines = (Closed_Set_Question_Answer_Inline,)

admin.site.register(Closed_Set_Train, Closed_Set_Train_Admin)
