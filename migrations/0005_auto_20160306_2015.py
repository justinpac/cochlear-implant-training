# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cochlear', '0004_auto_20160306_2014'),
    ]

    operations = [
        migrations.CreateModel(
            name='Closed_Set_Question_answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('iscorrect', models.BooleanField(default=False)),
                ('answer', models.ForeignKey(to='cochlear.Speach')),
            ],
        ),
        migrations.AlterField(
            model_name='speaker',
            name='difficulty',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
