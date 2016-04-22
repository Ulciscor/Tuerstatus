# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-03-08 06:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tuerstatus', '0007_auto_20160215_1616'),
    ]

    operations = [
        migrations.DeleteModel(
            name='User',
        ),
        migrations.AddField(
            model_name='date',
            name='deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='date',
            name='edit',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='date',
            name='topic_id',
            field=models.IntegerField(default=0),
        ),
    ]
