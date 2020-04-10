# Generated by Django 3.0.5 on 2020-04-09 06:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0012_person_date_of_birth"),
        ("accounts", "0008_auto_20200114_0757"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="person",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="contacts.Person",
                verbose_name="person",
            ),
        ),
    ]