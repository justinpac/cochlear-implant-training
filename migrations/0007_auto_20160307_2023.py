# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cochlear', '0006_auto_20160306_2028'),
    ]

    operations = [
        migrations.AlterField(
            model_name='speach',
            name='speach_file',
            field=models.FileField(upload_to='/cochlear/speach'),
        ),
    ]
