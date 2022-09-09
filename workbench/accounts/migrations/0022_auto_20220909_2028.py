# Generated by Django 3.2.14 on 2022-09-09 18:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0021_auto_20220327_1014"),
    ]

    operations = [
        migrations.CreateModel(
            name="SpecialistField",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="name")),
            ],
            options={
                "verbose_name": "specialist field",
                "verbose_name_plural": "specialist fields",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="user",
            name="specialist_field",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="accounts.specialistfield",
                verbose_name="specialist field",
            ),
        ),
        migrations.RunSQL(
            "SELECT audit_audit_table('accounts_specialistfield');",
            "",
        ),
    ]
