# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cochlear', '0008_auto_20160307_2043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='closed_set_train',
            name='choices',
            field=models.ManyToManyField(related_name='closed_set_choices', to='cochlear.Speach', through='cochlear.Closed_Set_Question_Answer'),
        ),
    ]
