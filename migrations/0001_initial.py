# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Closed_Set_Data',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('date_completed', models.DateTimeField(verbose_name='date completed')),
            ],
        ),
        migrations.CreateModel(
            name='Closed_Set_Question_Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('iscorrect', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Closed_Set_Train',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='Open_Set_Train',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('answer', models.TextField()),
                ('type_train', models.PositiveSmallIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Speaker',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('difficulty', models.PositiveSmallIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Speech',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('speech_file', models.FileField(upload_to='cochlear/speech')),
                ('difficulty', models.PositiveSmallIntegerField(default=0)),
                ('uploaded_date', models.DateTimeField(auto_now_add=True)),
                ('speaker', models.ForeignKey(to='cochlear.Speaker', null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL)),
            ],
        ),
        migrations.CreateModel(
            name='User_Attrib',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('username', models.CharField(max_length=50)),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254)),
                ('status', models.PositiveSmallIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='User_Session',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('date_completed', models.DateTimeField(verbose_name='date_completed')),
                ('user', models.ForeignKey(to='cochlear.User_Attrib')),
            ],
        ),
        migrations.AddField(
            model_name='open_set_train',
            name='test_sound',
            field=models.ForeignKey(to='cochlear.Speech'),
        ),
        migrations.AddField(
            model_name='closed_set_train',
            name='choices',
            field=models.ManyToManyField(related_name='Closed_Set_Trains', through='cochlear.Closed_Set_Question_Answer', to='cochlear.Speech'),
        ),
        migrations.AddField(
            model_name='closed_set_train',
            name='test_sound',
            field=models.ForeignKey(to='cochlear.Speech'),
        ),
        migrations.AddField(
            model_name='closed_set_question_answer',
            name='answer',
            field=models.ForeignKey(to='cochlear.Speech'),
        ),
        migrations.AddField(
            model_name='closed_set_question_answer',
            name='question',
            field=models.ForeignKey(to='cochlear.Closed_Set_Train'),
        ),
        migrations.AddField(
            model_name='closed_set_data',
            name='closed_set_train',
            field=models.ForeignKey(to='cochlear.Closed_Set_Train'),
        ),
        migrations.AddField(
            model_name='closed_set_data',
            name='user',
            field=models.ForeignKey(to='cochlear.User_Attrib'),
        ),
    ]
