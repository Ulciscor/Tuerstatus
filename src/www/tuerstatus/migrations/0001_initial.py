# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2015-12-14 22:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Date',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('date', models.DateTimeField()),
                ('type', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=50)),
                ('firstname', models.CharField(max_length=50)),
                ('secondname', models.CharField(max_length=50)),
                ('email', models.CharField(max_length=50)),
                ('type', models.IntegerField()),
            ],
        ),
        migrations.AddField(
            model_name='date',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tuerstatus.User'),
        ),
    ]
