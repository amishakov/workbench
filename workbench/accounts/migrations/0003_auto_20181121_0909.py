# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-11-21 08:09
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("accounts", "0002_remove_user_date_of_birth")]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={
                "ordering": ("_full_name", "_short_name", "email"),
                "verbose_name": "user",
                "verbose_name_plural": "users",
            },
        )
    ]
