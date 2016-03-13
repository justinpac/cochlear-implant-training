from django.db import models

class User_Attrib(models.Model):
    username = models.CharField(max_length = 50)
    first_name = models.CharField(max_length = 50)
    last_name = models.CharField(max_length = 50)
    email = models.EmailField()
    status = models.PositiveSmallIntegerField(default = 0) # 0 = standard user, 1 = manager, 2 = admin
    sessions_this_week = models.PositiveSmallIntegerField(default = 0) # Field for how many training sessions the user has completed in a week

    def __str__(self):
        return self.username

# Speaker associated with potentiallly many speach files
class Speaker(models.Model):
    name = models.CharField(max_length = 50)
    difficulty = models.PositiveSmallIntegerField(default = 0)

    def __str__(self):
        return self.name

# A sound file of speach, whether it be a sentence, word, or phoneme.
class Speach(models.Model):
    speach_file = models.FileField(upload_to = '/cochlear/speach')
    speaker = models.ForeignKey(Speaker, on_delete=models.SET_NULL, blank = True, null = True)
    difficulty = models.PositiveSmallIntegerField(default = 0)

# Associate each question with an answer, and indicate if that answer is right
class Closed_Set_Question_Answer(models.Model):
    question = models.ForeignKey('Closed_Set_Train',on_delete=models.SET_NULL, blank = True, null = True)
    answer = models.ForeignKey('Speach' ,on_delete=models.SET_NULL, blank = True, null = True)
    iscorrect = models.BooleanField(default = False)

# A generic training module for closed-set responses, such as speaker ID training
class Closed_Set_Train(models.Model):
    choices = models.ManyToManyField('Speach', through ='Closed_Set_Question_Answer', related_name = 'closed_set_choices')
    test_sound = models.ForeignKey(Speach)


# Data tracking for speaker identification training - to be implemented later
#class Closed_Set_Data(models.Models):
#    user = models.ForeignKey(User,on_delete=models.CASCADE)
#    attempts = models.PositiveIntegerField()
#    date_completed = models.DateTimeField('date completed')
#    total_time = models.DurationField()
