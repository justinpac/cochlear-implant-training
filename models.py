from django.db import models
from django.contrib import admin
from django.db.models import Avg

# Information about the user
class User_Attrib(models.Model):
	username = models.CharField(max_length = 50, unique = True)
	first_name = models.CharField(max_length = 50)
	last_name = models.CharField(max_length = 50)
	email = models.EmailField()
	status = models.PositiveSmallIntegerField(default = 0, help_text="0 = standard user, 1 = manager, 2 = admin") # 0 = standard user, 1 = manager, 2 = admin
	current_week_start_date = models.DateTimeField(blank = True, null=True)
	progression = models.PositiveSmallIntegerField(default=0, help_text='indicates which progression milestone the user has already passed. 0 = new user, 1 = tested, 2 = week one complete')
	meaningful_proficiency = models.PositiveSmallIntegerField(default=0)
	env_proficiency = models.PositiveSmallIntegerField(default=0)
	anom_proficiency = models.PositiveSmallIntegerField(default=0)
	word_proficiency = models.PositiveSmallIntegerField(default=0)
	phon_proficiency = models.PositiveSmallIntegerField(default=0)
	speaker_proficiency = models.PositiveSmallIntegerField(default=0)
	
	def __str__(self):
		return self.username

	class Meta:
		verbose_name_plural = "User Attributes"
		verbose_name = "user attribute"

# A series of training modules with a specified order
class Session(models.Model):
	speaker_ids = models.ManyToManyField('Speaker_ID', through='Speaker_ID_Order')
	open_set_modules = models.ManyToManyField('Open_Set_Module', through='Open_Set_Module_Order')
	closed_set_texts = models.ManyToManyField('Closed_Set_Text', through='Closed_Set_Text_Order')
	name = models.CharField(max_length=75, blank = True)
	meaningful_difficulty = models.PositiveSmallIntegerField(editable = False, default = 0)
	env_difficulty = models.PositiveSmallIntegerField(editable = False, default = 0)
	anom_difficulty = models.PositiveSmallIntegerField(editable = False, default = 0)
	word_difficulty = models.PositiveSmallIntegerField(editable = False, default = 0)
	phon_difficulty = models.PositiveSmallIntegerField(editable = False, default = 0)
	speaker_difficulty = models.PositiveSmallIntegerField(editable = False, default = 0)

	# Overrrides the models.Model superclass save() method, called whenever model is updated
	def save(self):
		#If this is the first time saving the model, save it first before accessing the many to many fields and saving again
		if not self.id:
			super(Session, self).save()

		# meaningful: open set
		meaningful_temp = self.open_set_modules.filter(module_type = 1).aggregate(Avg('difficulty')).get('difficulty__avg')
		meaningful_difficulty = 0 if meaningful_temp == None else round(meaningful_temp)
		# Environmental: open/closed set
		env_temp = self.open_set_modules.filter(module_type = 4).aggregate(Avg('difficulty')).get('difficulty__avg')
		env_temp2 = self.open_set_modules.filter(module_type = 2).aggregate(Avg('difficulty')).get('difficulty__avg')
		env_difficulty = 0 if env_temp == None or env_temp2 == None else round(env_temp + env_temp2)
		# Anomalous: open set
		anom_temp = self.open_set_modules.filter(module_type = 2).aggregate(Avg('difficulty')).get('difficulty__avg')
		anom_difficulty = 0 if anom_temp == None else round(anom_temp)
		# word: open set
		word_temp = self.open_set_modules.filter(module_type = 3).aggregate(Avg('difficulty')).get('difficulty__avg')
		word_difficulty = 0 if word_temp == None else round(word_temp)
		# phoneme: closed set
		phon_temp = self.closed_set_texts.filter(module_type = 1).aggregate(Avg('difficulty')).get('difficulty__avg')
		phon_difficulty = 0 if phon_temp == None else round(phon_temp)
		# speaker ids
		speaker_temp = self.speaker_ids.aggregate(Avg('difficulty')).get('difficulty__avg')
		speaker_difficulty = 0 if speaker_temp == None else round(speaker_temp)

		super(Session, self).save()

	def __str__ (self):
		return self.name if self.name != "" else "Unnamed Session"

	def countModules(self):
		return self.speaker_ids.all().count() + self.open_set_modules.all().count() + self.closed_set_texts.all().count()

