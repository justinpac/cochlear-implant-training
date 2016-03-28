# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cochlear', '0007_remove_speech_closed_set_trains'),
    ]

    operations = [
        migrations.AddField(
            model_name='closed_set_data',
            name='closed_set_train',
            field=models.ForeignKey(to='cochlear.Closed_Set_Train', default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='closed_set_train',
            name='choices',
            field=models.ManyToManyField(through='cochlear.Closed_Set_Question_Answer', to='cochlear.Speech', related_name='Closed_Set_Trains'),
        ),
    ]
