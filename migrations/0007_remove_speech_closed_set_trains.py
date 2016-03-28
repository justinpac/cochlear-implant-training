# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cochlear', '0006_auto_20160326_1851'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='speech',
            name='closed_set_trains',
        ),
    ]
