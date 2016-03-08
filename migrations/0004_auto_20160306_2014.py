# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cochlear', '0003_speach'),
    ]

    operations = [
        migrations.AddField(
            model_name='speach',
            name='difficulty',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='speach',
            name='speaker',
            field=models.ForeignKey(to='cochlear.Speaker', null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL),
        ),
    ]
