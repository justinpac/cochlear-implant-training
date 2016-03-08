# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cochlear', '0009_auto_20160307_2047'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='name',
            field=models.CharField(max_length=50, default='unknown'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='closed_set_train',
            name='choices',
            field=models.ManyToManyField(related_name='closed_set_choices', through='cochlear.Closed_Set_Question_Answer', to='cochlear.Speach'),
        ),
        migrations.AlterField(
            model_name='user',
            name='sessions_this_week',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='user',
            name='status',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=50),
        ),
    ]