# Data about a user's completion of a given session. Used primarily to track progress while a user is completing a session,
# but also contains the timestamp for completion of the session.
class User_Session(models.Model):
	user = models.ForeignKey('User_Attrib', on_delete=models.CASCADE)
	session = models.ForeignKey('Session', related_name='user_sessions', on_delete=models.SET_NULL, blank = True, null=True)
	user_sequence = models.ForeignKey('User_Sequence', on_delete=models.CASCADE, blank = True, null=True)
	date_completed = models.DateTimeField('date_completed', blank = True, null = True)
	modules_completed = models.PositiveSmallIntegerField(default=0)
	first_speaker_id = models.BooleanField(default = True)
	first_open_set_module = models.CharField(max_length=15, default="11111", help_text='A string of integers. The index represents module type, and each integer is a 0 or 1 indicating if this user has not yet completed a module of that type.')
	first_closed_set_text = models.CharField(max_length=15, default="111", help_text='A string of integers. The index represents module type, and each integer is a 0 or 1 indicating if this user has not yet completed a module of that type.')
	calibrated = models.BooleanField(default = False)

	def __str__(self):
		return "User: " + self.user.username + ", Session: " + str(self.session)+ ", DateCompleted: " + str(self.date_completed)

	class Meta:
		verbose_name_plural = "(User Data) User Session Data"
		verbose_name = "user session"

# The order of a session within a sequence
class Session_Order(models.Model):
	sequence = models.ForeignKey('Sequence')
	session = models.ForeignKey('Session')
	order = models.PositiveSmallIntegerField()

	class Meta:
		ordering = ('order',)

# A series of sessions assigned to a user
class Sequence(models.Model):
	name = models.CharField(max_length = 75, blank = True)
	category = models.PositiveSmallIntegerField(help_text='the type of sequence this is. 0 = testing, 1 = week one, 2 = autogenerated')
	sessions = models.ManyToManyField('Session',through='Session_Order')

	def __str__(self):
		return self.name

# A sequence that has been assigned to the user
class User_Sequence(models.Model):
	user = models.ForeignKey('User_Attrib', on_delete = models.CASCADE)
	sequence = models.ForeignKey('Sequence', on_delete = models.SET_NULL, blank=True, null=True)
	sessions_completed = models.PositiveSmallIntegerField(default=0)
	date_assigned = models.DateTimeField(auto_now_add=True)
	date_completed = models.DateTimeField(blank=True, null=True)
	date_started = models.DateTimeField(blank=True,null=True)

	class Meta:
		verbose_name_plural = "Sequence Assignments"
		verbose_name = "sequence assignment"

	def __str__(self):
		return "User: "  + self.user.username + ", Sequence: " + (self.sequence.name if self.sequence else "No Sequence Selected")

# Speaker associated with potentially many speech files
class Speaker(models.Model):
	name = models.CharField(max_length = 50, unique=True)
	display_name = models.CharField(max_length = 50, help_text="This is the name the user will see when encountering this speaker, such as in the speaker identification module")
	gender = models.CharField(max_length=20, help_text="Type 'male' for male or 'female' for female")
	notes = models.TextField(help_text="Miscellaneous information", blank=True)

	def __str__(self):
		return self.name

# A sound file of speech, whether it be a sentence, word, or phoneme.
class Speech(models.Model):
	speech_file = models.FileField(upload_to = 'cochlear/speech')
	speaker = models.ForeignKey('Speaker', on_delete=models.CASCADE)
	uploaded_date = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.speech_file.name.strip('cochlear/speech/')

	class Meta:
		verbose_name_plural = "Speech"
		verbose_name = "speech"

# The source of a non-speech sound
class Sound_Source(models.Model):
	name = models.CharField(max_length=50, unique=True, help_text="WARNING: this should not be a speaker")
	display_name = models.CharField(max_length = 50, help_text="This is the name the user will see when encountering this source, such as in environmental sound training")
	notes = models.TextField(help_text="Miscellaneous information", blank=True)

	def __str__(self):
		return self.name

	class Meta:
		verbose_name_plural = "Sound Sources"
		verbose_name = "sound source"

