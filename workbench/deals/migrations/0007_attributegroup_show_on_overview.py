# Generated by Django 5.0.6 on 2024-06-06 13:39

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("deals", "0006_deal_contributors"),
    ]

    operations = [
        migrations.AddField(
            model_name="attributegroup",
            name="show_on_overview",
            field=models.BooleanField(default=False, verbose_name="show on overview"),
        ),
    ]
