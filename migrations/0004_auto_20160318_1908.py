# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cochlear', '0003_auto_20160314_2106'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='closed_set_train',
            name='choices',
        ),
        migrations.AddField(
            model_name='speech',
            name='closed_set_trains',
            field=models.ManyToManyField(through='cochlear.Closed_Set_Question_Answer', to='cochlear.Closed_Set_Train'),
        ),
    ]