# A non-speech sound
class Sound(models.Model):
	sound_file = models.FileField(upload_to = 'cochlear/sound', help_text="This is not intended to be spoken word associated with a known speaker")
	source = models.ForeignKey('Sound_Source',on_delete=models.CASCADE)

	def __str__(self):
		return self.sound_file.name.strip('cochlear/sound/')

# A text-based response, used in closed set training modules.
class Text_Choice(models.Model):
	text = models.TextField(unique=True)

	def __str__(self):
		return self.text

	class Meta:
		verbose_name_plural = "Text Choices"
		verbose_name = "text choice"

# A closed set training module in which the user is presented with speech or a sound and a set of text-based response choices.
class Closed_Set_Text(models.Model):
	text_choices = models.ManyToManyField('Text_Choice', through = 'Closed_Set_Text_Choice', help_text = "A set of simple text-based response choices.")
	unknown_speech = models.ForeignKey('Speech', blank = True, null = True, on_delete = models.CASCADE, help_text = "The unknown speech to be identified. Pick one sound or speech.")
	unknown_sound = models.ForeignKey('Sound', blank = True, null = True, on_delete = models.CASCADE, help_text = "The unknown sound to be identified. Pick one sound or speech.")
	module_type = models.PositiveSmallIntegerField(help_text = "0 = other, 1 = phoneme training, 2 = environmental sound training")
	difficulty = models.PositiveSmallIntegerField(help_text="Enter a number between 0 and 9.")

	def __str__(self):
		module_types = ["Other","Phoneme", "Environmental"]
		test_sound = self.unknown_speech if self.unknown_speech else self.unknown_sound
		return "(" + module_types[self.module_type] + ") " + str(test_sound)

	class Meta:
		verbose_name_plural = "(Training Module) Closed Set Text Modules"
		verbose_name = "closed set text module"


# A text-based response within a given Closed_Set_Text
class Closed_Set_Text_Choice(models.Model):
	closed_set_text = models.ForeignKey('Closed_Set_Text', on_delete = models.CASCADE)
	choice = models.ForeignKey('Text_Choice', on_delete = models.CASCADE)
	iscorrect = models.BooleanField()

	def __str__(self):
		return "Closed Set Text: [" + str(self.closed_set_text) + "] choice: " + str(self.choice)

	class Meta:
		verbose_name_plural = "Closed Set Text Choices"
		verbose_name = "closed set text choice"

# The order of a Closed_Set_Text_Module within a given Session
class Closed_Set_Text_Order(models.Model):
	session = models.ForeignKey('Session', on_delete=models.CASCADE)
	closed_set_text = models.ForeignKey('Closed_Set_Text', on_delete=models.CASCADE)
	order = models.PositiveIntegerField(help_text = "unique integer value, starting at one, that spans all module types.")

	def __str__(self):
		return "Session: " + str(self.session) + ", Closed Set Text: ["+ str(self.closed_set_text) + "]"

	class Meta:
		verbose_name_plural = "Closed Set Text Order"
		verbose_name = "closed set text order"

# User-specific data on a user's completion of a CLosed_Set_Text module
class User_Closed_Set_Text(models.Model):
	user_attrib = models.ForeignKey('User_Attrib', on_delete = models.CASCADE)
	closed_set_text_order = models.ForeignKey('Closed_Set_Text_Order', on_delete = models.SET_NULL, blank=True, null=True)
	user_session = models.ForeignKey('User_Session', on_delete = models.CASCADE, blank = True, null = True)
	repeat = models.BooleanField(help_text = "Was this completed while the user was repeating the training module?") # Indicates if this instance was generated while the user was repeating the training module
	date_completed = models.DateTimeField(blank = True, null = True)
	user_response = models.ForeignKey('Text_Choice', on_delete = models.PROTECT, blank = True, null = True)
	correct = models.NullBooleanField(blank = True, null = True)

	def __str__(self):
		return "User: " + str(self.user_attrib) + ", " + str(self.closed_set_text_order)

	#This is the defaulted ordering of records. It is especially useful for exporting CSVs.
	class Meta:
		ordering = ('user_attrib__username','repeat','closed_set_text_order__closed_set_text__id')
		verbose_name_plural = "(User Data) User Closed Set Text Data"
		verbose_name = "user closed set text"

