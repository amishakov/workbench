# Generated by Django 3.2.14 on 2022-09-09 18:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("projects", "0021_remove_service_role"),
    ]

    operations = [
        migrations.CreateModel(
            name="InternalType",
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
                (
                    "ordering",
                    models.PositiveIntegerField(default=0, verbose_name="ordering"),
                ),
                ("name", models.CharField(max_length=100, verbose_name="name")),
                ("percentage", models.IntegerField(verbose_name="percentage")),
                (
                    "assigned_users",
                    models.ManyToManyField(
                        to=settings.AUTH_USER_MODEL, verbose_name="assigned users"
                    ),
                ),
            ],
            options={
                "verbose_name": "internal type",
                "verbose_name_plural": "internal types",
                "ordering": ["ordering"],
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="project",
            name="internal_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="projects.internaltype",
                verbose_name="internal type",
            ),
        ),
        migrations.RunSQL(
            "SELECT audit_audit_table('projects_internaltype');",
            "",
        ),
        migrations.RunSQL(
            "SELECT audit_audit_table('projects_internaltype_assigned_users');",
            "",
        ),
    ]
