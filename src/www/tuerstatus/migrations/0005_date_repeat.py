# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2015-12-16 19:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tuerstatus', '0004_auto_20151216_1802'),
    ]

    operations = [
        migrations.AddField(
            model_name='date',
            name='repeat',
            field=models.IntegerField(default=0),
        ),
    ]
