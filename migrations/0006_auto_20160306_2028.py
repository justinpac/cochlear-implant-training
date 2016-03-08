# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cochlear', '0005_auto_20160306_2015'),
    ]

    operations = [
        migrations.CreateModel(
            name='Closed_Set_Train',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.AlterField(
            model_name='closed_set_question_answer',
            name='answer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='cochlear.Speach', null=True),
        ),
        migrations.AddField(
            model_name='closed_set_train',
            name='choices',
            field=models.ManyToManyField(to='cochlear.Speach', related_name='closed_set_choices', through='cochlear.Closed_Set_Question_answer'),
        ),
        migrations.AddField(
            model_name='closed_set_train',
            name='test_sound',
            field=models.ForeignKey(to='cochlear.Speach'),
        ),
        migrations.AddField(
            model_name='closed_set_question_answer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='cochlear.Closed_Set_Train', null=True),
        ),
    ]
