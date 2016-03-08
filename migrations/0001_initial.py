# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('username', models.TextField(max_length=50)),
                ('email', models.EmailField(max_length=254)),
                ('status', models.PositiveSmallIntegerField()),
                ('sessions_this_week', models.PositiveSmallIntegerField()),
            ],
        ),
    ]
