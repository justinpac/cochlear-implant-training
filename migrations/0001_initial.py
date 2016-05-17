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
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('date_completed', models.DateTimeField(verbose_name='date completed')),
            ],
        ),
        migrations.CreateModel(
            name='Closed_Set_Question_Answer',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('iscorrect', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Closed_Set_Train',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Closed_Set_Train_Order',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveSmallIntegerField()),
                ('closed_set_train', models.ForeignKey(to='cochlear.Closed_Set_Train')),
            ],
        ),
        migrations.CreateModel(
            name='Open_Set_Train',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('answer', models.TextField()),
                ('type_train', models.PositiveSmallIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Open_Set_Train_Order',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveSmallIntegerField()),
                ('open_set_train', models.ForeignKey(to='cochlear.Open_Set_Train')),
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('week', models.PositiveIntegerField()),
                ('day', models.PositiveSmallIntegerField()),
                ('closed_set_trains', models.ManyToManyField(through='cochlear.Closed_Set_Train_Order', to='cochlear.Closed_Set_Train', related_name='Sessions')),
                ('open_set_trains', models.ManyToManyField(through='cochlear.Open_Set_Train_Order', to='cochlear.Open_Set_Train', related_name='Sessions')),
            ],
        ),
        migrations.CreateModel(
            name='Speaker',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('difficulty', models.PositiveSmallIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Speech',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('speech_file', models.FileField(upload_to='cochlear/speech')),
                ('difficulty', models.PositiveSmallIntegerField(default=0)),
                ('uploaded_date', models.DateTimeField(auto_now_add=True)),
                ('speaker', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, to='cochlear.Speaker', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='User_Attrib',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
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
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('date_completed', models.DateTimeField(verbose_name='date_completed')),
                ('session', models.ForeignKey(to='cochlear.Session')),
                ('user', models.ForeignKey(to='cochlear.User_Attrib')),
            ],
        ),
        migrations.AddField(
            model_name='open_set_train_order',
            name='session',
            field=models.ForeignKey(to='cochlear.Session'),
        ),
        migrations.AddField(
            model_name='open_set_train',
            name='test_sound',
            field=models.ForeignKey(to='cochlear.Speech'),
        ),
        migrations.AddField(
            model_name='closed_set_train_order',
            name='session',
            field=models.ForeignKey(to='cochlear.Session'),
        ),
        migrations.AddField(
            model_name='closed_set_train',
            name='choices',
            field=models.ManyToManyField(through='cochlear.Closed_Set_Question_Answer', to='cochlear.Speech', related_name='Closed_Set_Trains'),
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
