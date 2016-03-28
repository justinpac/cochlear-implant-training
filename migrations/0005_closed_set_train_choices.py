# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cochlear', '0004_auto_20160318_1908'),
    ]

    operations = [
        migrations.AddField(
            model_name='closed_set_train',
            name='choices',
            field=models.ManyToManyField(related_name='closed_set_choices', through='cochlear.Closed_Set_Question_Answer', to='cochlear.Speech'),
        ),
    ]
