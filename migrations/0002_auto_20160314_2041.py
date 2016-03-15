# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cochlear', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Speech',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('speech_file', models.FileField(upload_to='cochlear/speech')),
                ('difficulty', models.PositiveSmallIntegerField(default=0)),
                ('speaker', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, null=True, to='cochlear.Speaker')),
            ],
        ),
        migrations.RemoveField(
            model_name='speach',
            name='speaker',
        ),
        migrations.AlterField(
            model_name='closed_set_question_answer',
            name='answer',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, null=True, to='cochlear.Speech'),
        ),
        migrations.AlterField(
            model_name='closed_set_train',
            name='choices',
            field=models.ManyToManyField(related_name='closed_set_choices', through='cochlear.Closed_Set_Question_Answer', to='cochlear.Speech'),
        ),
        migrations.AlterField(
            model_name='closed_set_train',
            name='test_sound',
            field=models.ForeignKey(to='cochlear.Speech'),
        ),
        migrations.DeleteModel(
            name='Speach',
        ),
    ]
