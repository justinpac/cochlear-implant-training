# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cochlear', '0002_auto_20160314_2041'),
    ]

    operations = [
        migrations.AddField(
            model_name='closed_set_train',
            name='day',
            field=models.PositiveSmallIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='closed_set_train',
            name='week',
            field=models.PositiveSmallIntegerField(default=1),
            preserve_default=False,
        ),
    ]
