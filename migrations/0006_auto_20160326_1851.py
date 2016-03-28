# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cochlear', '0005_closed_set_train_choices'),
    ]

    operations = [
        migrations.CreateModel(
            name='Closed_Set_Data',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('date_completed', models.DateTimeField(verbose_name='date completed')),
            ],
        ),
        migrations.CreateModel(
            name='User_Session',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('date_completed', models.DateTimeField(verbose_name='date_completed')),
            ],
        ),
        migrations.RemoveField(
            model_name='user_attrib',
            name='sessions_this_week',
        ),
        migrations.AddField(
            model_name='user_session',
            name='user',
            field=models.ForeignKey(to='cochlear.User_Attrib'),
        ),
        migrations.AddField(
            model_name='closed_set_data',
            name='user',
            field=models.ForeignKey(to='cochlear.User_Attrib'),
        ),
    ]