# The unknown speech and answer choices of a speaker identification training module
class Speaker_ID(models.Model):
	unknown_speech = models.ForeignKey('Speech', on_delete = models.CASCADE, help_text = "The unknown speech is intended for speaker identification training, but can be combined with sound and text choices.")
	choices = models.ManyToManyField('Speech', related_name = "Speaker_IDs", through='Speaker_ID_Choice', help_text="The possible speech files (and corresponding speakers) that the user may identify as the unknown speaker")
	difficulty = models.PositiveSmallIntegerField(help_text="Enter a number between 0 and 9.")

	def __str__(self):
		return "Unknown Speech: " + str(self.unknown_speech)

	class Meta:
		# admin panel display name
		verbose_name_plural = "(Training Module) Speaker ID Modules"
		verbose_name = "speaker ID module"

# Associate each closed set training module with a possible choice, and indicate if that answer is correct
class Speaker_ID_Choice(models.Model):
	speaker_id = models.ForeignKey('Speaker_ID',on_delete=models.CASCADE)
	choice = models.ForeignKey('Speech' ,on_delete=models.CASCADE)
	iscorrect = models.BooleanField()

	def __str__(self):
		return "Speaker ID: [" + str(self.speaker_id) + "], Choice: " + str(self.choice)

	class Meta:
		# admin panel display name
		verbose_name_plural = "Speaker ID Choices"
		verbose_name = "speaker ID choice"

# Defines the order of a closed set training module in a session
class Speaker_ID_Order(models.Model):
	session = models.ForeignKey('Session', on_delete=models.CASCADE)
	speaker_id = models.ForeignKey('Speaker_ID', on_delete=models.CASCADE)
	order = models.PositiveSmallIntegerField(help_text = "unique integer value, starting at one, that spans all module types.")

	def __str__(self):
		return "Session: " + str(self.session) + ", Speaker_ID: ["+ str(self.speaker_id) + "]"

	class Meta:
		# admin panel display name
		verbose_name_plural = "Speaker ID Order"
		verbose_name = "speaker ID order"

# This is necessary to determine if a user has completed a certain training module in a given session.
# Also used to track data about a user's completion of that module
class User_Speaker_ID(models.Model):
	user_attrib = models.ForeignKey('User_Attrib', on_delete=models.CASCADE)
	speaker_id_order = models.ForeignKey('Speaker_ID_Order', on_delete=models.SET_NULL, blank=True, null=True)
	user_session = models.ForeignKey('User_Session', on_delete = models.CASCADE, blank = True, null = True)
	repeat = models.BooleanField(help_text = "Was this completed while the user was repeating the training module?") # Indicates if this instance was generated while the user was repeating the training module
	date_completed = models.DateTimeField(blank = True, null = True)
	user_response = models.ForeignKey('Speech', on_delete = models.PROTECT, blank = True, null = True)
	correct = models.NullBooleanField(blank = True, null = True)

	def __str__(self):
		return "User: " + str(self.user_attrib) + ", " + str(self.speaker_id_order)

	#This is the defaulted ordering of records. It is especially useful for exporting CSVs.
	class Meta:
		ordering = ('user_attrib__username','repeat','speaker_id_order__speaker_id__id')
		# admin panel display name
		verbose_name_plural = "(User Data) User Speaker ID Data"
		verbose_name = "user speaker ID"

# A training module for open-set responses, such as meaningful sentence training
class Open_Set_Module(models.Model):
	unknown_speech = models.ForeignKey('Speech', on_delete = models.CASCADE, blank = True, null = True, help_text = "The unknown speech to be identified. Pick one sound or speech.")
	unknown_sound = models.ForeignKey('Sound', on_delete = models.CASCADE, blank = True, null = True, help_text = "The unknown sound to be identified. Pick one sound or speech.")
	answer = models.TextField()
	module_type = models.PositiveSmallIntegerField(help_text="0 = other, 1 = meaningful sentence training, 2 = anomalous sentence training, 3 = word training, 4 = environmental sound training")
	key_words = models.TextField(blank=True, help_text='''The keywords of this answer (used to determine accuracy). Enter each keyword separated by underscores. Group together alternate words and separate them by forward slashes.
		For example, "birch_canoe_slid/hid/bid_down_smooth_planks/pluck ranks". The user is allow one typo (insertion, deletion, or substitution) when evaluating each keyword.''')
	difficulty = models.PositiveSmallIntegerField(help_text="Enter a number between 0 and 9.")

	def __str__(self):
		module_types = ["other", "meaningful", "anomalous", "word", "environmental"]
		test_sound = self.unknown_speech if self.unknown_speech else self.unknown_sound
		return "(" + module_types[self.module_type] + ") " + str(test_sound)

	class Meta:
		# admin panel display name
		verbose_name_plural = "(Training Module) Open Set Modules"
		verbose_name = "open set module"

