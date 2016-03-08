# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cochlear', '0002_speaker'),
    ]

    operations = [
        migrations.CreateModel(
            name='Speach',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('speach_file', models.FileField(upload_to='var/www/hipercic/static/cochlear/speach/')),
            ],
        ),
    ]
