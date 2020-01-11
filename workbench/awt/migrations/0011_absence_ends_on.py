# Generated by Django 3.0.2 on 2020-01-07 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("awt", "0010_absence_reason"),
    ]

    operations = [
        migrations.AddField(
            model_name="absence",
            name="ends_on",
            field=models.DateField(
                blank=True,
                help_text="Only used for the visualization of absences.",
                null=True,
                verbose_name="ends on",
            ),
        ),
    ]