# Defines the order of an open set training module in a session
class Open_Set_Module_Order(models.Model):
	session = models.ForeignKey('Session', on_delete=models.CASCADE)
	open_set_module = models.ForeignKey('Open_Set_Module', on_delete=models.CASCADE)
	order = models.PositiveSmallIntegerField(help_text = "unique integer value, starting at one, that spans all module types.")

	def __str__(self):
		return "Session: " + str(self.session) + ", OpenSetModule: "+ str(self.open_set_module)

	class Meta:
		# admin panel display name
		verbose_name_plural = "Open Set Module Order"
		verbose_name = "open set module order"


# Necessary to determine if a user has completed a certain training module in a given session.
# Also used for tracking data about a user's completion of that module
class User_Open_Set_Module(models.Model):
	user_attrib = models.ForeignKey('User_Attrib', on_delete=models.CASCADE)
	open_set_module_order = models.ForeignKey('Open_Set_Module_Order', on_delete=models.SET_NULL, blank=True, null=True)
	user_session = models.ForeignKey('User_Session', on_delete = models.CASCADE, blank = True, null = True)
	repeat = models.BooleanField(help_text = "Was this completed while the user was repeating the training module?") # Indicates if this instance was generated while the user was repeating the training module
	date_completed = models.DateTimeField(blank = True, null = True)
	user_response = models.TextField(blank = True, null = True)
	percent_correct = models.PositiveSmallIntegerField(blank = True, null = True)

	def __str__(self):
		return "User: " + str(self.user_attrib) + ", " + str(self.open_set_module_order)

	#This is the defaulted ordering of records. It is especially useful for exporting CSVs.
	class Meta:
		ordering = ('user_attrib__username','repeat','open_set_module_order__open_set_module__id')
		verbose_name_plural = "(User Data) User Open Set Module Data"
		verbose_name = "user open set module"


################################
## In-Line Admin Registration ##
################################
# For more information: https://docs.djangoproject.com/en/1.9/ref/contrib/admin/#django.contrib.admin.TabularInline
class Session_Order_Inline(admin.TabularInline):
	model = Session_Order
	extra = 1

class Closed_Set_Text_Choice_Inline(admin.TabularInline):
	model = Closed_Set_Text_Choice
	extra = 1

class Closed_Set_Text_Order_Inline(admin.TabularInline):
	model = Closed_Set_Text_Order
	extra = 1

class Speaker_ID_Choice_Inline(admin.TabularInline):
	model = Speaker_ID_Choice
	extra = 1

class Speaker_ID_Order_Inline(admin.TabularInline):
	model = Speaker_ID_Order
	extra = 1

class Open_Set_Module_Order_Inline(admin.TabularInline):
	model = Open_Set_Module_Order
	extra = 1

class Sequence_Admin(admin.ModelAdmin):
	inlines = [Session_Order_Inline]

class Closed_Set_Text_Admin(admin.ModelAdmin):
	inlines = [Closed_Set_Text_Choice_Inline]

class Speaker_ID_Admin(admin.ModelAdmin):
	inlines = [Speaker_ID_Choice_Inline]

class Session_Admin(admin.ModelAdmin):
	inlines = [Open_Set_Module_Order_Inline, Speaker_ID_Order_Inline, Closed_Set_Text_Order_Inline]

admin.site.register(Sequence, Sequence_Admin)
admin.site.register(Closed_Set_Text, Closed_Set_Text_Admin)
admin.site.register(Speaker_ID, Speaker_ID_Admin)
admin.site.register(Session, Session_Admin)
