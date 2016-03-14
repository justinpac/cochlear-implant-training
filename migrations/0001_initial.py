# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Closed_Set_Question_Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('iscorrect', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Closed_Set_Train',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Speach',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('speach_file', models.FileField(upload_to='/cochlear/speach')),
                ('difficulty', models.PositiveSmallIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Speaker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('difficulty', models.PositiveSmallIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='User_Attrib',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=50)),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254)),
                ('status', models.PositiveSmallIntegerField(default=0)),
                ('sessions_this_week', models.PositiveSmallIntegerField(default=0)),
            ],
        ),
        migrations.AddField(
            model_name='speach',
            name='speaker',
            field=models.ForeignKey(blank=True, to='cochlear.Speaker', on_delete=django.db.models.deletion.SET_NULL, null=True),
        ),
        migrations.AddField(
            model_name='closed_set_train',
            name='choices',
            field=models.ManyToManyField(related_name='closed_set_choices', to='cochlear.Speach', through='cochlear.Closed_Set_Question_Answer'),
        ),
        migrations.AddField(
            model_name='closed_set_train',
            name='test_sound',
            field=models.ForeignKey(to='cochlear.Speach'),
        ),
        migrations.AddField(
            model_name='closed_set_question_answer',
            name='answer',
            field=models.ForeignKey(blank=True, to='cochlear.Speach', on_delete=django.db.models.deletion.SET_NULL, null=True),
        ),
        migrations.AddField(
            model_name='closed_set_question_answer',
            name='question',
            field=models.ForeignKey(blank=True, to='cochlear.Closed_Set_Train', on_delete=django.db.models.deletion.SET_NULL, null=True),
        ),
    ]
